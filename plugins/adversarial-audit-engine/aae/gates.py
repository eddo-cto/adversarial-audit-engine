"""
gates.py — The gates that keep the engine honest.

These are pure, deterministic checks the orchestrator runs. They encode the
three properties that survived adversarial testing:

  1. defense-gate     : a finding may not be condemned without a recorded
                        defense attempt (responsible for ~0 false positives).
  2. coverage-gate    : every taxonomy dimension must be addressed or
                        excluded-with-justification, else the ledger is marked
                        COVERAGE INCOMPLETE (round 3 fix for F-04).
  3. independence-gate: the run may not be reported as VALIDATED unless an
                        external review with a DIFFERENT identity exists. Two
                        roles on the same instance do NOT count (round 4 F-07).
                        High stakes makes external review mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import (Ledger, Finding, Verdict, Posta, IndependenceLevel)
from .triage import TAXONOMY


# --------------------------------------------------------------------------
# 1. defense-gate
# --------------------------------------------------------------------------

def enforce_defense_gate(ledger: Ledger) -> list[str]:
    """Downgrade any condemnation lacking a defense attempt. Returns notes."""
    notes: list[str] = []
    for f in ledger.findings:
        if f.verdict == Verdict.ARTIFACT_DEFECTIVE and not f.defense.attempted:
            f.verdict = Verdict.NEEDS_EXPERT
            notes.append(f"{f.id}: condemnation without defense attempt → NEEDS_EXPERT")
    return notes


# --------------------------------------------------------------------------
# 2. coverage-gate
# --------------------------------------------------------------------------

def enforce_coverage_gate(ledger: Ledger) -> list[str]:
    """Every dimension must be covered (a finding touches it) or excluded with
    a justification. Otherwise flag the ledger."""
    notes: list[str] = []
    touched = {f.taxonomy_cell for f in ledger.findings}
    ledger.covered_cells = sorted(touched)
    for dim in TAXONOMY:
        if dim not in touched and dim not in ledger.excluded_cells:
            ledger.flags.append(f"COVERAGE INCOMPLETE: '{dim}' neither covered "
                                f"nor excluded-with-justification")
            notes.append(f"coverage gap: {dim}")
    return notes


# --------------------------------------------------------------------------
# 3. independence-gate
# --------------------------------------------------------------------------

@dataclass
class CompletionStatus:
    state: str          # "VALIDATED" | "EXTERNAL_REVIEW_PENDING" | "BLOCKED_OPEN_ITEMS"
    reason: str


def evaluate_completion(ledger: Ledger, *, max_posta: Posta,
                        external_identity: str | None,
                        internal_identity: str) -> CompletionStatus:
    """Decide the final state. The product NEVER reports VALIDATED on internal
    grounds alone. High stakes require a genuinely external identity."""
    # blockers first
    blockers = ledger.open_blockers()
    if blockers:
        return CompletionStatus(
            "BLOCKED_OPEN_ITEMS",
            f"{len(blockers)} NEEDS_READING/NEEDS_EXPERT findings still open "
            "(e.g. conceptual-novel routed to human expert).",
        )

    has_external = bool(external_identity) and external_identity != internal_identity
    is_human = bool(external_identity) and external_identity.lower().startswith("human")

    # ONLY a human external eye validates. A different-vendor LLM raises the
    # independence level and improves reliability, but it is still a machine
    # sharing the ultimate limit — it cannot reach VALIDATED. (Eight rounds.)
    if is_human:
        ledger.independence_level = IndependenceLevel.HUMAN_DOMAIN_EXPERT
        return CompletionStatus("VALIDATED",
                                f"Human external review by '{external_identity}' recorded.")
    if has_external:
        return CompletionStatus(
            "CROSS_MODEL_REVIEWED",
            f"Reviewed by a different-vendor model '{external_identity}' "
            f"(≠ '{internal_identity}'): independence raised, reliability "
            "improved — but NOT validated. A human external eye is still required.",
        )
    if max_posta == Posta.HIGH:
        return CompletionStatus(
            "EXTERNAL_REVIEW_PENDING",
            "High stakes: external review by a different identity is MANDATORY "
            "and absent. Internal self-falsification completed; not validated.",
        )

    return CompletionStatus(
        "EXTERNAL_REVIEW_PENDING",
        "No external identity recorded. Internal self-falsification completed; "
        "validation requires an external eye (the standing precondition).",
    )
