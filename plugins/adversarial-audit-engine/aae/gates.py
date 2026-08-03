"""
gates.py — The gates that keep the engine honest.

These are pure, deterministic checks the orchestrator runs. They encode the
three properties that survived adversarial testing:

  1. defense-gate     : a finding may not be condemned without a recorded
                        defense attempt (responsible for ~0 false positives).
  2. coverage-gate    : every taxonomy dimension must be addressed or
                        excluded-with-justification, else the ledger is marked
                        COVERAGE INCOMPLETE (round 3 fix for F-04).
  3. independence-gate: VENDOR-AWARE. CROSS_MODEL_REVIEWED needs a genuinely
                        different-vendor reviewer (level 3); a same-vendor model
                        is INTRA_VENDOR_REVIEWED (level 2). VALIDATED needs an
                        OUT-OF-BAND human attestation the model cannot author
                        (round 4 F-07; round 9 F-VENDOR/F-HUMAN). High stakes
                        makes external review mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import (Ledger, Finding, Verdict, Posta, IndependenceLevel)
from .triage import TAXONOMY
from .adapters import independence_level_between


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
    state: str          # VALIDATED | CROSS_MODEL_REVIEWED | INTRA_VENDOR_REVIEWED
    reason: str         # | EXTERNAL_REVIEW_PENDING | BLOCKED_OPEN_ITEMS


def _machine_external(external_identity: str | None) -> str | None:
    """A well-formed 'vendor:model' identity that is NOT a human-scheme string.
    Human closure is out-of-band only (see evaluate_completion), so a string
    beginning with 'human' is not a machine reviewer; and a bare token with no
    vendor (no ':') is not a well-formed external identity."""
    if not external_identity:
        return None
    s = external_identity.strip()
    if s.lower().startswith("human"):
        return None
    if ":" not in s:
        return None
    return s


def evaluate_completion(ledger: Ledger, *, max_posta: Posta,
                        external_identity: str | None,
                        internal_identity: str,
                        human_attestation: str | None = None) -> CompletionStatus:
    """Decide the final state. The product NEVER reports VALIDATED on internal
    grounds alone. Two hard rules, both enforced here in code (not a prompt):

      * VENDOR-AWARE independence. CROSS_MODEL_REVIEWED is emitted only for a
        genuinely different-vendor reviewer (independence level 3). A same-vendor
        different model is INTRA_VENDOR_REVIEWED (level 2): shared priors, not
        cross-vendor, not validated.
      * HUMAN CLOSURE IS OUT OF BAND. VALIDATED requires `human_attestation`,
        which the operator supplies from OUTSIDE the model's reach (an
        environment secret / signed file — see run_core.py). It can NOT come
        from `external_identity`, because the orchestrating model authors that
        payload: a string beginning with 'human' is explicitly not enough. This
        is what makes "the process cannot self-report validated" true in code.
    """
    # blockers first
    blockers = ledger.open_blockers()
    if blockers:
        return CompletionStatus(
            "BLOCKED_OPEN_ITEMS",
            f"{len(blockers)} NEEDS_READING/NEEDS_EXPERT findings still open "
            "(e.g. conceptual-novel routed to human expert).",
        )

    # Human closure — out-of-band only, never from the payload.
    if human_attestation:
        ledger.independence_level = IndependenceLevel.HUMAN_DOMAIN_EXPERT
        return CompletionStatus(
            "VALIDATED",
            "Human external review attested out-of-band "
            f"(operator token '{human_attestation}'). Closure recorded.",
        )

    machine_external = _machine_external(external_identity)
    level = independence_level_between(internal_identity, machine_external)
    ledger.independence_level = level
    internal_vendor = internal_identity.split(":", 1)[0]

    if level >= IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR:
        return CompletionStatus(
            "CROSS_MODEL_REVIEWED",
            f"Reviewed by a different-vendor model '{machine_external}' "
            f"(vendor ≠ '{internal_vendor}'): independence level 3, reliability "
            "improved — but NOT validated. A human external eye is still required.",
        )
    if level == IndependenceLevel.DIFFERENT_MODEL_SAME_VENDOR:
        return CompletionStatus(
            "INTRA_VENDOR_REVIEWED",
            f"Reviewed by a same-vendor different model '{machine_external}': "
            "independence level 2 (shared priors) — NOT cross-vendor and NOT "
            "validated. A different-vendor eye and, ultimately, a human are "
            "still required.",
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
