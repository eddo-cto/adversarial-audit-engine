"""
test_estimator_brier.py — proper scoring of the estimator defense (experiments/), deterministic.

Pins:
  1. perfect calibration (p=1 on holds, p=0 on fails) -> Brier 0;
  2. worst (p=0 on holds, p=1 on fails) -> Brier 1;
  3. PROPERNESS smoke: on a sub-claim that truly holds, honest p=0.9 scores better (lower Brier) than an
     inflated p=0.5-away report — i.e. reporting the truth is not punished.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "experiments"))

import estimator_brier as B    # noqa: E402


class TestBrier(unittest.TestCase):
    def test_perfect(self):
        est = [{"subclaim_id": "a", "p_holds": 1.0}, {"subclaim_id": "b", "p_holds": 0.0}]
        out = {"a": True, "b": False}
        self.assertEqual(B.brier(est, out), 0.0)

    def test_worst(self):
        est = [{"subclaim_id": "a", "p_holds": 0.0}, {"subclaim_id": "b", "p_holds": 1.0}]
        out = {"a": True, "b": False}
        self.assertEqual(B.brier(est, out), 1.0)

    def test_properness_smoke(self):
        out = {"a": True}
        honest = B.brier([{"subclaim_id": "a", "p_holds": 0.9}], out)     # close to truth
        hedged = B.brier([{"subclaim_id": "a", "p_holds": 0.4}], out)     # under-confident
        self.assertLess(honest, hedged)

    def test_score_bundle(self):
        s = B.score([{"subclaim_id": "a", "p_holds": 0.8}], {"a": True})
        self.assertEqual(s["n_scored"], 1)
        self.assertAlmostEqual(s["brier"], 0.04, places=6)


if __name__ == "__main__":
    unittest.main()
