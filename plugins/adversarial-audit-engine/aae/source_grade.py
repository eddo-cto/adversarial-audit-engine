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


def belnap_coverage(ledger: Ledger) -> dict:
    """4-valued (Belnap) coverage state per taxonomy cell — round 19, record-only.

    A boolean covered/not-covered view collapses two states the engine already
    produces but discards. This recovers them:
        T (true)  — covered: a finding cites the cell
        F (false) — excluded-with-justification: the cell is in `excluded_cells`
        N (none)  — silent: neither covered nor excluded (an unexamined gap)
        B (both)  — a conflict is present: the cell carries a finding typed
                    `conflicted` (temporal axis), i.e. two vectors kept in
                    disagreement instead of collapsed.
    Precedence B > T > F > N (the most informative state wins). Reads only fields
    the ledger already carries; never feeds a verdict. This is the surviving
    value from the derived-taxonomy exploration (which was killed at F0): making
    the excluded (F) and conflict (B) states visible instead of squashed to 0."""
    from .triage import TAXONOMY
    covered = {f.taxonomy_cell for f in ledger.findings}
    excluded = set(ledger.excluded_cells or {})
    conflicted = set()
    for f in ledger.findings:
        ts = getattr(f, "temporal_status", None)
        ts = getattr(ts, "value", ts)
        if ts == "conflicted" or getattr(f, "conflict_with", None):
            conflicted.add(f.taxonomy_cell)
    per_cell = {}
    for cell in TAXONOMY:
        if cell in conflicted:
            per_cell[cell] = "B"
        elif cell in covered:
            per_cell[cell] = "T"
        elif cell in excluded:
            per_cell[cell] = "F"
        else:
            per_cell[cell] = "N"
    counts = {"N": 0, "T": 0, "F": 0, "B": 0}
    for s in per_cell.values():
        counts[s] += 1
    return {"per_cell": per_cell, "counts": counts}
