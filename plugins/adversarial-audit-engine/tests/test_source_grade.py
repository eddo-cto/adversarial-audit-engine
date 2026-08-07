"""
test_source_grade.py — round-12 source-grade gate (§7.1) and the self-
instrumentation flag (§7.6), both from the finance runs.
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

from aae.schema import (Ledger, Finding, Accusation, Defense, DefectClass,  # noqa: E402
                        EvidenceBase, Posta, Verdict, ActionState)
from aae.source_grade import (SourceGrade, enforce_source_grade_gate,  # noqa: E402
                              source_grade_coverage)


def _condemning(fid, grade):
    f = Finding(id=fid, element="e", taxonomy_cell="mechanisms",
                defect_class=DefectClass.NUMERIC, posta=Posta.HIGH,
                accusation=Accusation(text="t", base=EvidenceBase.EXECUTION,
                                      evidence="ev", sections=["s1"]),
                defense=Defense(attempted=True, present=False, fact=None),
                action="fix", source_grade=grade)
    f.adjudicate()  # EXECUTION + defense attempted, no fact -> ARTIFACT_DEFECTIVE
    assert f.verdict == Verdict.ARTIFACT_DEFECTIVE
    return f


class SourceGradeGate(unittest.TestCase):
    def test_secondary_source_conviction_is_downgraded(self):
        led = Ledger(artifact_name="x")
        led.add(_condemning("F1", SourceGrade.INSTITUTIONAL))
        notes = enforce_source_grade_gate(led, primary_reachable=True)
        self.assertEqual(Verdict.NEEDS_READING, led.findings[0].verdict)
        self.assertTrue(any("source-grade" in n for n in notes))

    def test_primary_source_conviction_stands(self):
        led = Ledger(artifact_name="x")
        led.add(_condemning("F1", SourceGrade.PRIMARY_FILED))
        enforce_source_grade_gate(led, primary_reachable=True)
        self.assertEqual(Verdict.ARTIFACT_DEFECTIVE, led.findings[0].verdict)

    def test_gate_abstains_when_no_primary_exists(self):
        led = Ledger(artifact_name="x")
        led.add(_condemning("F1", SourceGrade.GENERALIST))
        enforce_source_grade_gate(led, primary_reachable=False)
        self.assertEqual(Verdict.ARTIFACT_DEFECTIVE, led.findings[0].verdict)

    def test_undeclared_grade_is_treated_as_non_primary(self):
        led = Ledger(artifact_name="x")
        led.add(_condemning("F1", 9))  # UNKNOWN default
        enforce_source_grade_gate(led, primary_reachable=True)
        self.assertEqual(Verdict.NEEDS_READING, led.findings[0].verdict)

    def test_coverage_counts_per_grade(self):
        led = Ledger(artifact_name="x")
        for i, g in enumerate((1, 1, 2, 3, 9)):
            led.add(_condemning(f"F{i}", g))
        cov = source_grade_coverage(led)
        self.assertEqual({1: 2, 2: 1, 3: 1, 0: 1}, cov)


def _load_run_core():
    spec = importlib.util.spec_from_file_location(
        "run_core", os.path.join(_SCRIPTS, "run_core.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RunCoreWiring(unittest.TestCase):
    def _payload(self, grade, discarded=False):
        f = {"id": "V-1", "element": "e", "taxonomy_cell": "mechanisms",
             "defect_class": "numeric", "posta": "high",
             "accusation": {"text": "t", "base": "execution", "evidence": "ev",
                            "sections": ["s1"]},
             "defense": {"attempted": True, "present": False, "fact": None},
             "action": "fix", "declared_limit": "x", "source_role": "verifier",
             "source_grade": grade}
        if discarded:
            f["action_state"] = "deliberately_discarded"
            f["discard_justification"] = "killed by a verifiable defending fact"
        return {"artifact_name": "t", "internal_identity": "anthropic:opus",
                "findings": [f]}

    def test_run_core_downgrades_secondary_conviction_and_flags_instrumentation(self):
        rc = _load_run_core()
        with tempfile.TemporaryDirectory() as d:
            res = rc.run(self._payload(grade=3), d)
            self.assertEqual(Verdict.NEEDS_READING, res.ledger.findings[0].verdict)
            self.assertTrue(any("source-grade" in fl for fl in res.ledger.flags))
            self.assertTrue(any("SELF-INSTRUMENTATION" in fl for fl in res.ledger.flags))


if __name__ == "__main__":
    unittest.main()
