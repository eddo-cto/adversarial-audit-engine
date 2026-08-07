"""
orchestrator.py — The audit loop.

Flow (every step validated across seven hostile rounds):

  1. Oracle builds the domain dossier (mechanisms, not verdicts).
  2. Triage picks dimensions present + which specialists to deploy.
  3. Each active role (core + specialists) attacks, under the defense-gate,
     returning findings as JSON.
  4. Findings are parsed into the typed schema, deduplicated across roles.
  5. The verdict state machine adjudicates each finding.
  6. Gates run: defense-gate, coverage-gate.
  7. Completion is evaluated: NEVER 'validated' on internal grounds alone;
     high stakes require an external identity.
  8. Metrics + ledger JSON are produced.

The orchestrator is the Synthesizer/Arbiter role: it holds state, dedups,
and routes. It is code, not an LLM — by design.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .config import AuditConfig
from .llm import LLMClient
from .oracle import Oracle
from .triage import run_triage, TAXONOMY, TriageResult
from .roles import all_roles, Role
from .dedup import deduplicate
from .gates import (enforce_defense_gate, enforce_coverage_gate,
                    evaluate_completion, CompletionStatus)
from . import metrics as metrics_mod
from .triadic import TriadicLayer, TriadicResult
from .construens import ConstruensLayer, ConstruensResult
from .meta_epistemic import MetaGovernor, MetaAssessment
from .schema import (Finding, Ledger, Accusation, Defense, DefectClass,
                     EvidenceBase, Posta, CostToFix, Verdict, ActionState)


# --------------------------------------------------------------------------
# Parsing role output into the typed schema (robust to missing fields)
# --------------------------------------------------------------------------

def _enum(enum_cls, value, default):
    if value is None:
        return default
    try:
        return enum_cls(str(value).strip().lower())
    except ValueError:
        return default


def parse_finding(raw: dict, *, role_key: str) -> Finding | None:
    if not isinstance(raw, dict) or not raw.get("element"):
        return None
    acc_raw = raw.get("accusation", {}) or {}
    def_raw = raw.get("defense", {}) or {}
    accusation = Accusation(
        text=str(acc_raw.get("text", "")),
        base=_enum(EvidenceBase, acc_raw.get("base"), EvidenceBase.READING),
        evidence=str(acc_raw.get("evidence", "")),
        sections=list(acc_raw.get("sections", []) or []),
    )
    defense = Defense(
        attempted=bool(def_raw.get("attempted", False)),
        present=bool(def_raw.get("present", False)),
        fact=def_raw.get("fact"),
    )
    return Finding(
        id=str(raw.get("id") or f"{role_key}-?"),
        element=str(raw.get("element")),
        taxonomy_cell=str(raw.get("taxonomy_cell", "mechanisms")),
        defect_class=_enum(DefectClass, raw.get("defect_class"),
                           DefectClass.IDIOSYNCRATIC_LOCAL),
        posta=_enum(Posta, raw.get("posta"), Posta.MEDIUM),
        accusation=accusation,
        defense=defense,
        cost_to_fix=_enum(CostToFix, raw.get("cost_to_fix"), CostToFix.MEDIUM),
        action=str(raw.get("action", "")),
        declared_limit=raw.get("declared_limit"),
        source_role=role_key,
        sources=list(raw.get("sources", []) or []),
        severity=str(raw.get("severity", "")),
        source_grade=int(raw.get("source_grade", 9) or 9),
        action_state=_enum(ActionState, raw.get("action_state"), ActionState.OPEN),
        discard_justification=raw.get("discard_justification"),
    )


def run_role(client: LLMClient, role: Role, *, artifact: str, dossier: str,
             taxonomy: list[str], max_tokens: int) -> list[Finding]:
    system, user = role.build_prompt(artifact=artifact, dossier=dossier,
                                     taxonomy=taxonomy)
    try:
        data = client.complete_json(system, user, max_tokens=max_tokens)
    except ValueError:
        return []
    raw_findings = data.get("findings", []) if isinstance(data, dict) else []
    out: list[Finding] = []
    for rf in raw_findings:
        f = parse_finding(rf, role_key=role.key)
        if f:
            out.append(f)
    return out


# --------------------------------------------------------------------------
# Result
# --------------------------------------------------------------------------

@dataclass
class AuditResult:
    ledger: Ledger
    triage: TriageResult
    completion: CompletionStatus
    metrics: "metrics_mod.Metrics"
    corroboration: dict[str, list[str]] = field(default_factory=dict)
    integrity_problems: list[str] = field(default_factory=list)
    triadic: "TriadicResult | None" = None
    construens: "ConstruensResult | None" = None
    meta: "MetaAssessment | None" = None

    def summary(self) -> str:
        lines = [
            f"# Audit of: {self.ledger.artifact_name}",
            f"completion: {self.completion.state} — {self.completion.reason}",
            f"roles active: {', '.join(self.triage.active_roles)}",
            "",
            self.metrics.as_text(),
        ]
        if self.triadic:
            lines += ["", self.triadic.summary()]
        if self.construens:
            lines += ["", self.construens.summary()]
        if self.meta:
            lines += ["", self.meta.summary()]
        if self.ledger.flags:
            lines += ["", "FLAGS:"] + [f"  - {x}" for x in self.ledger.flags]
        if self.integrity_problems:
            lines += ["", "INTEGRITY PROBLEMS:"] + \
                     [f"  - {x}" for x in self.integrity_problems]
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Orchestrator
# --------------------------------------------------------------------------

class Orchestrator:
    def __init__(self, client: LLMClient):
        self.client = client
        self.roles = all_roles()

    def run(self, artifact: str, config: AuditConfig,
            artifact_name: str = "artifact") -> AuditResult:
        # 1. oracle dossier
        oracle = Oracle(self.client, allow_web=config.allow_web)
        dossier = oracle.build_dossier(artifact, domain_hint=config.domain_hint)

        # 2. triage
        triage = run_triage(self.client, artifact)

        # 3. run active roles
        all_findings: list[Finding] = []
        for rkey in triage.active_roles:
            role = self.roles.get(rkey)
            if not role:
                continue
            all_findings.extend(run_role(
                self.client, role, artifact=artifact, dossier=str(dossier),
                taxonomy=list(TAXONOMY), max_tokens=config.max_tokens))

        # 4. dedup
        unique, corroboration = deduplicate(all_findings)

        # 5. build ledger + adjudicate
        ledger = Ledger(artifact_name=artifact_name)
        for f in unique:
            ledger.add(f)
        ledger.excluded_cells = dict(triage.excluded)  # carried for coverage
        ledger.adjudicate_all()

        # 6. gates
        enforce_defense_gate(ledger)
        enforce_coverage_gate(ledger)

        # 7. completion / independence
        completion = evaluate_completion(
            ledger, max_posta=config.max_posta,
            external_identity=config.external_review_identity,
            internal_identity=self.client.identity)

        # 8. metrics + integrity
        m = metrics_mod.compute(ledger)
        problems = ledger.integrity_report()

        # 9. deep layers (adaptive; off by default — the Freno)
        triadic_res = None
        if config.enable_triadic:
            triadic_res = TriadicLayer(self.client).run(artifact, str(dossier))
        construens_res = None
        if config.enable_construens and config.construens_idea:
            construens_res = ConstruensLayer(self.client).run(
                config.construens_idea, str(dossier))

        result = AuditResult(ledger=ledger, triage=triage, completion=completion,
                             metrics=m, corroboration=corroboration,
                             integrity_problems=problems,
                             triadic=triadic_res, construens=construens_res)

        # 10. meta-epistemic governor (5th layer): validate the validator.
        # On by default — it is the brake against apparent coherence. It never
        # certifies; it terminates the recursion at the human.
        if config.enable_meta:
            result.meta = MetaGovernor(self.client).assess(result, use_llm=config.allow_web)
        return result


def write_outputs(result: AuditResult, out_dir: str, stem: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    ledger_path = os.path.join(out_dir, f"{stem}.ledger.json")
    with open(ledger_path, "w", encoding="utf-8") as fh:
        fh.write(result.ledger.to_json())
    paths.append(ledger_path)
    summary_path = os.path.join(out_dir, f"{stem}.summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write(result.summary())
    paths.append(summary_path)
    return paths
