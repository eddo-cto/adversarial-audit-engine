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
# 1a. attack-gate (the DUAL of the defense-gate, record-only)
# --------------------------------------------------------------------------

def enforce_attack_gate(ledger: Ledger) -> list[str]:
    """The mirror of the defense-gate. The defense-gate stops a CONDEMNATION that rests on no
    real defence attempt (over-condemnation, Type-I). This stops a CLEARANCE that rests on no
    real attack: an element declared to HOLD without a recorded attack (attack.attempted + a
    named vector) is a possible rubber-stamp — the silent under-attacking (Type-II) the coverage
    gate cannot see, because a token 'holds' finding already marks the cell 'covered'.

    Record-only: it FLAGS, it never changes a verdict. Downgrading every unattacked clearance would
    turn every audit into BLOCKED_OPEN_ITEMS; instead the flag makes the silence visible to the
    governor and to a human, and gives the attack-surface map the future adversarial harness needs."""
    notes: list[str] = []
    for f in ledger.findings:
        if f.verdict == Verdict.ARTIFACT_HOLDS:
            a = getattr(f, "attack", None)
            if not (a and getattr(a, "attempted", False) and str(getattr(a, "vector", "")).strip()):
                ledger.flags.append(
                    f"ATTACK-GATE: {f.id} ('{f.taxonomy_cell}') cleared without a declared attack "
                    f"vector — possible rubber-stamp, verify the clearance")
                notes.append(f"{f.id}: holds without a declared attack")
    return notes


# --------------------------------------------------------------------------
# 1b. evidence-sufficiency gate
# --------------------------------------------------------------------------

