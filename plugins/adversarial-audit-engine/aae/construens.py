"""
construens.py — Cause-of-absence diagnosis with the inverted defense-gate.

This is the constructive layer, validated across three business-idea tests
(crypto primes, underpriced stocks, leveraged derivatives) and an x402 test.
Its job is NOT to originate a venture — the tests proved negation does not
generate. Its job is honest TRIAGE: when an idea (or a gap) appears absent or
broken, diagnose WHY it is absent and label the cause:

  - KNOWN_STRUCTURAL      : absence explained by a permanent cause (e.g. EMH,
                            a math impossibility, a regulatory ban). Dead there.
  - CONTINGENT_DOCUMENTED  : a real but removable barrier, with evidence.
  - CONTINGENT_CONJECTURAL : maybe removable, not provable -> human expert.

INVERTED defense-gate (mirror of the destruens gate, controls optimism bias):
the optimistic "the absence is removable / it's an opportunity" hypothesis is
admitted ONLY if it survives a maximal attack by the opposite hypothesis ("the
absence is structural and permanent"). Optimism is the danger here, so the
burden is on the optimistic claim.

Every cause carries a confidence. The construens never validates a venture; it
hands back the short, labelled list of gaps worth a human expert's look.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .llm import LLMClient


class AbsenceLabel(str, Enum):
    KNOWN_STRUCTURAL = "known_structural"
    CONTINGENT_DOCUMENTED = "contingent_documented"
    CONTINGENT_CONJECTURAL = "contingent_conjectural"


@dataclass
class AbsenceCause:
    id: str
    area: str
    optimistic_hypothesis: str        # "the absence is removable / opportunity"
    structural_attack: str            # the maximal opposite-hypothesis attack
    label: AbsenceLabel
    confidence: float                 # 0..1
    survives_inverted_gate: bool = False  # optimistic hypothesis survived?

    def evaluate_gate(self) -> bool:
        """The optimistic 'removable' reading survives only if NOT classified
        KNOWN_STRUCTURAL. Conjectural survives but is flagged for the expert."""
        self.survives_inverted_gate = self.label != AbsenceLabel.KNOWN_STRUCTURAL
        return self.survives_inverted_gate


@dataclass
class SurvivingFragment:
    description: str
    constraints: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ConstruensResult:
    causes: list[AbsenceCause] = field(default_factory=list)
    surviving_fragments: list[SurvivingFragment] = field(default_factory=list)
    honest_null: bool = False         # True if nothing exploitable survives

    @property
    def expert_referrals(self) -> list[AbsenceCause]:
        return [c for c in self.causes
                if c.label == AbsenceLabel.CONTINGENT_CONJECTURAL]

    def summary(self) -> str:
        by = {}
        for c in self.causes:
            by[c.label.value] = by.get(c.label.value, 0) + 1
        tag = "HONEST NULL" if self.honest_null else \
            f"{len(self.surviving_fragments)} surviving fragment(s)"
        return f"construens: {tag}; causes " + \
            ", ".join(f"{k}={v}" for k, v in by.items())


_CONSTRUENS_SYS = (
    "You run the CAUSE-OF-ABSENCE diagnosis (constructive triage) with an "
    "INVERTED defense-gate. For the idea/gap described, find why it is absent or "
    "broken. For EACH cause: (1) state the optimistic hypothesis that the "
    "absence is contingent/removable (an opportunity); (2) attack it with "
    "MAXIMAL force using the opposite hypothesis that the absence is STRUCTURAL "
    "and permanent (impossibility, regulation, no-persistent-edge, harm/"
    "liability, dynamic-validation needs); (3) the optimistic reading passes "
    "ONLY if it survives. Label each cause known_structural | "
    "contingent_documented | contingent_conjectural, with a confidence 0..1. "
    "Then list surviving fragments (the defensible reduced form) with their "
    "binding constraints, or declare an honest null if nothing exploitable "
    "survives. Do not manufacture removable-barrier stories: a cause is "
    "contingent only if anchored to evidence. Return JSON {\"causes\":[{id,"
    "area,optimistic_hypothesis,structural_attack,label,confidence}],"
    "\"surviving_fragments\":[{description,constraints,confidence}],"
    "\"honest_null\":bool}."
)


class ConstruensLayer:
    def __init__(self, client: LLMClient):
        self.client = client

    def run(self, idea: str, dossier: str) -> ConstruensResult:
        user = f"DOSSIER (facts):\n{dossier}\n\nIDEA / GAP TO DIAGNOSE:\n{idea}"
        try:
            data = self.client.complete_json(_CONSTRUENS_SYS, user, max_tokens=3072)
        except ValueError:
            data = {}

        result = ConstruensResult(honest_null=bool(data.get("honest_null", False))
                                  if isinstance(data, dict) else True)
        for rc in (data.get("causes", []) if isinstance(data, dict) else []):
            if not isinstance(rc, dict):
                continue
            try:
                label = AbsenceLabel(str(rc.get("label", "contingent_conjectural")).lower())
            except ValueError:
                label = AbsenceLabel.CONTINGENT_CONJECTURAL
            cause = AbsenceCause(
                id=str(rc.get("id") or "C-?"),
                area=str(rc.get("area", "")),
                optimistic_hypothesis=str(rc.get("optimistic_hypothesis", "")),
                structural_attack=str(rc.get("structural_attack", "")),
                label=label,
                confidence=float(rc.get("confidence", 0.5) or 0.5),
            )
            cause.evaluate_gate()
            result.causes.append(cause)
        for sf in (data.get("surviving_fragments", []) if isinstance(data, dict) else []):
            if not isinstance(sf, dict) or not sf.get("description"):
                continue
            result.surviving_fragments.append(SurvivingFragment(
                description=str(sf.get("description")),
                constraints=list(sf.get("constraints", []) or []),
                confidence=float(sf.get("confidence", 0.5) or 0.5),
            ))
        if not result.surviving_fragments:
            result.honest_null = True
        return result
