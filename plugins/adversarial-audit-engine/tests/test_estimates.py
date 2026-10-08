"""
test_estimates.py — the estimator defense field defense.estimates (1.12, record-only).

Pins (from the decision sheet §6):
  1. p_holds out of [0,1] -> an integrity problem (flag, never a verdict change);
  2. estimates default to [] (a finding that omits them is unchanged);
  3. backward-compat: a 1.11-style payload (no estimates) parses and validates;
  4. round-trip: estimates survive parse -> to_dict;
  5. VERDICT-NEUTRAL: discipline() gives the same verdict with and without estimates (the red line);
  6. estimates present without a defense attempt -> flagged (not an error).
"""
import copy
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

from aae.schema import Finding, Accusation, Defense, Estimate, EvidenceBase, DefectClass, Posta, Verdict  # noqa: E402
from aae.orchestrator import parse_finding                                                               # noqa: E402
from aae import pipeline                                                                                 # noqa: E402


def _finding(estimates=None, attempted=True):
    f = Finding(id="F1", element="v", taxonomy_cell="mechanisms", defect_class=DefectClass.NUMERIC,
                posta=Posta.LOW,
                accusation=Accusation(text="maybe", base=EvidenceBase.EXECUTION, evidence="x"),
                defense=Defense(attempted=attempted, present=True, fact="ok", estimates=estimates or []))
    f.verdict = Verdict.ARTIFACT_HOLDS
    return f


class TestValidation(unittest.TestCase):
    def test_p_holds_out_of_range_flagged(self):
        f = _finding([{"subclaim_id": "s1", "text": "t", "p_holds": 1.7}])
        self.assertTrue(any("p_holds must be in [0,1]" in p for p in f.validate()))

    def test_valid_estimate_ok(self):
        f = _finding([{"subclaim_id": "s1", "text": "t", "p_holds": 0.6}])
        self.assertFalse(any("p_holds" in p for p in f.validate()))

    def test_default_empty(self):
        self.assertEqual(_finding().defense.estimates, [])

    def test_estimates_without_attempt_flagged(self):
        f = _finding([{"subclaim_id": "s1", "text": "t", "p_holds": 0.6}], attempted=False)
        self.assertTrue(any("without a defense attempt" in p for p in f.validate()))


class TestBackwardCompatAndRoundTrip(unittest.TestCase):
    def test_1_11_payload_parses(self):
        raw = {"element": "v", "defect_class": "numeric", "posta": "low",
               "accusation": {"text": "t", "base": "execution", "evidence": "x"},
               "defense": {"attempted": True, "present": True, "fact": "ok"}}   # NO estimates (1.11 shape)
        f = parse_finding(raw, role_key="verifier")
        self.assertIsNotNone(f)
        self.assertEqual(f.defense.estimates, [])

    def test_round_trip(self):
        raw = {"element": "v", "defect_class": "numeric", "posta": "low",
               "accusation": {"text": "t", "base": "execution", "evidence": "x"},
               "defense": {"attempted": True, "present": True, "fact": "ok",
                           "estimates": [{"subclaim_id": "s1", "text": "sub", "p_holds": 0.75}]}}
        f = parse_finding(raw, role_key="verifier")
        self.assertEqual(f.defense.estimates[0].p_holds, 0.75)
        d = f.to_dict()
        self.assertEqual(d["defense"]["estimates"], [{"subclaim_id": "s1", "text": "sub", "p_holds": 0.75}])


class TestVerdictNeutral(unittest.TestCase):
    def _payload(self, with_estimates):
        pl = {"artifact_name": "x", "internal_identity": "anthropic:c", "max_posta": "low",
              "excluded_cells": {c: "n/a" for c in ("premises", "inputs", "mechanisms", "outputs", "boundary", "interface")},
              "findings": [{"source_role": "verifier", "element": "v", "taxonomy_cell": "mechanisms",
                            "defect_class": "numeric", "posta": "low", "source_grade": 1,
                            "accusation": {"text": "maybe", "base": "execution", "evidence": "the value is 5"},
                            "defense": {"attempted": True, "present": True, "fact": "5 is correct"}, "action": ""}]}
        if with_estimates:
            pl["findings"][0]["defense"]["estimates"] = [{"subclaim_id": "s1", "text": "5 holds", "p_holds": 0.3}]
        return pl

    def test_same_verdict_with_and_without(self):
        v0 = pipeline.discipline(copy.deepcopy(self._payload(False))).ledger.findings[0].verdict
        v1 = pipeline.discipline(copy.deepcopy(self._payload(True))).ledger.findings[0].verdict
        self.assertEqual(v0, v1)   # estimates NEVER change a verdict in 1.12


if __name__ == "__main__":
    unittest.main()
