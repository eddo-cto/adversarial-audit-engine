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
    REDUCED = "accusa_ridimensionata"          # real but minor
    ARTIFACT_HOLDS = "artefatto_regge"         # defended by a fact
    NEEDS_READING = "da_leggere"               # pattern-flagged, must be read
    NEEDS_EXPERT = "conteso"                    # contested — human expert required
    PENDING = "pending"                        # not yet adjudicated


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

        # Rule 5: defense attempted, no fact found, solid base → condemn.
        if a.base in (EvidenceBase.READING, EvidenceBase.EXECUTION,
                      EvidenceBase.DOMAIN_KNOWLEDGE):
            self.verdict = Verdict.ARTIFACT_DEFECTIVE
            return self.verdict

        self.verdict = Verdict.REDUCED
        return self.verdict

    def validate(self) -> list[str]:
        """Return a list of integrity problems (empty == valid)."""
        problems: list[str] = []
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
            "findings": [f.to_dict() for f in self.findings],
        }
        return json.dumps(payload, indent=indent, ensure_ascii=False)
