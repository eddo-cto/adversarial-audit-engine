"""
metrics_g.py — G (real audit quality) for the self-test release gate (1.12).

G is measured against EXTERNAL labels, never asserted. Over a corpus of cases (each already matched by
match.match_case), it aggregates:
  - recall           = TP / (TP+FN)                 — fraction of labelled defects condemned
  - recall_severity  = sev_hit / sev_total          — PRIMARY: recall weighted by defect severity
  - precision        = TP / (TP+FP)
  - f1               = harmonic mean(precision, recall)
  - fp_rate          = condemning findings on NO-DEFECT cases / no-defect cases   (the Type-I direction)
Reported together: a high recall with a high fp_rate is not quality (the toy run taught us escape alone is
gameable). stdlib only. The engine (frontier) produces the findings at release time; this only scores them.
"""
from __future__ import annotations


def aggregate(case_results: list[dict], no_defect_flags: list[bool] | None = None) -> dict:
    """case_results: outputs of match.match_case, one per case, aligned with no_defect_flags (True = a case
    with zero labelled defects, used for the false-positive rate)."""
    n = len(case_results)
    flags = no_defect_flags if no_defect_flags is not None else [r["n_defects"] == 0 for r in case_results]

    tp = sum(r["tp"] for r in case_results)
    fp = sum(r["fp"] for r in case_results)
    fn = sum(r["fn"] for r in case_results)
    sev_total = sum(r["sev_total"] for r in case_results)
    sev_hit = sum(r["sev_hit"] for r in case_results)

    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    recall_sev = sev_hit / sev_total if sev_total else float("nan")
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    f1 = (2 * precision * recall / (precision + recall)
          if precision == precision and recall == recall and (precision + recall) else float("nan"))

    # false-positive rate on the no-defect cases: fraction that produced ANY condemning finding
    nd_idx = [i for i, isnd in enumerate(flags) if isnd]
    nd_wrong = sum(1 for i in nd_idx if case_results[i]["n_condemning"] > 0)
    fp_rate = nd_wrong / len(nd_idx) if nd_idx else float("nan")

    return {"n_cases": n, "tp": tp, "fp": fp, "fn": fn,
            "recall": recall, "recall_severity": recall_sev, "precision": precision, "f1": f1,
            "fp_rate": fp_rate, "n_no_defect": len(nd_idx)}