def enforce_evidence_sufficiency_gate(ledger: Ledger) -> list[str]:
    """A finding may not be ASSERTED on a document it does not have. Any finding that
    declares `requires_docs` not present in the run's `evidence_base` is forced out of
    a condemning verdict (ARTIFACT_DEFECTIVE / REDUCED / still-PENDING) into
    NEEDS_EXPERT, and its declared limit names the missing documents.

    This encodes, in code, a lesson from a real L3 client-review: the engine had
    flagged a 'patrimonial anomaly' from a 2024 conferimento and an IVA-regime issue —
    both legitimate QUESTIONS, but neither verifiable nor even supposable from the
    supplied fascicolo (the ante-operation comparative and the VAT returns were absent).
    An artefact that HOLDS is untouched: needing an absent document is a bar to
    CONDEMNING, not to absolution. Deterministic; the model's judgement is not trusted
    to remember the limit."""
    notes: list[str] = []
    base = {str(d).strip().lower() for d in (getattr(ledger, "evidence_base", []) or []) if str(d).strip()}
    condemning = (Verdict.ARTIFACT_DEFECTIVE, Verdict.REDUCED, Verdict.PENDING)
    for f in ledger.findings:
        if f.verdict == Verdict.ARTIFACT_HOLDS:
            continue
        req = [str(d).strip() for d in (getattr(f, "requires_docs", []) or []) if str(d).strip()]
        missing = [d for d in req if d.lower() not in base]
        if not missing:
            continue
        limit = ("EVIDENCE-BASE: richiede documenti non nel fascicolo (" +
                 ", ".join(missing) + ") → il rilievo si può sollevare, non asserire; "
                 "instradato all'esperto")
        if f.verdict in condemning:
            f.verdict = Verdict.NEEDS_EXPERT
        f.declared_limit = ((f.declared_limit + " | ") if f.declared_limit else "") + limit
        notes.append(f"{f.id}: missing evidence {missing} → NEEDS_EXPERT")
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
    state: str          # VALIDATED | CROSS_MODEL_REVIEWED | CROSS_MODEL_CLAIMED
    reason: str         # | INTRA_VENDOR_REVIEWED | EXTERNAL_REVIEW_PENDING | BLOCKED_OPEN_ITEMS


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
                        human_verified: bool = False,
                        human_claimed: bool = False,
                        attested_identity: str | None = None) -> CompletionStatus:
    """Decide the final state. The product NEVER reports VALIDATED on internal
    grounds alone. Round-11 hardening — closure is now enforced, not conventional:

      * HUMAN CLOSURE IS CRYPTOGRAPHIC. `human_verified` is True only when the
        operator supplied a valid HMAC of the ledger digest under a key the model
        cannot reach (computed in run_core via aae.attestation). A merely
        *presented* token that does not verify sets `human_claimed` and is
        recorded as unverified — it does NOT validate. The model authors the
        payload but not the key, so it cannot self-report VALIDATED.
      * INDEPENDENCE IS ATTESTED, NOT CLAIMED. Level 3 (CROSS_MODEL_REVIEWED) is
        credited only from `attested_identity` — the identity the adapter that
        made the call actually reports. A different-vendor identity that comes
        only from the payload (`external_identity`) is CROSS_MODEL_CLAIMED and its
        independence is NOT credited (level 1), because the model authored it.
    """
    # Record the honest independence level from the ATTESTED reviewer UP FRONT, so it
    # survives even when the run is BLOCKED on open items. A real datapoint (an EIA
    # study audited via Claude Code) called a genuine cross-vendor eye whose level was
    # LOST because the blocker branch returned before crediting it — the ledger then
    # read level 1 despite an attested level-3 review. Completion STATE and independence
    # LEVEL are separate facts: the level reflects who actually reviewed, regardless of
    # whether open items still block closure. (Claimed-only reviewers are not credited.)
    _attested_up = _machine_external(attested_identity)
    if _attested_up:
        ledger.independence_level = independence_level_between(internal_identity, _attested_up)

    # blockers first
    blockers = ledger.open_blockers()
    if blockers:
        return CompletionStatus(
            "BLOCKED_OPEN_ITEMS",
            f"{len(blockers)} NEEDS_READING/NEEDS_EXPERT findings still open "
            "(e.g. conceptual-novel routed to human expert).",
        )

    # Human closure — only a cryptographically verified attestation validates.
    if human_verified:
        ledger.independence_level = IndependenceLevel.HUMAN_DOMAIN_EXPERT
        return CompletionStatus(
            "VALIDATED",
            "Human external review cryptographically attested (valid HMAC over the "
            "ledger digest under the operator key). Closure recorded.",
        )
    if human_claimed:
        ledger.flags.append(
            "UNVERIFIED human attestation presented (no valid signature under "
            "AAE_HUMAN_KEY) — NOT honored; closure still requires a human.")

    internal_vendor = internal_identity.split(":", 1)[0]
    attested = _machine_external(attested_identity)
    claimed = _machine_external(external_identity)

    # Attested machine reviewer: independence credited at its true level.
    if attested:
        level = independence_level_between(internal_identity, attested)
        ledger.independence_level = level
        if level >= IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR:
            return CompletionStatus(
                "CROSS_MODEL_REVIEWED",
                f"Reviewed by an ATTESTED different-vendor model '{attested}' "
                f"(vendor ≠ '{internal_vendor}'): independence level 3, reliability "
                "improved — but NOT validated. A human external eye is still required.",
            )
        if level == IndependenceLevel.DIFFERENT_MODEL_SAME_VENDOR:
            return CompletionStatus(
                "INTRA_VENDOR_REVIEWED",
                f"Attested same-vendor different model '{attested}': independence "
                "level 2 (shared priors) — not cross-vendor, not validated.",
            )

    # Only a payload-claimed reviewer: do NOT credit level-3 independence.
    if claimed:
        level = independence_level_between(internal_identity, claimed)
        if level >= IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR:
            ledger.independence_level = IndependenceLevel.SAME_INSTANCE_ROLES
            return CompletionStatus(
                "CROSS_MODEL_CLAIMED",
                f"Reviewer '{claimed}' is CLAIMED by the payload but NOT attested by "
                "the calling adapter: independence NOT credited (level 1). Set "
                "AAE_EXTERNAL_ATTESTED_IDENTITY from the adapter to credit level 3.",
            )
        if level == IndependenceLevel.DIFFERENT_MODEL_SAME_VENDOR:
            ledger.independence_level = level
            return CompletionStatus(
                "INTRA_VENDOR_REVIEWED",
                f"Same-vendor different model '{claimed}': independence level 2 "
                "(shared priors) — not cross-vendor, not validated.",
            )

    ledger.independence_level = IndependenceLevel.SAME_INSTANCE_ROLES
    if max_posta == Posta.HIGH:
        return CompletionStatus(
            "EXTERNAL_REVIEW_PENDING",
            "High stakes: external review by an ATTESTED different identity is "
            "MANDATORY and absent. Internal self-falsification completed; not validated.",
        )
    return CompletionStatus(
        "EXTERNAL_REVIEW_PENDING",
        "No attested external identity recorded. Internal self-falsification "
        "completed; validation requires an external eye (the standing precondition).",
    )
