"""test_source_grade_in_orchestrator.py — G1: the source-grade gate runs IN THE ENGINE.

Before G1 the gate was hand-wired AFTER the orchestrator in the run script (and, worse, after
completion and the manifest were already computed). These tests pin that Orchestrator.run() itself:
  (1) always reports source_grade_coverage (a measured fact, not a late-noticed one), and
  (2) downgrades a worse-than-primary condemnation to NEEDS_READING when a primary is reachable,
      and abstains when the operator declares no primary exists (primary_reachable=False).

The mock propagator emits an undeclared-grade (=9) condemnation, so it is exactly the case the gate
must catch — through the orchestrator door, with no external call.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae import Orchestrator, MockLLMClient, AuditConfig  # noqa: E402
from aae.schema import Verdict  # noqa: E402


def _run(primary_reachable: bool):
    cfg = AuditConfig(artifact_path="prova.md", primary_reachable=primary_reachable)
    return Orchestrator(MockLLMClient()).run(
        "artefatto di prova con numeri.", cfg, artifact_name="prova.md").ledger


class SourceGradeInEngine(unittest.TestCase):
    def test_coverage_always_reported_by_the_engine(self):
        led = _run(primary_reachable=True)
        cov = led.source_grade_coverage
        self.assertIsInstance(cov, dict)
        self.assertTrue(cov, "coverage must be populated by run(), not left empty")
        self.assertEqual(sum(cov.values()), len(led.findings))

    def test_gate_downgrades_worse_than_primary_condemnation(self):
        led = _run(primary_reachable=True)
        # the undeclared-grade propagator condemnation must have been read-gated
        downgraded = [f for f in led.findings if f.verdict == Verdict.NEEDS_READING]
        self.assertTrue(
            downgraded,
            "a worse-than-primary condemnation should be downgraded to NEEDS_READING")

    def test_gate_abstains_when_no_primary_exists(self):
        # Same run, but the operator declares no primary is reachable: the gate must
        # NOT punish. The propagator finding stays a condemnation instead of NEEDS_READING.
        reach = _run(primary_reachable=True)
        noreach = _run(primary_reachable=False)
        reads_when_reachable = {f.id for f in reach.findings if f.verdict == Verdict.NEEDS_READING}
        reads_when_not = {f.id for f in noreach.findings if f.verdict == Verdict.NEEDS_READING}
        self.assertTrue(
            reads_when_reachable - reads_when_not,
            "at least one finding is read-gated only when a primary is reachable")


if __name__ == "__main__":
    unittest.main()
