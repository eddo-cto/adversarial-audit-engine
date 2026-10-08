"""
estimator_brier.py — proper scoring of the estimator defense (experiments/, NOT the core).

The estimator defense (schema `defense.estimates`) records a calibrated `p_holds` per sub-claim. Here, where
LABELS exist (a corpus with ground truth), we score the defender with a STRICTLY PROPER scoring rule. The
point (Gneiting-Raftery 2007; Brown-Cohen/Irving prover-estimator debate 2025): under a proper rule, the
defender's optimal strategy is to report its TRUE probabilities — it cannot gain by inflating confidence.
This is why the estimator defense is an anti-obfuscation / anti-rubber-stamp mechanism.

This lives in experiments/ on purpose: at runtime on client documents there are no labels, so the core only
RECORDS the estimates (record-only, verdict-neutral). stdlib only.
"""
from __future__ import annotations

import math

_EPS = 1e-9


def brier(estimates: list[dict], outcomes: dict[str, bool]) -> float:
    """Mean Brier score over the estimates that have a known outcome. Lower is better (0 = perfect).
    estimates: [{subclaim_id, p_holds, ...}]; outcomes: {subclaim_id: True(holds)/False(fails)}."""
    pairs = [(float(e["p_holds"]), bool(outcomes[e["subclaim_id"]]))
             for e in estimates if e.get("subclaim_id") in outcomes]
    if not pairs:
        return float("nan")
    return sum((p - (1.0 if y else 0.0)) ** 2 for p, y in pairs) / len(pairs)


def log_score(estimates: list[dict], outcomes: dict[str, bool]) -> float:
    """Mean negative log score (secondary metric). Lower is better. p clipped to [EPS, 1-EPS]."""
    pairs = [(min(max(float(e["p_holds"]), _EPS), 1 - _EPS), bool(outcomes[e["subclaim_id"]]))
             for e in estimates if e.get("subclaim_id") in outcomes]
    if not pairs:
        return float("nan")
    return -sum(math.log(p if y else 1 - p) for p, y in pairs) / len(pairs)


def score(estimates: list[dict], outcomes: dict[str, bool]) -> dict:
    return {"brier": brier(estimates, outcomes), "log_score": log_score(estimates, outcomes),
            "n_scored": sum(1 for e in estimates if e.get("subclaim_id") in outcomes)}
