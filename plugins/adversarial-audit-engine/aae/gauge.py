"""Gauge invariance (1.20.0) — a verdict's TRUTH class must not depend on a SEVERITY declaration.

Born from the «Trasduzione e uscita da Goodhart» programme (section A: measure only the invariants of the group G
of admissible transformations = pass to the quotient S/G; and the local argument: wherever proxy and target are not
aligned, a direction exists that moves the proxy without moving the target). In the engine the proxy is the verdict,
a pure function of fields the auditor declares. Some of those fields describe HOW MUCH a defect matters (`posta`,
`cost_to_fix`); others decide WHETHER it is real, open or defended (defense, sources, documents, grounding). The
first group must be a gauge for the second: re-declaring the stakes or the fix cost of a finding may change its
priority, never whether it condemns, holds or stays open.

A real run showed the violation (CT 2800/2025, finding F-12): a lookup claim resting on a non-primary source, with a
primary reachable, escaped the source-grade gate because `cost_to_fix=trivial` turned it from ARTIFACT_DEFECTIVE into
REDUCED, and the gate only looked at ARTIFACT_DEFECTIVE. The claim was false; an L4 read of the primary overturned
it. That escape is closed in source_grade.py (1.20); this module makes the whole CLASS of escapes visible for every
current and future gate, by running the real core on each finding under every single-lever severity variation.

Record-only: verdicts are never changed here. Deterministic, stdlib-only. The probe calls `discipline()` itself, so
it can never drift from the gate cascade it audits.
"""
from __future__ import annotations

import copy

CONDEMN = {"accusa_vince", "accusa_ridimensionata"}
HOLD = {"artefatto_regge"}

SEVERITY_LEVERS = {
    "cost_to_fix": ["trivial", "low", "medium", "high"],
    "posta": ["low", "medium", "high"],
}


def truth_class(verdict_value: str) -> str:
    """condemn / holds / open — the quotient of the verdict by the severity axis."""
    v = str(verdict_value or "")
    if v in CONDEMN:
        return "condemn"
    if v in HOLD:
        return "holds"
    return "open"


def _single_verdict(payload: dict, raw_finding: dict) -> str | None:
    from .pipeline import discipline   # local import: pipeline imports this module
    mini = {k: v for k, v in payload.items()
            if k not in ("findings", "deep_causal_roots", "root_judgments")}
    mini["findings"] = [raw_finding]
    try:
        led = discipline(mini, _probe=True).ledger
    except Exception:   # a malformed variant is not evidence of a gauge leak
        return None
    if not led.findings:
        return None
    return led.findings[0].verdict.value


def gauge_probe(payload: dict, ledger) -> tuple[list, dict, list]:
    """Return (report, summary, flag notes). `ledger` is the already-disciplined ledger (for the declared verdicts)."""
    declared = {str(f.id): f.verdict.value for f in ledger.findings}
    report: list[dict] = []
    checked = 0
    raws = list(payload.get("findings", []) or [])
    for i, rf in enumerate(raws, start=1):
        if not isinstance(rf, dict):
            continue
        # the ledger may have re-assigned ids (1.18); match by position when the declared id is missing/duplicated
        fid = str(rf.get("id") or "")
        if fid not in declared and i - 1 < len(ledger.findings):
            fid = str(ledger.findings[i - 1].id)
        base_v = _single_verdict(payload, rf)
        if base_v is None or base_v != declared.get(fid, base_v):
            continue   # finding not separable from the rest of the ledger: abstain rather than guess
        checked += 1
        base_c = truth_class(base_v)
        for lever, values in SEVERITY_LEVERS.items():
            current = str(rf.get(lever) or "")
            for val in values:
                if val == current:
                    continue
                var = copy.deepcopy(rf)
                var[lever] = val
                v = _single_verdict(payload, var)
                if v is None:
                    continue
                if truth_class(v) != base_c:
                    report.append({"id": fid, "lever": lever, "declared": current or None, "variant": val,
                                   "class_declared": base_c, "class_variant": truth_class(v),
                                   "verdict_declared": base_v, "verdict_variant": v})
    dependent = sorted({r["id"] for r in report})
    summary = {"checked": checked, "dependent": len(dependent), "levers": sorted(SEVERITY_LEVERS)}
    notes = []
    if dependent:
        items = "; ".join(f"{r['id']} ({r['lever']} {r['declared']}→{r['variant']}: "
                          f"{r['verdict_declared']}→{r['verdict_variant']})" for r in report[:8])
        notes.append(f"GAUGE: {len(dependent)}/{checked} finding la cui CLASSE di verità (condanna / regge / aperto) "
                     f"cambia dichiarando diversamente la sola gravità — {items}. Una dichiarazione di gravità non deve "
                     f"decidere se un rilievo è vero: un gate ne dipende. Record-only.")
    return report, summary, notes
