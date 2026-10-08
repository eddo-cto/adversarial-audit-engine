"""
release_gate.py — the G regression gate for CI (1.12 product-health instrument).

Given a FROZEN baseline G (recorded from the current release) and a new run's G (computed by metrics_g on the
sealed hold-out), the gate FAILS the build if quality regressed:
  - severity-weighted recall dropped by more than delta_recall, OR
  - the false-positive rate rose by more than delta_fp.
Deterministic; the thresholds are frozen here. The findings themselves come from the engine (frontier) at
release time — this only compares two G records. A negative result is a real signal, not a nuisance.
"""
from __future__ import annotations

DELTA_RECALL = 0.05   # allowed drop in severity-weighted recall vs baseline
DELTA_FP = 0.05       # allowed rise in false-positive rate vs baseline


def evaluate(baseline: dict, new: dict, *, delta_recall: float = DELTA_RECALL,
             delta_fp: float = DELTA_FP) -> dict:
    """Return {passed, reasons, recall_delta, fp_delta}. passed=False means CI should fail."""
    reasons = []
    br, nr = baseline.get("recall_severity"), new.get("recall_severity")
    bf, nf = baseline.get("fp_rate"), new.get("fp_rate")
    recall_delta = (nr - br) if (br is not None and nr is not None) else None
    fp_delta = (nf - bf) if (bf is not None and nf is not None) else None

    if recall_delta is not None and recall_delta < -delta_recall:
        reasons.append(f"severity-recall regressed {br:.3f} -> {nr:.3f} (drop {-recall_delta:.3f} > {delta_recall})")
    if fp_delta is not None and fp_delta > delta_fp:
        reasons.append(f"false-positive rate rose {bf:.3f} -> {nf:.3f} (rise {fp_delta:.3f} > {delta_fp})")

    return {"passed": not reasons, "reasons": reasons,
            "recall_delta": recall_delta, "fp_delta": fp_delta}
