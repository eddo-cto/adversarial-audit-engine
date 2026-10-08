"""
test_self_test_runner.py — the self-test orchestrator (1.12), mock auditor only (no LLM).

Pins:
  1. measure_g over a perfect auditor -> severity-recall 1.0, fp_rate 0.0;
  2. gate_against_baseline: no baseline -> passes (establishes it); a degraded run vs a written baseline -> fails.
"""
import json
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "self_test"))

import run_selftest as R     # noqa: E402


def perfect_auditor(case):
    return [{"verdict": "accusa_vince", "defect_class": d["defect_class"],
             "accusation": {"evidence": d["verbatim"]}} for d in case["defects"]]


def blind_auditor(case):
    # finds nothing on defects, and wrongly condemns clean cases
    if case["label"] == "clean":
        return [{"verdict": "accusa_vince", "defect_class": "numeric",
                 "accusation": {"evidence": case["source_text"][:15]}}]
    return []


class TestRunner(unittest.TestCase):
    def test_perfect_measure(self):
        g = R.measure_g(perfect_auditor, n=30)
        self.assertEqual(g["recall_severity"], 1.0)
        self.assertEqual(g["fp_rate"], 0.0)

    def test_gate_no_baseline_then_regression(self):
        with tempfile.TemporaryDirectory() as d:
            base_path = os.path.join(d, "baseline_g.json")
            good = R.measure_g(perfect_auditor, n=30)
            self.assertTrue(R.gate_against_baseline(good, base_path)["passed"])   # no baseline yet
            json.dump(good, open(base_path, "w", encoding="utf-8"))               # freeze baseline
            bad = R.measure_g(blind_auditor, n=30)
            self.assertFalse(R.gate_against_baseline(bad, base_path)["passed"])   # regression caught


if __name__ == "__main__":
    unittest.main()
