"""
schema.py — Data model, verdict state machine, and ledger.

This module is the deterministic core of the engine. It encodes, as code,
the rules that seven adversarial test rounds validated:

  - Defect *class* drives expected recall and human-escalation (rounds 5-7).
  - The verdict is a *state machine*, not a free label (draft 2 / round 5):
      * a pattern-only accusation can never directly condemn the artifact
        (it goes to NEEDS_READING),
      * an accusation cannot reach ARTIFACT_DEFECTIVE without a recorded
        defense attempt (the defense-gate that produced ~0 false positives
        across 4 rounds),
      * conceptual-novel / genuinely contested findings go to NEEDS_EXPERT
        (the load-bearing CONTESO state),
      * NEEDS_READING and NEEDS_EXPERT may not remain open at ledger close.
  - Every ledger must declare at least one limit it cannot cover from the
    inside, or it is flagged suspicious (the independence precondition).

Nothing here calls an LLM. The LLM is the semantic engine; this file is the
scaffold that keeps the engine honest.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# --------------------------------------------------------------------------
# Enumerations
# --------------------------------------------------------------------------

class DefectClass(str, Enum):
    """Classification of a finding. Expected recall differs sharply by class;
    see metrics.EXPECTED_RECALL. The last value is the residual limit that
    no internal tier covers and that must be routed to a human expert."""
    LOOKUP = "lookup"                       # value/version/threshold vs a standard
    NUMERIC = "numeric"                     # a re-computable calculation error
    IDIOSYNCRATIC_LOCAL = "idiosyncratic_local"   # local reasoning/derivation error
    NON_LOCAL_MECHANICAL = "non_local_mechanical" # two sections, incompatible values
    NON_LOCAL_CONCEPTUAL_DOCUMENTED = "non_local_conceptual_documented"
    NON_LOCAL_CONCEPTUAL_NOVEL = "non_local_conceptual_novel"  # residual limit
    EPISTEMIC = "epistemic"                 # validation / inference / construct validity
    ETHICAL = "ethical"                     # harm / autonomy / undisclosed value trade-off
    PHENOMENOLOGICAL = "phenomenological"   # lived-experience / perception failure


class EvidenceBase(str, Enum):
    """How an accusation is grounded. PATTERN alone may flag but never condemn."""
    READING = "reading"
    EXECUTION = "execution"          # simulation / re-computation
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    PATTERN = "pattern"              # regex / string match — flags only


class Verdict(str, Enum):
    """Outcome for the ARTIFACT (not for the accuser)."""
    ARTIFACT_DEFECTIVE = "accusa_vince"        # accusation wins in full
    REDUCED = "accusa_ridimensionata"          # real defect, but trivial to fix (derived from cost_to_fix)
    ARTIFACT_HOLDS = "artefatto_regge"         # defended by a fact
    NEEDS_READING = "da_leggere"               # pattern-flagged, must be read
    NEEDS_EXPERT = "conteso"                    # contested — human expert required
    PENDING = "pending"                        # not yet adjudicated


class TemporalStatus(str, Enum):
    """Temporal/epistemic status of a finding ACROSS turns (longitudinal use).

    A third axis, orthogonal to the taxonomy (WHERE the defect is) and to the
    verdict (this turn's adjudicated truth): it types the status of a claim as
    the audit is re-run against new primary documents over time. The four values
    are mutually exclusive lifecycle points — tested on the OPTT longitudinal
    corpus, no two co-occur at a single turn. `perishable_pivot` is a SEPARATE
    orthogonal flag on Finding, because it genuinely co-occurs with a lifecycle
    state. NEVER read by adjudicate(): purely record-only. Default unset."""
    STABLE = "stable"            # holds this turn, no reason to expect change
    PROVISIONAL = "provisional"  # suspected, not yet realized (carries a likelihood)
    TRANSIENT = "transient"      # true this turn, resolved/superseded at a later one
    CONFLICTED = "conflicted"    # two vectors in disagreement, both kept (Belnap B)


class ActionState(str, Enum):
    OPEN = "open"
    DONE = "done"
    DEFERRED = "deferred"
    DELIBERATELY_DISCARDED = "deliberately_discarded"


class CostToFix(str, Enum):
    TRIVIAL = "trivial"     # < 5 min, no design decision
    LOW = "low"             # < 1 h, local decision
    MEDIUM = "medium"       # < 1 day, touches several parts
    HIGH = "high"           # > 1 day or a structural change


class Posta(str, Enum):
    """Stakes. Qualified by objective criteria, never self-declared (round 4
    Difetto A). HIGH stakes makes external review mandatory (gates.py)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IndependenceLevel(int, Enum):
    """How independent the external review was. Level 1 does NOT count as
    external (separate prompts != separate priors — round 4 F-07)."""
    SAME_INSTANCE_ROLES = 1     # not external
    DIFFERENT_MODEL_SAME_VENDOR = 2
    DIFFERENT_MODEL_DIFFERENT_VENDOR = 3
    HUMAN_DOMAIN_EXPERT = 4     # the only true external eye


# --------------------------------------------------------------------------
# Sub-structures
# --------------------------------------------------------------------------

@dataclass
class Accusation:
    text: str
    base: EvidenceBase
    evidence: str = ""                 # the concrete observation / computation
    sections: list[str] = field(default_factory=list)  # ≥2 for non-local findings


@dataclass
class Defense:
    attempted: bool = False            # the defense-gate flag — must be True to condemn
    present: bool = False              # a real verifiable fact was found
    fact: Optional[str] = None         # must be verifiable, not plausibility


# --------------------------------------------------------------------------
# Finding
# --------------------------------------------------------------------------

@dataclass
class Finding:
    id: str
    element: str
    taxonomy_cell: str
    defect_class: DefectClass
    posta: Posta
    accusation: Accusation
    defense: Defense = field(default_factory=Defense)
    verdict: Verdict = Verdict.PENDING
    cost_to_fix: Optional[CostToFix] = None
    action: str = ""
    action_state: ActionState = ActionState.OPEN
    discard_justification: Optional[str] = None
    declared_limit: Optional[str] = None
    source_role: str = ""
    sources: list[str] = field(default_factory=list)   # cited URLs / clauses
    severity: str = ""                                  # alta/media/bassa (free text)
    source_grade: int = 9   # SourceGrade of the load-bearing datum (1 primary-filed,
                            # 2 institutional, 3 generalist, 9 undeclared) — round 12

    # ---- temporal/epistemic axis (round 19, record-only, longitudinal) ------
    # Orthogonal to taxonomy (WHERE) and to verdict (adjudicated truth THIS turn).
    # NEVER read by adjudicate(): purely additive/record-only. Default unset — like
    # source_grade=9, a one-shot run asserts no temporal judgment; the axis lights
    # up only under longitudinal use or when a role types it explicitly.
    temporal_status: Optional[TemporalStatus] = None
    likelihood: Optional[float] = None        # only on provisional; a DECLARED, NON-CALIBRATED estimate in [0,1]
    likelihood_basis: Optional[str] = None    # required if likelihood is set: what the estimate rests on
    conflict_with: list[str] = field(default_factory=list)  # only on conflicted: claim_key(s) of the opposing vector(s)
    perishable_pivot: bool = False            # orthogonal flag: rests on a time-sensitive datum (longitudinal gap 4.3)
    pivot_valid_until: Optional[str] = None   # optional: date by which the perishable pivot must be re-verified
    claim_key: Optional[str] = None           # stable cross-run identity of the CLAIM; auto-filled on serialize if unset
    superseded_by: Optional[str] = None       # claim_key of the later-turn finding that resolved/replaced this one

    # ---- state machine -------------------------------------------------

    def adjudicate(self) -> Verdict:
        """Apply the verdict state machine. Pure function of the finding's
        own fields. Raises IntegrityError on impossible combinations so bugs
        surface loudly instead of silently mislabeling."""
        a, d = self.accusation, self.defense

        # Rule 1: pattern-only evidence can flag, never condemn.
        if a.base == EvidenceBase.PATTERN:
            self.verdict = Verdict.NEEDS_READING
            return self.verdict

        # Rule 2: genuinely novel conceptual non-locals are not internally
        # decidable — route to the human expert.
        if self.defect_class == DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL:
            self.verdict = Verdict.NEEDS_EXPERT
            return self.verdict

        # Rule 3: a verifiable defending fact means the artifact holds.
        if d.present and d.fact:
            self.verdict = Verdict.ARTIFACT_HOLDS
            return self.verdict

        # Rule 4: to reach ARTIFACT_DEFECTIVE a defense MUST have been
        # attempted (the defense-gate). Without it, we cannot condemn.
        if not d.attempted:
            self.verdict = Verdict.NEEDS_EXPERT  # unresolved: needs a real defense pass
            return self.verdict

        # Rule 5: defense attempted, no decisive fact, solid base → the defect is
        # real. Its verdict *projects the severity axis onto the verdict* (a derived,
        # one-way signal, so it cannot drift from `cost_to_fix`): a defect that is
        # TRIVIAL to fix is "real but minor" (REDUCED); anything costlier is a full
        # condemnation (ARTIFACT_DEFECTIVE). This gives a client a verdict-level
        # priority signal without cross-referencing `cost_to_fix`.
        if a.base in (EvidenceBase.READING, EvidenceBase.EXECUTION,
                      EvidenceBase.DOMAIN_KNOWLEDGE):
            self.verdict = (Verdict.REDUCED if self.cost_to_fix == CostToFix.TRIVIAL
                            else Verdict.ARTIFACT_DEFECTIVE)
            return self.verdict

        # Exhaustive by construction: PATTERN is handled by Rule 1 and the three
        # remaining bases by Rule 5, so this point is unreachable for the current
        # EvidenceBase set. Kept as a defensive route-to-human: if a new base is
        # ever added and reaches here, hand it to the expert rather than silently
        # condemn or hold.
        self.verdict = Verdict.NEEDS_EXPERT
        return self.verdict

    def compute_claim_key(self) -> str:
        """Deterministic cross-run identity of the CLAIM (not the per-run `id`).

        A stable fingerprint of WHERE + WHAT — taxonomy cell, element, and the
        accusation text, whitespace/case-normalized — so a longitudinal tracker
        can recognize the same claim across turns and draw its status line. It
        does NOT depend on the turn, the verdict, or the wording of connective
        prose. stdlib only; pure function of the finding's own fields."""
        import hashlib
        import re
        norm_el = re.sub(r"\s+", " ", (self.element or "").strip().lower())
        norm_acc = re.sub(r"\s+", " ", (self.accusation.text or "").strip().lower())
        basis = f"{self.taxonomy_cell}|{norm_el}|{norm_acc}"
        return "ck_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]

    def validate(self) -> list[str]:
        """Return a list of integrity problems (empty == valid)."""
        problems: list[str] = []
        # temporal axis: soft checks that fire ONLY when the (optional) fields are
        # populated, so they can never break an existing finding that omits them.
        if self.likelihood is not None:
            if not (0.0 <= self.likelihood <= 1.0):
                problems.append(f"{self.id}: likelihood must be in [0,1].")
            if not self.likelihood_basis:
                problems.append(f"{self.id}: likelihood requires a declared basis "
                                f"(it is a non-calibrated estimate, not a measured rate).")
            if self.temporal_status != TemporalStatus.PROVISIONAL:
                problems.append(f"{self.id}: likelihood is only meaningful on a provisional finding.")
        if self.conflict_with and self.temporal_status != TemporalStatus.CONFLICTED:
            problems.append(f"{self.id}: conflict_with requires temporal_status=conflicted.")
        if self.verdict == Verdict.ARTIFACT_DEFECTIVE and not self.defense.attempted:
            problems.append(f"{self.id}: condemned without a defense attempt (defense-gate).")
        if self.verdict == Verdict.ARTIFACT_DEFECTIVE and \
                self.accusation.base == EvidenceBase.PATTERN:
            problems.append(f"{self.id}: pattern-only evidence cannot condemn.")
        if self.verdict != Verdict.ARTIFACT_HOLDS and not self.action:
            problems.append(f"{self.id}: non-holding verdict requires a corrective action.")
        if self.action_state == ActionState.DELIBERATELY_DISCARDED and \
                not self.discard_justification:
            problems.append(f"{self.id}: discarded action requires a justification.")
        is_non_local = self.defect_class in (
            DefectClass.NON_LOCAL_MECHANICAL,
            DefectClass.NON_LOCAL_CONCEPTUAL_DOCUMENTED,
            DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL,
        )
        if is_non_local and len(self.accusation.sections) < 2:
            problems.append(f"{self.id}: non-local finding must cite >=2 sections.")
        return problems

    def to_dict(self) -> dict:
        d = asdict(self)
        # enums -> their values for clean JSON
        for k, v in list(d.items()):
            if isinstance(v, Enum):
                d[k] = v.value
        d["accusation"]["base"] = self.accusation.base.value
        d["defect_class"] = self.defect_class.value
        d["posta"] = self.posta.value
        d["verdict"] = self.verdict.value
        d["action_state"] = self.action_state.value
        if self.cost_to_fix:
            d["cost_to_fix"] = self.cost_to_fix.value
        if self.temporal_status:
            d["temporal_status"] = self.temporal_status.value
        # always carry the stable claim identity so a longitudinal tracker can
        # recognize this claim across turns, even if no role set it explicitly.
        if not d.get("claim_key"):
            d["claim_key"] = self.compute_claim_key()
        return d


class IntegrityError(Exception):
    pass


# --------------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------------

@dataclass
class Ledger:
    artifact_name: str
    findings: list[Finding] = field(default_factory=list)
    covered_cells: list[str] = field(default_factory=list)
    excluded_cells: dict[str, str] = field(default_factory=dict)  # cell -> justification
    independence_level: IndependenceLevel = IndependenceLevel.SAME_INSTANCE_ROLES
    created_at: float = field(default_factory=time.time)
    flags: list[str] = field(default_factory=list)
    completion_state: str = ""   # set by run_core after evaluate_completion; the
                                 # Stop hook reads it to enforce non-closure
    content_digest: str = ""     # SHA-256 over (artifact_name, findings); the
                                 # human attestation is an HMAC of this (round 11)
    run_manifest: dict = field(default_factory=dict)   # execution manifest (round 13):
                                 # which layers RAN / NOT_APPLICABLE / MISSING
    source_grade_coverage: dict = field(default_factory=dict)  # per-grade finding count (round 14)
    belnap_coverage: dict = field(default_factory=dict)  # 4-valued cell state N/T/F/B (round 19, record-only)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def adjudicate_all(self) -> None:
        for f in self.findings:
            f.adjudicate()

    def integrity_report(self) -> list[str]:
        problems: list[str] = []
        for f in self.findings:
            problems.extend(f.validate())
        # The independence precondition: at least one declared limit, ever.
        if not any(f.declared_limit for f in self.findings):
            problems.append("LEDGER: no finding declares an internal limit — suspicious.")
        return problems

    def open_blockers(self) -> list[Finding]:
        """NEEDS_READING / NEEDS_EXPERT findings that may not remain open at close."""
        return [f for f in self.findings
                if f.verdict in (Verdict.NEEDS_READING, Verdict.NEEDS_EXPERT)
                and f.action_state == ActionState.OPEN]

    def to_json(self, indent: int = 2) -> str:
        payload = {
            "artifact_name": self.artifact_name,
            "created_at": self.created_at,
            "independence_level": int(self.independence_level),
            "covered_cells": self.covered_cells,
            "excluded_cells": self.excluded_cells,
            "flags": self.flags,
            "completion_state": self.completion_state,
            "content_digest": self.content_digest,
            "run_manifest": self.run_manifest,
            "source_grade_coverage": self.source_grade_coverage,
            "belnap_coverage": self.belnap_coverage,
            "findings": [f.to_dict() for f in self.findings],
        }
        return json.dumps(payload, indent=indent, ensure_ascii=False)
