"""pipeline.py — THE ONE disciplined core.

Both entry points funnel through here: the `/audit` product path (`scripts/run_core.py`, the agent
produces findings) and `Orchestrator.run()` (the code drives the LLM to produce findings). They differ
only in WHO produces the findings; the discipline — adjudication, defense/source-grade/coverage gates,
grounding, self-instrumentation, honest completion (never VALIDATED internally), attested independence,
the meta-governor, and the A+B run-validity manifest — is enforced ONCE, in `discipline()`, from a single
findings payload (the `--schema` contract). No I/O here: `run_core.run` adds the file writes; the
orchestrator attaches its deep-layer results. One contract, one audited place.

The payload shape and the live enum vocabulary are emitted by `run_core.py --schema`.
"""
from __future__ import annotations

import os

from .schema import Ledger, Posta, ActionState
from .orchestrator import parse_finding, AuditResult
from .gates import enforce_defense_gate, enforce_coverage_gate, evaluate_completion
from .source_grade import enforce_source_grade_gate, source_grade_coverage
from .run_manifest import build_manifest, enforce_run_validity
from .grounding import enforce_grounding
from . import metrics as metrics_mod
from .triage import TriageResult
from .meta_epistemic import MetaGovernor
from .attestation import content_digest, verify_human_attestation
from .type1_calibration import latest_calibration, cite as cite_type1
from .layer_policy import deep_causal_warranted


def discipline(payload: dict, *, attested_identity: str | None = None) -> AuditResult:
    """Enforce the whole discipline on a findings payload and return the AuditResult (no I/O).

    `attested_identity`: the identity of an external eye that was ACTUALLY called. Trusted callers
    (the orchestrator, which invoked the adapter) pass it directly; otherwise it is read from the
    operator environment (`AAE_EXTERNAL_ATTESTED_IDENTITY`). It is NEVER taken from the model-authored
    payload — that is the C1 independence invariant."""
    ledger = Ledger(artifact_name=payload.get("artifact_name", "artifact"))
    for rf in payload.get("findings", []):
        f = parse_finding(rf, role_key=rf.get("source_role", "role"))
        if f:
            ledger.add(f)
    ledger.excluded_cells = dict(payload.get("excluded_cells", {}))
    ledger.adjudicate_all()
    enforce_defense_gate(ledger)
    # source-grade gate: a condemnation on a worse-than-primary datum, when a primary is reachable,
    # is downgraded to NEEDS_READING. The operator may declare no primary via source_primary_reachable.
    primary_reachable = bool(payload.get("source_primary_reachable", True))
    ledger.flags.extend(enforce_source_grade_gate(ledger, primary_reachable=primary_reachable))
    enforce_coverage_gate(ledger)
    # structural integrity (non-local needs >=2 sections; a declared limit) surfaced as flags.
    ledger.flags.extend(f"INTEGRITY: {p}" for p in ledger.integrity_report())
    # anti-hallucination: a condemning quote not verbatim in source_text is downgraded.
    src_text = payload.get("source_text", "")
    if src_text:
        enforce_grounding(ledger.findings, src_text)

    internal = payload.get("internal_identity", "anthropic:internal")
    external = payload.get("external_identity")
    try:
        max_posta = Posta(payload.get("max_posta", "high"))
    except ValueError:
        max_posta = Posta.HIGH

    # self-instrumentation: a HIGH-stakes run with NO deliberately-discarded hypotheses has an unknown
    # generated/discarded denominator, so the false-positive rate is asserted, not measured.
    discarded = sum(1 for f in ledger.findings
                    if f.action_state == ActionState.DELIBERATELY_DISCARDED)
    if max_posta == Posta.HIGH and discarded == 0:
        ledger.flags.append(
            "SELF-INSTRUMENTATION: no discarded hypotheses recorded on a high-stakes run — the "
            "generated/discarded denominator is unknown, so the false-positive rate is asserted, not "
            "measured. Record killed hypotheses with action_state=deliberately_discarded.")

    # Type-I citation (G4): cite this auditor's calibrated false-demolition rate from the calibration
    # store (AAE_CALIBRATION), or say honestly it is NOT calibrated. Never 'low' — always the number
    # and its interval, or nothing. Calibration is produced offline by the control battery.
    _cal_store = os.environ.get("AAE_CALIBRATION")
    _cal = latest_calibration(internal, _cal_store) if _cal_store else None
    ledger.flags.append("TYPE-I: " + cite_type1(_cal))

    # closure is ENFORCED, not conventional. Human closure = a valid HMAC over the ledger digest under
    # an operator key the model cannot reach. Independence level 3 is credited only from the
    # adapter-attested identity, never from the model-authored payload.
    digest = content_digest(ledger.artifact_name,
                            [{"element": f.element, "verdict": f.verdict.value}
                             for f in ledger.findings])
    ledger.content_digest = digest
    key = os.environ.get("AAE_HUMAN_KEY")
    token = os.environ.get("AAE_HUMAN_ATTESTATION")
    human_verified = verify_human_attestation(digest, token, key)
    human_claimed = bool(token) and not human_verified
    if attested_identity is None:
        attested_identity = os.environ.get("AAE_EXTERNAL_ATTESTED_IDENTITY") or None

    completion = evaluate_completion(ledger, max_posta=max_posta,
                                     external_identity=external,
                                     internal_identity=internal,
                                     human_verified=human_verified,
                                     human_claimed=human_claimed,
                                     attested_identity=attested_identity)
    ledger.completion_state = completion.state
    ledger.source_grade_coverage = source_grade_coverage(ledger)

    m = metrics_mod.compute(ledger)
    result = AuditResult(ledger=ledger,
                         triage=TriageResult(dimensions_present=[], deploy_roles=[]),
                         completion=completion, metrics=m)
    result.meta = MetaGovernor(None).assess(result, use_llm=False)  # deterministic

    # execution manifest. Scaffolding is MEASURED from real outputs. When the eye was ACTUALLY attested
    # (identity present), external_auditor RAN — recorded deterministically, overriding an
    # under-declaring payload so the record cannot understate the independence.
    execution = dict(payload.get("execution") or {})
    if attested_identity:
        layers = dict(execution.get("layers") or {})
        layers["external_auditor"] = {
            "status": "ran",
            "justification": f"attested independent eye {attested_identity} (credited by the core)"}
        execution["layers"] = layers
    # A1 enforcement: deep-causal is warranted deterministically (HIGH posta + something to cluster). If
    # it was warranted but the payload did not mark it RAN, record the gap — the product path cannot skip
    # a warranted root-cause pass silently. On a small/sparse run it is not warranted, so no flag.
    _dc_ran = str(((execution.get("layers") or {}).get("deep_causal") or {}).get("status", "")).lower() == "ran"
    if deep_causal_warranted(ledger.findings, max_posta) and not _dc_ran:
        ledger.flags.append(
            "DEEP-CAUSAL WARRANTED BUT NOT RUN: high posta with clustering structure (>=5 findings, or "
            ">=2 findings sharing a taxonomy cell, or a conceptual-novel finding) — root-cause clustering "
            "should have run; coverage of non-local roots is unverified.")

    manifest = build_manifest(ledger, execution,
                              triage=payload.get("triage"),
                              governor_ran=result.meta is not None)

    # non-bypassable A+B refusal: records the manifest and forces INVALID_RUN if the rule fails.
    enforce_run_validity(ledger, manifest)
    return result
