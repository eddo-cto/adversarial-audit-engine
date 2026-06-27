"""
repr_validator.py — representation-change validator for NON-LOCAL anomalies.

Estesia transduction §17 (honest, deterministic shadow): we cannot escape Tarski by
recoding, but transducing a corpus into a representation where NON-LOCAL structure becomes
LOCALLY salient genuinely lowers the detection cost for an external validator. The full
cross-modal version (sonification / color / embedding-2D) needs external models; this is the
stdlib, deterministic core for the most common audit case — a corpus of NUMBERS (areas,
amounts, dates-as-ordinals, rendite) — surfacing what no per-span local check would catch:
robust outliers (MAD), trend/monotonicity breaks, and exact duplicates.

It does NOT decide; it emits a graded anomaly signal (0-100) per element, to feed the
explicit criterion. External + ground-truth-free (it imports only the corpus's own
distribution), so it is a *detection aid*, not a truth oracle. Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NumAnomaly:
    index: int
    value: float
    score: float           # 0-100 graded anomaly
    kinds: list[str] = field(default_factory=list)


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def numeric_anomalies(values: list[float], expect_monotonic: str | None = None) -> list[NumAnomaly]:
    """Flag non-local anomalies in a numeric corpus.
    - robust OUTLIERS via MAD (modified z-score); |z|>=3.5 -> strong.
    - TREND/monotonicity breaks if expect_monotonic in {'increasing','decreasing'} (e.g.,
      a sequence of dated values that should not go backwards).
    - exact DUPLICATES (often a copy-paste error in tabulated data).
    Returns only elements with score>0, graded 0-100."""
    n = len(values)
    out: list[NumAnomaly] = []
    if n == 0:
        return out
    med = _median(values)
    mad = _median([abs(v - med) for v in values]) or 1e-9
    # duplicates
    seen: dict[float, int] = {}
    for v in values:
        seen[v] = seen.get(v, 0) + 1

    for i, v in enumerate(values):
        kinds: list[str] = []
        score = 0.0
        z = 0.6745 * abs(v - med) / mad           # modified z-score
        if z >= 2.0:
            kinds.append(f"outlier(MAD z={z:.1f})")
            score = max(score, min(100.0, (z / 3.5) * 100.0))
        if expect_monotonic and i > 0:
            prev = values[i - 1]
            broke = (expect_monotonic == "increasing" and v < prev) or \
                    (expect_monotonic == "decreasing" and v > prev)
            if broke:
                kinds.append(f"rottura di trend ({expect_monotonic})")
                score = max(score, 70.0)
        if seen.get(v, 0) > 1:
            kinds.append("duplicato esatto")
            score = max(score, 45.0)
        if kinds:
            out.append(NumAnomaly(i, v, round(score, 1), kinds))
    return out


def as_signal(values: list[float], expect_monotonic: str | None = None) -> float:
    """Single graded anomaly signal (0-100) for the corpus = max element anomaly.
    Feeds the explicit criterion alongside the LLM/auditor score."""
    an = numeric_anomalies(values, expect_monotonic)
    return max((a.score for a in an), default=0.0)
