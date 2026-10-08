"""
match.py — deterministic finding<->defect matching for the G self-test (product release gate, 1.12).

NO LLM-as-judge (that would reintroduce the circularity the whole protocol fights). A ledger finding
CONDEMNS a labelled defect iff:
  (a) LOCATION: the finding's verbatim evidence quote is found in the case's source_text, and its byte span
      overlaps the defect's span within a fixed tolerance — feasible precisely BECAUSE the grounding-gate
      guarantees the evidence is a verbatim quote present in the source; and
  (b) CLASS: the finding's defect_class is compatible with the defect's class per a FROZEN table.
Only condemning verdicts (accusa_vince / accusa_ridimensionata) count as defect claims; a held finding on a
defect location is a MISS, not a match. stdlib only; core aae/ untouched.
"""
from __future__ import annotations

CONDEMNING = {"accusa_vince", "accusa_ridimensionata"}
TOLERANCE = 40  # bytes: the quote need not align exactly with the labelled span

# FROZEN class-compatibility table (a defect of class K may be condemned by a finding of any class in the set).
CLASS_COMPAT: dict[str, set[str]] = {
    "numeric": {"numeric", "non_local_mechanical"},
    "non_local_mechanical": {"non_local_mechanical", "numeric"},
    "lookup": {"lookup", "epistemic"},
    "date": {"lookup", "numeric"},
    "epistemic": {"epistemic", "lookup"},
    "non_local_conceptual_documented": {"non_local_conceptual_documented", "epistemic"},
    "credential": {"credential", "lookup", "epistemic"},
}


def _verdict(f: dict) -> str:
    v = f.get("verdict")
    return v.value if hasattr(v, "value") else str(v or "")


def locate(quote: str, source_text: str) -> tuple[int, int] | None:
    """Byte span of the first verbatim occurrence of `quote` in `source_text`, or None."""
    if not quote:
        return None
    i = source_text.find(quote)
    return (i, i + len(quote)) if i >= 0 else None


def _overlap(a: tuple[int, int], b: tuple[int, int], tol: int) -> bool:
    (as_, ae), (bs, be) = a, b
    if min(ae, be) - max(as_, bs) > 0:      # real overlap
        return True
    return abs(as_ - bs) <= tol or abs(ae - be) <= tol   # or near-adjacent within tolerance


def _class_ok(defect_class: str, finding_class: str) -> bool:
    return finding_class in CLASS_COMPAT.get(defect_class, {defect_class})


def _finding_span(f: dict, source_text: str) -> tuple[int, int] | None:
    acc = f.get("accusation", {}) or {}
    return locate(str(acc.get("evidence", "") or ""), source_text)


def match_case(findings: list[dict], defects: list[dict], source_text: str,
               tol: int = TOLERANCE) -> dict:
    """Match one case. Returns per-case TP/FP/FN + which defects were recalled and their severities.
    Each defect is credited at most once; each condemning finding is counted once."""
    condemning = [f for f in findings if _verdict(f) in CONDEMNING]
    f_spans = [( _finding_span(f, source_text), str((f.get("defect_class") or "")) ) for f in condemning]

    matched_defect_idx: set[int] = set()
    matched_finding_idx: set[int] = set()
    for di, d in enumerate(defects):
        dspan = (int(d["span"][0]), int(d["span"][1]))
        dclass = str(d.get("defect_class", ""))
        for fi, (fspan, fclass) in enumerate(f_spans):
            if fspan is None:
                continue
            if _overlap(fspan, dspan, tol) and _class_ok(dclass, fclass):
                matched_defect_idx.add(di)
                matched_finding_idx.add(fi)

    tp = len(matched_defect_idx)
    fn = len(defects) - tp
    fp = len(condemning) - len(matched_finding_idx)       # condemning findings matching no defect
    sev_total = sum(float(d.get("severity", 1)) for d in defects)
    sev_hit = sum(float(defects[i].get("severity", 1)) for i in matched_defect_idx)
    return {"tp": tp, "fp": fp, "fn": fn,
            "n_defects": len(defects), "n_condemning": len(condemning),
            "sev_total": sev_total, "sev_hit": sev_hit,
            "matched_defects": sorted(matched_defect_idx)}
