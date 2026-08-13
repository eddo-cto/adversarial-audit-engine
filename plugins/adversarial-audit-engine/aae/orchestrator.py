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


def _deep_layers_warranted(config, ledger) -> bool:
    """G2 policy — deterministic, testable. The deep passes (triadic / construens /
    deep-causal) are warranted, without an explicit flag, when the run carries depth:
      * HIGH posta — the operator's declared stakes, or
      * a conceptual-novel finding — precisely what root-clustering exists to cluster.
    Anything below that (a low/medium run with no conceptual-novel signal) leaves them
    off: the Freno against over-engineering a small artifact."""
    if config.max_posta == Posta.HIGH:
        return True
    return any(f.defect_class == DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL
               for f in ledger.findings)


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

def _run_external_eye(eye, artifact: str, ledger) -> str:
    """G3 — the independent-eye pass. Ask a DIFFERENT-vendor model to attack the run's
    strongest condemnations. The point is not that a (usually weaker) eye finds more; it
    is that the call is REAL, so the independence is *attested by the adapter that made
    it*, not merely claimed in a payload. Returns the eye's note. Raises if unreachable —
    the caller degrades gracefully to level 1 rather than pretend a review happened."""
    top = [f for f in ledger.findings
           if getattr(f.verdict, "value", "") in ("accusa_vince", "accusa_ridimensionata",
                                                   "conteso")][:8]
    lines = [f"- {f.id} [{f.taxonomy_cell}]: {f.element}" for f in top] or ["- (no condemnations)"]
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

        # 5. build ledger + adjudicate
        ledger = Ledger(artifact_name=artifact_name)
        for f in unique:
            ledger.add(f)
        ledger.excluded_cells = dict(triage.excluded)  # carried for coverage
        ledger.adjudicate_all()

        # 6. gates. The source-grade gate runs FIRST and IN THE ENGINE (G1): a
        # conviction resting on a worse-than-primary datum, while a primary is
        # reachable, is downgraded to NEEDS_READING before completion and the
        # manifest see it — so "read the primary first" is enforced on every entry
        # point, not hand-wired after the run. Its coverage is always reported.
        enforce_source_grade_gate(ledger, primary_reachable=config.primary_reachable)
        ledger.source_grade_coverage = source_grade_coverage(ledger)
        enforce_defense_gate(ledger)
        enforce_coverage_gate(ledger)

        # 6b. independent eye (G3). If an eye is configured (env AAE_EYE=… or injected) it is
        # CALLED here — a real, different-vendor pass over the strongest condemnations — and its
        # adapter identity becomes the ATTESTED reviewer. Vendor-agnostic: a local Ollama eye earns
        # the same level-3 credit as a hosted one. If it is unreachable, we degrade gracefully to
        # level 1 (a flag, no pretense) — the build never HARD-requires an external service.
        attested_identity = None
        eye = self._resolve_eye()
        if eye is not None:
            try:
                note = _run_external_eye(eye, artifact, ledger)
                attested_identity = getattr(eye, "identity", None)
                ledger.flags.append(
                    f"External eye '{attested_identity}' reviewed (attested by adapter). "
                    f"Note: {str(note)[:280]}")
            except Exception as e:  # unreachable local server, network, etc.
                ledger.flags.append(
                    f"External eye '{getattr(eye, 'identity', '?')}' configured but the call "
                    f"failed ({type(e).__name__}); independence NOT credited — run stays level 1.")

        # 7. completion / independence
        completion = evaluate_completion(
            ledger, max_posta=config.max_posta,
            external_identity=config.external_review_identity,
            internal_identity=self.client.identity,
            attested_identity=attested_identity)

        # 8. metrics + integrity
        m = metrics_mod.compute(ledger)
        problems = ledger.integrity_report()

        # 9. deep layers. AUTO-DEPLOYED by stakes (G2): the operator no longer has to
        # remember to switch them on. They fire when the run WARRANTS depth — HIGH posta
        # (the operator's declared stakes) or a conceptual-novel finding (exactly what
        # root-clustering is for) — or when an explicit flag forces them. The Freno holds:
        # on a low/medium run with no conceptual-novel signal they stay off.
        warranted = config.auto_deep_layers and _deep_layers_warranted(config, ledger)
        triadic_res = None
        if config.enable_triadic or warranted:
            triadic_res = TriadicLayer(self.client).run(artifact, str(dossier))
        construens_res = None
        if (config.enable_construens or warranted) and config.construens_idea:
            construens_res = ConstruensLayer(self.client).run(
                config.construens_idea, str(dossier))
        deep_causal_res = None
        if config.enable_deep_causal or warranted:
            deep_causal_res = DeepCausalLayer(self.client).run(
                artifact, [f"{f.id}: {f.element}" for f in ledger.findings])

        result = AuditResult(ledger=ledger, triage=triage, completion=completion,
                             metrics=m, corroboration=corroboration,
                             integrity_problems=problems,
                             triadic=triadic_res, construens=construens_res,
                             deep_causal=deep_causal_res)

        # 10. meta-epistemic governor (5th layer): validate the validator.
        # On by default — it is the brake against apparent coherence. It never
        # certifies; it terminates the recursion at the human.
        if config.enable_meta:
            result.meta = MetaGovernor(self.client).assess(result, use_llm=config.allow_web)

        # 11. A+B run-validity, applied HERE too — not only in the CLI. Build the
        # execution manifest from the triage decision record and the governor run,
        # then apply the non-bypassable refusal: an under-run cannot be closed no
        # matter which entry point produced it.
        ledger.completion_state = completion.state
        # deep_causal is a manifest-tracked optional layer: when it auto-deployed it
        # must show RAN (measured), not NOT_APPLICABLE. Declared status wins in the
        # manifest, so this is the honest record of what the engine actually did.
        execution_layers = {}
        if deep_causal_res is not None:
            execution_layers["deep_causal"] = {
                "status": "ran",
                "justification": "auto-deployed (G2): high posta or conceptual-novel finding"}
        if attested_identity is not None:
            execution_layers["external_auditor"] = {
                "status": "ran",
                "justification": f"attested independent eye {attested_identity} (G3)"}
        execution = {"layers": execution_layers} if execution_layers else None
        manifest = build_manifest(
            ledger, execution,
            triage={"dimensions_present": triage.dimensions_present,
                    "deploy_roles": triage.deploy_roles},
            governor_ran=result.meta is not None)
        enforce_run_validity(ledger, manifest)
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
