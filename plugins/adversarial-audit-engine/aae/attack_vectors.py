"""
attack_vectors.py — a structured library of attack moves, per defect class.

The attack layer of the hive is the LEAST code-structured part of the engine: the
adjudication (gates, verdict machine, dedup, governor) is deterministic, but the
attack itself is prompt+LLM and, until now, improvised. Two consequences:

  * recall/power depends on the model remembering to try the right move;
  * a cleared element ("holds") carries no record of WHICH attack was tried, so a
    real "attacked -> holds" is indistinguishable from a rubber-stamp "looked, fine".

This module gives the attack a spine. For each `defect_class` it enumerates the
concrete moves an attacker should try; roles receive the menu in their prompt and
must name, on every finding, the `attack.vector` they used. The enumeration is DATA
(like roles.py): adding a move is editing data, not code. It does not adjudicate —
the attack-gate (gates.py) only makes a missing attack visible; verdicts are untouched.
"""
from __future__ import annotations

# defect_class -> ordered list of concrete attack moves (the menu the attacker draws from)
ATTACK_VECTORS: dict[str, list[str]] = {
    "lookup": [
        "value vs the authoritative source (not a snippet/aggregator)",
        "outdated or superseded version of the standard/threshold",
        "wrong unit or scale",
        "definition drift — a term used with a meaning different from the standard",
    ],
    "numeric": [
        "recompute the quantity independently",
        "test boundary / edge values",
        "rounding and precision",
        "unit conversion",
        "sign or direction of the effect",
    ],
    "idiosyncratic_local": [
        "follow the derivation step by step and locate the broken step",
        "surface a hidden assumption a single step relies on",
        "inverted causality",
        "a 'guaranteed' property the chosen mechanism cannot actually provide",
        "double-attack the same judgment as both 'too high' and 'too low'",
    ],
    "non_local_mechanical": [
        "tabulate every premise with its origin section and propagate its consequence",
        "two distant sections carrying incompatible values",
        "reconciliation gap — a sum that does not match a declared total",
        "cross-reference mismatch between sections",
    ],
    "non_local_conceptual_documented": [
        "apply a known mechanism from the dossier across sections",
        "instantiate a documented failure mode of the mechanism",
        "compose independently-valid parts into a combination that breaks",
    ],
    "non_local_conceptual_novel": [
        "a residual interaction not covered by any standard — route to the human expert",
        "a novel cross-section conflict with no documented precedent",
    ],
    "epistemic": [
        "circular or non-independent validation (the check reuses what it validates)",
        "evidence insufficient for the strength of the claim",
        "construct validity — the measure does not measure the construct",
        "correlation presented as causation",
        "undue transfer of a result across populations/contexts",
        "a criterion stated so it can never be falsified",
    ],
    "ethical": [
        "name who is harmed and how, anchored to a real framework",
        "burden shifted onto the weaker party",
        "consent or autonomy violation",
        "a value trade-off disguised as a technical choice",
    ],
    "phenomenological": [
        "an 'objective' measure that ignores first-person experience",
        "false precision that reifies a lived complexity",
        "anchoring on a number",
        "the gap between what is 'delivered' and what is 'understood'",
    ],
}


def vectors_for(defect_class: str) -> list[str]:
    """The attack menu for a defect class (empty list if the class is unknown)."""
    return list(ATTACK_VECTORS.get(str(defect_class), []))


def all_vectors() -> set[str]:
    """Every move in the library, flattened — for validation/audit."""
    return {v for moves in ATTACK_VECTORS.values() for v in moves}


def render_for_prompt() -> str:
    """A compact menu injected into role prompts, so the attack is systematic, not improvised.
    Each finding must name the attack.vector it used (a move below, or a declared novel one)."""
    lines = ["ATTACK VECTORS (try these systematically; on every finding name the "
             "attack.vector you used — one of these, or 'novel: <describe>'):"]
    for cls, moves in ATTACK_VECTORS.items():
        lines.append(f"  {cls}: " + "; ".join(moves))
    return "\n".join(lines)
