"""
metrics.py — Run metrics and the honest expected-recall table.

The product's central honesty: recall is per-CLASS, not global. These numbers
are the empirical summary of seven hostile rounds (six domains, blind roles).
They are not promises; they are declared expectations that route high-stakes,
low-expected-recall classes to a human expert.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import (Ledger, Finding, Verdict, CostToFix, DefectClass)


# Declared expected recall by class (empirical, rounds 1-7). The last class is
# the residual limit: not internally guaranteed → human expert.
EXPECTED_RECALL: dict[DefectClass, str] = {
    DefectClass.LOOKUP: "high",
    DefectClass.NUMERIC: "high",
    DefectClass.IDIOSYNCRATIC_LOCAL: "high",
    DefectClass.NON_LOCAL_MECHANICAL: "high",
    DefectClass.NON_LOCAL_CONCEPTUAL_DOCUMENTED: "medium-high",
    DefectClass.EPISTEMIC: "medium-high",
    DefectClass.ETHICAL: "medium-high",
    DefectClass.PHENOMENOLOGICAL: "medium-high",
    DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL: "low — route to human expert",
}

_COST_RANK = {CostToFix.TRIVIAL: 0, CostToFix.LOW: 1,
              CostToFix.MEDIUM: 2, CostToFix.HIGH: 3}


@dataclass
class Metrics:
    total_findings: int
    by_verdict: dict[str, int]
    by_class: dict[str, int]
    bite_rate: float                 # share of wins with cost >= medium
    false_positive_guard: int        # count of ARTIFACT_HOLDS (discipline signal)
    needs_expert: int
    declared_limits: int

    def as_text(self) -> str:
        lines = [
            f"findings (after dedup): {self.total_findings}",
            f"bite-rate (wins cost>=medium): {self.bite_rate:.0%}",
            f"held / defended (false-positive discipline): {self.false_positive_guard}",
            f"routed to human expert (NEEDS_EXPERT): {self.needs_expert}",
            f"declared internal limits: {self.declared_limits}",
            "by verdict: " + ", ".join(f"{k}={v}" for k, v in self.by_verdict.items()),
            "by class: " + ", ".join(f"{k}={v}" for k, v in self.by_class.items()),
        ]
        return "\n".join(lines)


def compute(ledger: Ledger) -> Metrics:
    findings = ledger.findings
    by_verdict: dict[str, int] = {}
    by_class: dict[str, int] = {}
    for f in findings:
        by_verdict[f.verdict.value] = by_verdict.get(f.verdict.value, 0) + 1
        by_class[f.defect_class.value] = by_class.get(f.defect_class.value, 0) + 1

    wins = [f for f in findings if f.verdict == Verdict.ARTIFACT_DEFECTIVE]
    meaty = [f for f in wins
             if f.cost_to_fix and _COST_RANK[f.cost_to_fix] >= _COST_RANK[CostToFix.MEDIUM]]
    bite = (len(meaty) / len(wins)) if wins else 0.0

    return Metrics(
        total_findings=len(findings),
        by_verdict=by_verdict,
        by_class=by_class,
        bite_rate=bite,
        false_positive_guard=sum(1 for f in findings
                                 if f.verdict == Verdict.ARTIFACT_HOLDS),
        needs_expert=sum(1 for f in findings
                         if f.verdict == Verdict.NEEDS_EXPERT),
        declared_limits=sum(1 for f in findings if f.declared_limit),
    )
