"""
attack_seed.py — RAW MATERIAL for the Goodhart forger, harvested from real engine use.

Provenance and firewall (protocol §4, §8):
  The protocol says the forger's raw material starts from "attacks collected from real use, then mutates".
  These moves were abstracted from a real multi-document audit (an Italian judicial-sale dossier) into
  GENERIC, domain-neutral attack MOVES. The firewall the invariants require is enforced HERE, by construction:
    - no case identifiers, no figures, no lot/party/document names — only the shape of the move;
    - no gold labels and no verdicts — a move is a way to attack, NOT a claim that some artefact is invalid;
    - so nobody who "knows the labels" is leaking them: there are no labels in this file to leak.
  These are CANDIDATE moves for the forger's repertoire, not experimental items. They never enter the
  engine's own attack_vectors.py (which would change the plugin); they live in benchmarks/ as research seed.

Shape: MOVES[defect_class] -> list of generic attack moves (imperative, artefact-agnostic). The forger
picks/mutates from these under pressure; the mechanical gold (gold_mechanical.py) decides truth independently.
"""
from __future__ import annotations

MOVES: dict[str, list[str]] = {
    "numeric": [
        "recompute a stated ratio/percentage independently and compare it against the series of comparable items",
        "check that a declared threshold (e.g. a fixed percentage of a base) holds exactly for every item, by exact recomputation",
        "verify that a per-unit rate or coefficient is consistent across homogeneous items (differences only from rounding)",
        "recompute a rounding step and check the direction is uniform across items (never silently up where others go down)",
    ],
    "non_local_mechanical": [
        "find a value copied from a similar item that does not actually apply here (identifiers, adjacencies, lineage)",
        "compare a summary document against its source for a threshold that appears in two places with different values",
        "check a stated date/deadline against a term imposed by a superordinate act, flagging an unexplained gap",
        "trace a chain of derivation and check the endpoint still matches the item it is attached to",
    ],
    "non_local_conceptual_documented": [
        "check whether a note or caveat present in the source was dropped from the derived/summary document",
        "check whether a charge or obligation quantified in the source is actually reflected in the estimate/price",
        "test whether a documented limitation on one item propagates to a guarantee stated elsewhere",
    ],
    "lookup": [
        "compare an identifier (e.g. sheet/parcel) between two sections of the same document for a silent mismatch",
        "verify the declared status of a cited procedure (requested vs granted) against where the document relies on it",
    ],
    "epistemic": [
        "identify a status declared as indeterminate (requested, pending) and surface the unresolved dependency it leaves",
        "find an obligation flagged but not quantified (missing amount or date) and show the decision it blocks",
    ],
    "idiosyncratic_local": [
        "compare the unit value of an item carrying a specific risk against items without it, and check the risk is quantified",
    ],
}


def moves_for(defect_class: str) -> list[str]:
    return list(MOVES.get(defect_class, []))


def all_moves() -> list[str]:
    return [m for lst in MOVES.values() for m in lst]
