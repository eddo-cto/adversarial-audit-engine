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
from .run_manifest import build_manifest, enforce_run_validity
from .source_grade import enforce_source_grade_gate, source_grade_coverage
from .adapters import external_eye_from_env
from . import metrics as metrics_mod
from .triadic import TriadicLayer, TriadicResult
from .construens import ConstruensLayer, ConstruensResult
from .deep_causal import DeepCausalLayer, DeepCausalResult
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


def _deep_layers_warranted(config, findings) -> bool:
    """G2 policy — deterministic, testable. The deep passes (triadic / construens /
    deep-causal) are warranted, without an explicit flag, when the run carries depth:
      * HIGH posta — the operator's declared stakes, or
      * a conceptual-novel finding — precisely what root-clustering exists to cluster.
    Anything below that (a low/medium run with no conceptual-novel signal) leaves them
    off: the Freno against over-engineering a small artifact. `findings` is a list."""
    if config.max_posta == Posta.HIGH:
        return True
    return any(f.defect_class == DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL for f in findings)


def _finding_to_payload(f: Finding) -> dict:
    """Serialize a live Finding back to the `--schema` payload shape, so the orchestrator
    hands the ONE contract to `pipeline.discipline` just like the /audit product path does."""
    return {
        "id": f.id,
        "source_role": f.source_role,
        "element": f.element,
        "taxonomy_cell": f.taxonomy_cell,
        "defect_class": f.defect_class.value,
        "posta": f.posta.value,
        "accusation": {"text": f.accusation.text, "base": f.accusation.base.value,
                       "evidence": f.accusation.evidence, "sections": list(f.accusation.sections)},
        "defense": {"attempted": f.defense.attempted, "present": f.defense.present,
                    "fact": f.defense.fact},
        "cost_to_fix": f.cost_to_fix.value if f.cost_to_fix else None,
        "action": f.action,
        "declared_limit": f.declared_limit,
        "sources": list(f.sources),
        "severity": f.severity,
        "source_grade": f.source_grade,
        "action_state": f.action_state.value,
        "discard_justification": f.discard_justification,
    }


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
    deep_causal: "DeepCausalResult | None" = None
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
        if self.deep_causal:
            lines += ["", self.deep_causal.summary()]
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

def _run_external_eye(eye, artifact: str, findings) -> str:
    """G3 — the independent-eye pass. Ask a DIFFERENT-vendor model to attack the run's
    strongest findings. It runs BEFORE the core assigns verdicts, so it selects by posta
    (not verdict). The point is not that a (usually weaker) eye finds more; it is that the
    call is REAL, so the independence is *attested by the adapter that made it*, not merely
    claimed. Returns the eye's note. Raises if unreachable — the caller degrades to level 1."""
    _order = {"high": 0, "medium": 1, "low": 2}
    top = sorted(findings, key=lambda f: _order.get(getattr(f.posta, "value", ""), 3))[:8]
    lines = [f"- {f.id} [{f.taxonomy_cell}]: {f.element}" for f in top] or ["- (no findings)"]
    system = ("You are an INDEPENDENT external auditor from a different model vendor. Try to "
              "REFUTE the following condemnations of an artifact — attempt the strongest defense "
              "for the artifact. Report, briefly, which you would UPHOLD, which you DISPUTE, and "
              "anything only a human can close. Do not rubber-stamp.")
    user = "Artifact under audit (excerpt):\n" + artifact[:4000] + "\n\nCondemnations:\n" + "\n".join(lines)
    return eye.complete(system, user, max_tokens=1024)


class Orchestrator:
    def __init__(self, client: LLMClient, external_eye="auto"):
        """`external_eye`:
             "auto"  -> resolve an independent eye from the environment (AAE_EYE=…);
                        None if not configured — the run stays honestly level 1.
             None    -> explicitly no eye (hermetic; used by tests).
             client  -> an injected LLMClient-like eye (its `.identity` is what gets attested).
        The eye is vendor-agnostic: a LOCAL Ollama eye earns the same level-3 credit as a
        hosted one, so a confidential run keeps full independence without leaving the host."""
        self.client = client
        self.external_eye = external_eye
        self.roles = all_roles()

    def _resolve_eye(self):
        if self.external_eye == "auto":
            return external_eye_from_env()
        return self.external_eye

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

        # 5. deep layers — the producer's semantic depth, AUTO-DEPLOYED by stakes (G2): HIGH posta or a
        # conceptual-novel finding warrants them; the Freno leaves them off on a small low/medium run.
        # Their rich outputs ride on the result for presentation (exploration, not disciplined findings).
        warranted = config.auto_deep_layers and _deep_layers_warranted(config, unique)
        triadic_res = None
        if config.enable_triadic or warranted:
            triadic_res = TriadicLayer(self.client).run(artifact, str(dossier))
        construens_res = None
        if (config.enable_construens or warranted) and config.construens_idea:
            construens_res = ConstruensLayer(self.client).run(config.construens_idea, str(dossier))
        deep_causal_res = None
        if config.enable_deep_causal or warranted:
            deep_causal_res = DeepCausalLayer(self.client).run(
                artifact, [f"{f.id}: {f.element}" for f in unique])

        # 6. independent eye — CALLED before the core, on the strongest findings; its adapter identity
        # becomes the ATTESTED reviewer handed to the discipline. Vendor-agnostic; a local Ollama eye
        # earns level 3. Unreachable -> graceful level 1 (a flag, no pretense).
        attested_identity = None
        eye_note = None
        eye_failed = None
        eye = self._resolve_eye()
        if eye is not None:
            try:
                eye_note = _run_external_eye(eye, artifact, unique)
                attested_identity = getattr(eye, "identity", None)
            except Exception as e:  # unreachable local server, network, etc.
                eye_failed = (f"External eye '{getattr(eye, 'identity', '?')}' configured but the call "
                              f"failed ({type(e).__name__}); independence NOT credited — run stays level 1.")

        # 7. THE ONE contract + THE ONE discipline. Serialize the findings to the --schema payload and
        # delegate every gate / verdict / completion / governor / manifest to `pipeline.discipline` —
        # the same audited core the /audit product path runs. No discipline is enforced here anymore;
        # this method is now purely the findings PRODUCER (who drives the model), the core is one place.
        from .pipeline import discipline
        execution_layers = {}
        if deep_causal_res is not None:
            execution_layers["deep_causal"] = {
                "status": "ran",
                "justification": "auto-deployed by stakes (high posta / conceptual-novel)"}
        payload = {
            "artifact_name": artifact_name,
            "internal_identity": self.client.identity,
            "external_identity": config.external_review_identity,
            "max_posta": config.max_posta.value,
            "source_primary_reachable": config.primary_reachable,
            "source_text": artifact,                       # arms the grounding gate on this path too
            "excluded_cells": dict(triage.excluded),
            "triage": {"dimensions_present": triage.dimensions_present,
                       "deploy_roles": triage.deploy_roles},
            "execution": {"layers": execution_layers} if execution_layers else None,
            "findings": [_finding_to_payload(f) for f in unique],
        }
        result = discipline(payload, attested_identity=attested_identity)

        # 8. attach the producer's artefacts (outside the disciplined ledger) for presentation.
        result.triage = triage
        result.corroboration = corroboration
        result.triadic = triadic_res
        result.construens = construens_res
        result.deep_causal = deep_causal_res
        if attested_identity:
            result.ledger.flags.append(
                f"External eye '{attested_identity}' reviewed (attested by adapter). "
                f"Note: {str(eye_note)[:280]}")
        elif eye_failed:
            result.ledger.flags.append(eye_failed)
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
