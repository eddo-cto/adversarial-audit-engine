"""test_source_grade_in_orchestrator.py — the source-grade gate runs IN THE ONE disciplined core.

Since unification, both entry points (/audit -> run_core, and Orchestrator.run) funnel through
`pipeline.discipline`, so the source-grade gate is enforced once, on the payload contract. These tests
pin it there with a controlled payload (no source_text, so the grounding gate does not interfere and the
source-grade effect is isolated): coverage is always reported; a worse-than-primary condemnation is
downgraded to NEEDS_READING when a primary is reachable, and the gate abstains when none exists.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(_HERE)
sys.path.insert(0, PLUGIN)

from aae.pipeline import discipline  # noqa: E402
from aae.schema import Verdict  # noqa: E402


def _payload(primary_reachable: bool):
    return {
        "artifact_name": "prova.md",
        "internal_identity": "anthropic:claude-opus-5",
        "external_identity": None,
        "max_posta": "high",
        "source_primary_reachable": primary_reachable,
        # NO source_text -> grounding gate abstains, isolating the source-grade gate
        "triage": {"dimensions_present": ["mechanisms"], "deploy_roles": ["verifier", "propagator"]},
        "findings": [{
            "id": "V-1", "source_role": "verifier", "element": "a numeric claim",
            "taxonomy_cell": "mechanisms", "defect_class": "numeric", "posta": "high",
            "accusation": {"text": "wrong", "base": "execution", "evidence": "recomputed",
                           "sections": ["§1"]},
            "defense": {"attempted": True, "present": False, "fact": None},
            "cost_to_fix": "medium", "action": "fix", "declared_limit": "needs human",
            "sources": ["secondary reproduction"], "severity": "media",
            "source_grade": 2, "action_state": "open"}],
    }


class SourceGradeInEngine(unittest.TestCase):
    def test_coverage_always_reported_by_the_engine(self):
        led = discipline(_payload(primary_reachable=True)).ledger
        cov = led.source_grade_coverage
        self.assertIsInstance(cov, dict)
        self.assertTrue(cov, "coverage must be populated")
        self.assertEqual(sum(cov.values()), len(led.findings))

    def test_gate_downgrades_worse_than_primary_condemnation(self):
        led = discipline(_payload(primary_reachable=True)).ledger
        self.assertEqual(led.findings[0].verdict, Verdict.NEEDS_READING)

    def test_gate_abstains_when_no_primary_exists(self):
        led = discipline(_payload(primary_reachable=False)).ledger
        # source_grade abstains -> the grade-2 condemnation stands, not read-gated
        self.assertNotEqual(led.findings[0].verdict, Verdict.NEEDS_READING)


if __name__ == "__main__":
    unittest.main()
