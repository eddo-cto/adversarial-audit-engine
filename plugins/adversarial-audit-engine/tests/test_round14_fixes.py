"""
test_round14_fixes.py — regressions for the three defects the measurement run
found in the round-12/13 instrumentation, on the documented payload path.

  V-1  parse_finding dropped action_state / discard_justification, so the §7.6
       denominator counter was structurally always 0 (self-instrumentation flag
       fired even when killed hypotheses were declared).
  V-2  the governor counted ALL ledger flags as coverage gaps (len(led.flags)),
       mislabelling e.g. SELF-INSTRUMENTATION as an uncovered taxonomy dimension.
  V-3  source_grade_coverage was imported but never called, so the per-grade
       breakdown never reached the ledger.
"""
import importlib.util
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_PLUGIN, "scripts")
sys.path.insert(0, _PLUGIN)

from aae.orchestrator import parse_finding  # noqa: E402
from aae.schema import ActionState  # noqa: E402


def _load_run_core():
    spec = importlib.util.spec_from_file_location(
        "run_core", os.path.join(_SCRIPTS, "run_core.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V1_ParseDiscarded(unittest.TestCase):
    def test_parse_finding_reads_action_state_and_justification(self):
        f = parse_finding({
            "element": "killed", "taxonomy_cell": "outputs", "defect_class": "numeric",
            "posta": "high", "accusation": {"text": "t", "base": "domain_knowledge",
                                            "evidence": "e", "sections": ["a"]},
            "defense": {"attempted": True, "present": True, "fact": "the fact"},
            "action_state": "deliberately_discarded",
            "discard_justification": "defense-fact"}, role_key="propagator")
        self.assertEqual(ActionState.DELIBERATELY_DISCARDED, f.action_state)
        self.assertEqual("defense-fact", f.discard_justification)

    def test_declared_discarded_suppresses_self_instrumentation_flag(self):
        rc = _load_run_core()
        payload = {"artifact_name": "t", "internal_identity": "anthropic:opus",
                   "max_posta": "high", "source_primary_reachable": False,
                   "findings": [
                       {"id": "V-1", "element": "e", "taxonomy_cell": "mechanisms",
                        "defect_class": "numeric", "posta": "high",
                        "accusation": {"text": "t", "base": "execution", "evidence": "e",
                                       "sections": ["a"]},
                        "defense": {"attempted": True}, "action": "fix",
                        "declared_limit": "x", "source_role": "verifier", "source_grade": 1},
                       {"id": "H-K", "element": "killed", "taxonomy_cell": "outputs",
                        "defect_class": "numeric", "posta": "high",
                        "accusation": {"text": "t", "base": "domain_knowledge",
                                       "evidence": "e", "sections": ["a"]},
                        "defense": {"attempted": True, "present": True, "fact": "f"},
                        "source_role": "propagator", "source_grade": 2,
                        "action_state": "deliberately_discarded",
                        "discard_justification": "defense-fact"}]}
        with tempfile.TemporaryDirectory() as d:
            res = rc.run(payload, d)
            self.assertFalse(any("SELF-INSTRUMENTATION" in fl for fl in res.ledger.flags),
                             f"flag fired despite a declared discarded hypothesis: {res.ledger.flags}")

    def test_source_grade_coverage_is_recorded(self):
        rc = _load_run_core()
        payload = {"artifact_name": "t", "internal_identity": "anthropic:opus",
                   "source_primary_reachable": False,
                   "findings": [{"id": "V-1", "element": "e", "taxonomy_cell": "mechanisms",
                                 "defect_class": "numeric", "posta": "high",
                                 "accusation": {"text": "t", "base": "execution",
                                                "evidence": "e", "sections": ["a"]},
                                 "defense": {"attempted": True}, "action": "fix",
                                 "declared_limit": "x", "source_role": "verifier",
                                 "source_grade": 1}]}
        with tempfile.TemporaryDirectory() as d:
            res = rc.run(payload, d)
            self.assertEqual(1, res.ledger.source_grade_coverage.get(1))


class V2_GovernorCoverage(unittest.TestCase):
    def test_non_coverage_flags_are_not_counted_as_uncovered_dimensions(self):
        # Full taxonomy coverage + a non-coverage flag (a source-grade downgrade).
        # The governor must NOT report an uncovered dimension.
        rc = _load_run_core()
        cells = ["premises", "inputs", "mechanisms", "outputs", "boundary", "interface"]
        findings = [{"id": f"F{i}", "element": "e", "taxonomy_cell": c,
                     "defect_class": "numeric", "posta": "high",
                     "accusation": {"text": "t", "base": "execution", "evidence": "e",
                                    "sections": ["a"]},
                     "defense": {"attempted": True}, "action": "fix",
                     "declared_limit": "x", "source_role": "verifier",
                     "source_grade": 1} for i, c in enumerate(cells)]
        # force a non-coverage flag: a conviction on a grade-3 source, primary reachable
        findings[0]["source_grade"] = 3
        payload = {"artifact_name": "t", "internal_identity": "anthropic:opus",
                   "source_primary_reachable": True, "findings": findings}
        with tempfile.TemporaryDirectory() as d:
            res = rc.run(payload, d)
            self.assertTrue(any("source-grade" in fl for fl in res.ledger.flags))  # non-coverage flag present
            self.assertFalse(any("COVERAGE INCOMPLETE" in fl for fl in res.ledger.flags))  # coverage full
            summary = res.summary()
            self.assertNotIn("uncovered", summary.lower())


if __name__ == "__main__":
    unittest.main()
