"""
source_grade.py — the source-grade gate (round 12, from the finance runs' §7.1).

A live different-vendor-style run surfaced the oracle's dominant failure mode: an
oracle indifferent to the GRADE of its sources is not a false-positive *shield*,
it is an *amplifier* — it lends a third party's error the authority of a
"documented fact". Two grave false accusations in the finance runs were avoided
only because the oracle happened to climb to the filed primary PDFs.

This makes the rule the run proposed enforceable IN CODE, not in a prompt: a
conviction (ARTIFACT_DEFECTIVE) that rests on a numeric datum of grade worse than
primary — when a primary document on the same datum is reachable — cannot stand;
it is downgraded to NEEDS_READING (read the primary first). Data-driven: the grade
lives on the finding (`source_grade`), read from the payload, not from a side table.
"""
from __future__ import annotations

from enum import IntEnum

from .schema import Ledger, Verdict


class SourceGrade(IntEnum):
    """Grade of the source the accusation's load-bearing datum rests on."""
    PRIMARY_FILED = 1     # issuer's filed/published primary document, retrieved in full
    INSTITUTIONAL = 2     # news agency / broker / regulator index (secondary, reputable)
    GENERALIST = 3        # generalist press / aggregator
    UNKNOWN = 9           # not declared → treated as worse-than-primary


def enforce_source_grade_gate(ledger: Ledger, *,
                              primary_reachable: bool = True) -> list[str]:
    """Downgrade any condemnation resting on a non-primary datum when a primary is
    reachable. Returns notes. `primary_reachable=False` means the operator has
    declared that no primary document exists for this artifact class (e.g. a not-
    yet-filed 10-K), in which case the gate abstains rather than punish."""
    notes: list[str] = []
    if not primary_reachable:
        return notes
    for f in ledger.findings:
        if f.verdict != Verdict.ARTIFACT_DEFECTIVE:
            continue
        grade = int(getattr(f, "source_grade", SourceGrade.UNKNOWN) or SourceGrade.UNKNOWN)
        if grade > int(SourceGrade.PRIMARY_FILED):
            f.verdict = Verdict.NEEDS_READING
            notes.append(
                f"{f.id}: condemnation rests on source grade {grade} "
                f"(> primary) while a primary document is reachable — downgraded "
                f"to NEEDS_READING (source-grade gate). Read the primary first.")
    return notes


def source_grade_coverage(ledger: Ledger) -> dict:
    """Per-grade count of the findings' load-bearing sources — the coverage a run
    must report so 'the dossier is asymmetric' becomes a measured fact, not a
    late-noticed one. grade 0 groups undeclared."""
    out = {1: 0, 2: 0, 3: 0, 0: 0}
    for f in ledger.findings:
        g = int(getattr(f, "source_grade", SourceGrade.UNKNOWN) or SourceGrade.UNKNOWN)
        out[g if g in (1, 2, 3) else 0] += 1
    return out
