"""
auditor_engine.py — the BRIDGE from the ablation toggles to the real engine (the harness Auditor).

This is the ONE goodhart module that depends on `aae` (by nature: it runs the engine). It keeps the
pure modules (analysis/harness/gold) engine-free. The LLM part — turning a forged artefact into a
findings payload by running the attacking roles — is INJECTED as `role_runner(artifact, cell) -> payload`,
so the bridge's own logic (apply ablation, run the deterministic core, derive CLEARED) is testable with a
mock role_runner, deterministically, without any model call.

Toggle -> engine mapping:
  eye      : ON  -> discipline(..., attested_identity=<different vendor>) (independence 3; the eye can
                    CATCH what the internal hive missed, changing CLEARED->caught)
             OFF -> no attestation (independence 1)
  axes     : ON  -> keep every role's findings ; OFF -> keep only ONE role's findings (single-axis)
  governor : recorded but does NOT change verdicts in the engine (record-only). Honest consequence: the
             governor toggle is expected to be ~null on the escape metric — the harness will SHOW that,
             which is itself a result (the eye and the axes mitigate escape; the governor only surfaces).

CLEARED := the engine did NOT condemn the artefact, i.e. no finding has a condemning verdict
(accusa_vince / accusa_ridimensionata). caught := not cleared. Nothing here adjudicates — discipline does.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..")))   # -> plugin root, for `aae`

from aae.pipeline import discipline   # noqa: E402

_CONDEMNING = {"accusa_vince", "accusa_ridimensionata"}

# a stand-in different-vendor eye identity for the ablation (the real run attests the eye actually called)
DIFFERENT_VENDOR_EYE = "google:gemini-cross-vendor"
SAME_VENDOR_SEED_EYE = "anthropic:claude-same-vendor"   # H2 placebo (cross-seed, same vendor)


def apply_ablation(payload: dict, cell) -> tuple[dict, str | None]:
    """Return (payload_after_ablation, attested_identity_for_eye). Pure dict surgery; no engine call."""
    p = dict(payload)
    if not getattr(cell, "axes", True):
        fs = list(p.get("findings", []))
        if fs:
            keep = fs[0].get("source_role")
            p["findings"] = [f for f in fs if f.get("source_role") == keep]   # single-axis
    if getattr(cell, "eye", True):
        attested = SAME_VENDOR_SEED_EYE if getattr(cell, "eye_mode", "cross_vendor") == "cross_seed" \
            else DIFFERENT_VENDOR_EYE
    else:
        attested = None
    return p, attested


class EngineAuditor:
    """Runs the real engine under an ablation cell and returns CLEARED.

    `role_runner(artifact, cell)` supplies the findings payload and is itself axes-aware (runs every role
    when cell.axes, else one). `eye` (optional) is a different-vendor producer `(artifact, cell) -> finding|None`
    (see role_runner.make_eye): when cell.eye it is ACTUALLY called, its finding appended, and its identity
    attested so the core credits level-3 independence. eye=None -> no eye (the toggle is then a no-op, honestly)."""

    def __init__(self, role_runner, eye=None, eye_identity: str = DIFFERENT_VENDOR_EYE):
        self.role_runner = role_runner
        self.eye = eye
        self.eye_identity = eye_identity

    def audit(self, artifact, cell) -> bool:
        payload = self.role_runner(artifact, cell)            # axes handled inside the role_runner
        attested = None
        if getattr(cell, "eye", False) and self.eye is not None:
            ef = self.eye(artifact, cell)                     # a REAL different-vendor re-attack
            if ef:
                payload.setdefault("findings", []).append(ef)
            attested = (SAME_VENDOR_SEED_EYE
                        if getattr(cell, "eye_mode", "cross_vendor") == "cross_seed" else self.eye_identity)
        result = discipline(payload, attested_identity=attested)
        caught = any(
            (f.verdict.value if hasattr(f.verdict, "value") else str(f.verdict)) in _CONDEMNING
            for f in result.ledger.findings)
        return not caught     # CLEARED iff nothing condemned
