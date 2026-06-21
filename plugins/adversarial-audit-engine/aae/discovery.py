"""
discovery.py — Generative opportunity-scan by primitive decomposition.

This is the construct's GENERATIVE complement, validated by the primitive-scan
test. The earlier construens (cause-of-absence) is good at killing bad ideas
and carving toward existing markets — but it does not originate. Negation does
not generate. This module generates by a different route:

  1. Decompose the construct into its cognitive PRIMITIVES.
  2. For each primitive, run an INDEPENDENT, blind scan: where in the world is
     *this exact primitive* demanded as a micro/process-service, across ALL
     domains (not just audit)?
  3. Score every candidate space with a GATED, WEIGHTED rubric whose weights
     are RE-BALANCED on the data (variance-driven), anchoring ranking to a
     method principle rather than impression.
  4. Cross-correlate the independent scans for (a) multi-primitive
     INTERSECTIONS (spaces demanding 2+ primitives — where the combination
     beats single-primitive incumbents) and (b) unexpected structural
     correlations (same primitive in unrelated domains).

Key empirical finding encoded here: the most decisive gate is
`value_without_validation` — spaces where the UNVALIDATED output is the product
(e.g. abductive hypothesis lists in incident RCA, differential diagnosis,
claims subrogation, threat modeling). That class inverts the validation limit
that blocks most ideas, so it tends to win the ranking. The scan still returns
CANDIDATES for a human to validate — it is an amplifier, not an oracle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import pvariance

from .llm import LLMClient


# The construct's primitives (extend as the construct grows).
PRIMITIVES: dict[str, str] = {
    "consequence_propagation": "a choice/premise in one place whose undeclared "
        "consequence breaks a guarantee in a distant place (non-local conflicts "
        "& hidden dependencies across a system/document/rule-set)",
    "cause_of_absence": "why X is absent / undone — structural-permanent vs "
        "contingent-removable — with label and confidence",
    "exhaustive_verification": "check every number/value/threshold/date/citation/"
        "cross-reference, one by one, recomputed against a source (completeness)",
    "abduction": "given an observation/result, generate the best rival "
        "explanations, each anchored to a fact and falsifiable (with the "
        "discriminating test)",
}

# Rubric weights (a-priori). Re-balanced on data by rebalance_weights().
PRIOR_WEIGHTS = {
    "capability_fit": 0.30,
    "under_served": 0.25,
    "wtp": 0.18,
    "defensibility": 0.12,
    "low_liability": 0.10,
    "low_friction": 0.05,
}
_MAX_SHIFT = 0.10  # cap on |calibrated - prior| per weight (anti-overfit)


@dataclass
class CandidateSpace:
    name: str
    domain: str
    primitive: str
    # rubric dimensions, 0..5
    capability_fit: int = 0
    under_served: int = 0
    wtp: int = 0
    defensibility: int = 0
    low_liability: int = 0
    low_friction: int = 0
    # gates (veto)
    gate_legal: bool = True            # no AI ban / no licence wall on the output
    gate_value_without_validation: bool = True  # unvalidated output has value
    # context
    absence_label: str = ""
    unexpected_correlation: str = ""
    sources: list[str] = field(default_factory=list)
    score: float | None = None         # filled by scoring (None = gated out)
    gated_out_reason: str = ""

    def dims(self) -> dict[str, int]:
        return {
            "capability_fit": self.capability_fit,
            "under_served": self.under_served,
            "wtp": self.wtp,
            "defensibility": self.defensibility,
            "low_liability": self.low_liability,
            "low_friction": self.low_friction,
        }

    def apply_score(self, weights: dict[str, float]) -> None:
        if not self.gate_legal:
            self.score, self.gated_out_reason = None, "legal/policy gate failed"
            return
        if not self.gate_value_without_validation:
            self.score, self.gated_out_reason = None, "value-without-validation gate failed"
            return
        self.score = sum(weights[k] * (v / 5.0) for k, v in self.dims().items())


def rebalance_weights(candidates: list[CandidateSpace]) -> dict[str, float]:
    """Anchor weights to the data: a dimension that does not discriminate (low
    variance across candidates) loses weight; one that separates them gains it.
    Shift capped at +/-_MAX_SHIFT from prior, then renormalised to sum 1."""
    scored = [c for c in candidates if c.gate_legal and c.gate_value_without_validation]
    if len(scored) < 2:
        return dict(PRIOR_WEIGHTS)
    variances = {k: pvariance([c.dims()[k] for c in scored]) for k in PRIOR_WEIGHTS}
    vmax = max(variances.values()) or 1.0
    raw = {}
    for k, prior in PRIOR_WEIGHTS.items():
        # discriminating power in [0,1]; map to a shift in [-_MAX_SHIFT, +_MAX_SHIFT]
        disc = variances[k] / vmax
        shift = (disc - 0.5) * 2 * _MAX_SHIFT
        raw[k] = max(0.0, prior + shift)
    total = sum(raw.values()) or 1.0
    return {k: v / total for k, v in raw.items()}


# --------------------------------------------------------------------------
# Scan prompt (carries a distinctive marker for the mock backend)
# --------------------------------------------------------------------------

_SCAN_SYS = (
    "You are an independent MARKET SCOUT for ONE cognitive PRIMITIVE. Find real "
    "micro/process-service spaces where THIS primitive is the core value, across "
    "ALL domains (do not default to audit/peer-review). For each candidate "
    "return rubric fields. Return JSON {\"candidates\":[{name, domain, "
    "capability_fit(0-5), under_served(0-5), wtp(0-5), defensibility(0-5), "
    "low_liability(0-5), low_friction(0-5), gate_legal(bool), "
    "gate_value_without_validation(bool), absence_label, "
    "unexpected_correlation, sources}]}. gate_value_without_validation=true ONLY "
    "if the UNVALIDATED output has standalone value in that space."
)


@dataclass
class DiscoveryResult:
    candidates: list[CandidateSpace] = field(default_factory=list)
    calibrated_weights: dict[str, float] = field(default_factory=dict)
    intersections: dict[str, list[str]] = field(default_factory=dict)  # domain -> primitives
    correlations: list[str] = field(default_factory=list)

    def ranked(self) -> list[CandidateSpace]:
        return sorted([c for c in self.candidates if c.score is not None],
                      key=lambda c: c.score, reverse=True)

    def summary(self) -> str:
        top = self.ranked()[:5]
        lines = ["discovery scan:",
                 "  calibrated weights: " +
                 ", ".join(f"{k}={v:.2f}" for k, v in self.calibrated_weights.items()),
                 f"  candidates: {len(self.candidates)} "
                 f"(gated-out: {sum(1 for c in self.candidates if c.score is None)})",
                 "  multi-primitive intersections: " +
                 (", ".join(f"{d}({len(p)})" for d, p in self.intersections.items())
                  or "none"),
                 "  top spaces:"]
        for c in top:
            lines.append(f"    {c.score:.2f}  {c.name} [{c.domain}] via {c.primitive}")
        return "\n".join(lines)


class DiscoveryLayer:
    def __init__(self, client: LLMClient):
        self.client = client

    def scan(self, primitives: dict[str, str] | None = None) -> DiscoveryResult:
        prims = primitives or PRIMITIVES
        result = DiscoveryResult()
        for key, desc in prims.items():
            user = f"PRIMITIVE: {key} — {desc}"
            try:
                data = self.client.complete_json(_SCAN_SYS, user, max_tokens=3072)
            except ValueError:
                data = {}
            for rc in (data.get("candidates", []) if isinstance(data, dict) else []):
                if not isinstance(rc, dict) or not rc.get("name"):
                    continue
                result.candidates.append(CandidateSpace(
                    name=str(rc.get("name")), domain=str(rc.get("domain", "")),
                    primitive=key,
                    capability_fit=int(rc.get("capability_fit", 0) or 0),
                    under_served=int(rc.get("under_served", 0) or 0),
                    wtp=int(rc.get("wtp", 0) or 0),
                    defensibility=int(rc.get("defensibility", 0) or 0),
                    low_liability=int(rc.get("low_liability", 0) or 0),
                    low_friction=int(rc.get("low_friction", 0) or 0),
                    gate_legal=bool(rc.get("gate_legal", True)),
                    gate_value_without_validation=bool(
                        rc.get("gate_value_without_validation", True)),
                    absence_label=str(rc.get("absence_label", "")),
                    unexpected_correlation=str(rc.get("unexpected_correlation", "")),
                    sources=list(rc.get("sources", []) or []),
                ))

        # weighted scoring with data-fit re-balancing
        result.calibrated_weights = rebalance_weights(result.candidates)
        for c in result.candidates:
            c.apply_score(result.calibrated_weights)

        # cross-correlate: domains demanded by >=2 distinct primitives
        by_domain: dict[str, set[str]] = {}
        for c in result.candidates:
            by_domain.setdefault(c.domain.lower().strip(), set()).add(c.primitive)
        result.intersections = {d: sorted(p) for d, p in by_domain.items()
                                if len(p) >= 2 and d}
        result.correlations = [c.unexpected_correlation for c in result.candidates
                               if c.unexpected_correlation]
        return result
