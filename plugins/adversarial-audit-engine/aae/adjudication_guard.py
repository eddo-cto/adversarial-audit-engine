"""
adjudication_guard.py — bias-resistant adjudication as a NAMED, TESTABLE guarantee.

This is a RULE/PROFILE, not a new layer. It formalises what the engine already
does when it adjudicates blind (the fase-2 and inter-nature runs: relabelled
pairs, cross-domain decoys, a fresh instance that never audited) into explicit
immunities that can be *checked*, not just claimed.

Why now: the 2026 LLM-as-judge literature names a recurring set of judge biases —
**position** bias (the verdict flips when candidates are reordered), **length**
bias (longer/shorter answers preferred), **self-preference** bias (a judge favours
its own output) — and shows multi-agent setups can *amplify* rather than cancel
them. Almost every ensemble/debate tool asserts it "aggregates perspectives";
none certify that the aggregation is immune to these. This module lets a run
certify it.

The four immunities:
  1. self-preference — the adjudicator identity is not among the auditors;
  2. position — the decision is invariant under reordering of the candidates;
  3. length — the YES/NO decision does not correlate with candidate length;
  4. closure — only inter-nature or human adjudication can lift the ceiling
     (delegated to the independence ledger, so the two rules compose).

Pure standard library. No new capability.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Hashable, Sequence

from .independence_ledger import build_independence_ledger


# -------------------------------------------------------------- self-preference
def is_self_adjudicating(adjudicator: str | None,
                         auditors: Sequence[str]) -> bool:
    """True if the adjudicator is one of the identities it is judging."""
    return bool(adjudicator) and adjudicator in set(auditors)


# -------------------------------------------------------------- position
def blind_relabel(items: Sequence[Hashable], *, seed: int) -> tuple[list, dict]:
    """Deterministically shuffle and relabel items so neither order nor original
    identity carries a signal to the adjudicator. Returns (relabelled, key) where
    relabelled is a list of (token, item) in shuffled order and key maps token->item."""
    idx = list(range(len(items)))
    random.Random(seed).shuffle(idx)
    relabelled, key = [], {}
    for n, i in enumerate(idx, 1):
        token = f"C{n:02d}"
        relabelled.append((token, items[i]))
        key[token] = items[i]
    return relabelled, key


def position_invariant(decide: Callable[[list], frozenset],
                       items: Sequence[Hashable],
                       *, seeds: Sequence[int] = (1, 2, 3, 4, 5)) -> bool:
    """True if `decide` returns the SAME set of YES items under every reordering.

    `decide` takes an ordered list of items and returns a frozenset of the items
    it judges YES. If the YES-set changes when the order changes, the judge has
    position bias.
    """
    baseline: frozenset | None = None
    for s in seeds:
        order = list(items)
        random.Random(s).shuffle(order)
        yes = decide(order)
        if baseline is None:
            baseline = yes
        elif yes != baseline:
            return False
    return True


# -------------------------------------------------------------- length
def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def length_bias(lengths: Sequence[float], yes_flags: Sequence[int],
                *, threshold: float = 0.5) -> tuple[float, bool]:
    """Correlate candidate length with the YES decision. Returns (r, flagged).
    A judge whose YES tracks length is length-biased."""
    r = _pearson([float(x) for x in lengths], [float(y) for y in yes_flags])
    return r, abs(r) >= threshold


# -------------------------------------------------------------- report
@dataclass(frozen=True)
class BiasResistanceReport:
    self_preference_blocked: bool
    position_immune: bool | None      # None = not tested
    length_bias_r: float | None       # None = not tested
    length_bias_flagged: bool | None
    independence_scope: str           # from the independence ledger
    independence_ceiling: str
    notes: tuple

    def to_dict(self) -> dict:
        return {
            "self_preference_blocked": self.self_preference_blocked,
            "position_immune": self.position_immune,
            "length_bias_r": self.length_bias_r,
            "length_bias_flagged": self.length_bias_flagged,
            "independence_scope": self.independence_scope,
            "independence_ceiling": self.independence_ceiling,
            "notes": list(self.notes),
        }

    def clean(self) -> bool:
        """True only if every tested immunity holds."""
        if not self.self_preference_blocked:
            return False
        if self.position_immune is False:
            return False
        if self.length_bias_flagged:
            return False
        return True


def assess_adjudication(*, auditors: Sequence[str], adjudicator: str | None,
                        external: str | None = None,
                        decide: Callable[[list], frozenset] | None = None,
                        items: Sequence[Hashable] | None = None,
                        lengths: Sequence[float] | None = None,
                        yes_flags: Sequence[int] | None = None,
                        length_threshold: float = 0.5) -> BiasResistanceReport:
    """Certify the bias-resistance of one adjudication. Composes with the
    independence ledger for closure (self-preference + cross-nature)."""
    notes: list[str] = []

    self_pref = is_self_adjudicating(adjudicator, auditors)
    self_pref_blocked = not self_pref
    if self_pref:
        notes.append("SELF-PREFERENCE: adjudicator is one of the audited "
                     "identities — verdict cannot claim independence.")

    position_immune = None
    if decide is not None and items is not None:
        position_immune = position_invariant(decide, items)
        if position_immune is False:
            notes.append("POSITION BIAS: the YES-set changed under reordering.")

    length_r = length_flagged = None
    if lengths is not None and yes_flags is not None:
        length_r, length_flagged = length_bias(lengths, yes_flags,
                                                threshold=length_threshold)
        if length_flagged:
            notes.append(f"LENGTH BIAS: YES correlates with length (r={length_r:.2f}).")

    led = build_independence_ledger(auditors=list(auditors),
                                    adjudicator=adjudicator, external=external)
    notes.append(f"CLOSURE: {led.scope} → ceiling {led.ceiling}.")

    return BiasResistanceReport(
        self_preference_blocked=self_pref_blocked,
        position_immune=position_immune,
        length_bias_r=length_r,
        length_bias_flagged=length_flagged,
        independence_scope=led.scope,
        independence_ceiling=led.ceiling,
        notes=tuple(notes),
    )
