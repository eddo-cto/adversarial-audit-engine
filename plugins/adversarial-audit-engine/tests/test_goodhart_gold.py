"""
test_goodhart_gold.py — the mechanical gold oracle (#119): independent, exact, ungameable.

Pins:
  1. true arithmetic/relational claims -> VALID; false ones -> INVALID (exact);
  2. SAFETY: a forged expression with names/calls/imports raises ValueError (cannot execute code);
  3. exactness is not silently relaxed ('arith' is exact); approx only via explicit 'arith_approx'+tol;
  4. unknown kind / non-boolean claim raises (never a silent mislabel);
  5. it satisfies the harness Gold protocol (usable as the loop's gold).
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "goodhart"))

import gold_mechanical as G   # noqa: E402
import harness as H           # noqa: E402


class TestArith(unittest.TestCase):
    def test_true_and_false(self):
        g = G.MechanicalGold()
        self.assertEqual(g.label({"kind": "arith", "expr": "12*12 == 144"}), "VALID")
        self.assertEqual(g.label({"kind": "arith", "expr": "12*12 == 145"}), "INVALID")
        self.assertEqual(g.label({"kind": "arith", "expr": "60/100*150 == 90"}), "VALID")
        self.assertEqual(g.label({"kind": "arith", "expr": "2 < 1 or 3 >= 3"}), "VALID")

    def test_exact_not_relaxed(self):
        g = G.MechanicalGold()
        # a near-miss that is actually false must be INVALID, not waved through
        self.assertEqual(g.label({"kind": "arith", "expr": "5*1.609 == 8.0"}), "INVALID")

    def test_approx_only_when_declared(self):
        g = G.MechanicalGold()
        self.assertEqual(g.label({"kind": "arith_approx", "lhs": "5*1.609", "rhs": 8.05, "tol": 0.01}), "VALID")
        self.assertEqual(g.label({"kind": "arith_approx", "lhs": "5*1.609", "rhs": 8.5, "tol": 0.01}), "INVALID")


class TestSafety(unittest.TestCase):
    def test_names_calls_imports_rejected(self):
        for bad in ("__import__('os')", "open('x')", "x + 1", "pow(2,3)", "(1).__class__"):
            with self.assertRaises(ValueError):
                G.safe_eval(bad)

    def test_label_rejects_unknown_kind_and_nonbool(self):
        g = G.MechanicalGold()
        with self.assertRaises(ValueError):
            g.label({"kind": "prose", "text": "whatever"})
        with self.assertRaises(ValueError):
            g.label({"kind": "arith", "expr": "2 + 2"})   # not boolean -> loud, not silent


class TestGoldProtocol(unittest.TestCase):
    def test_usable_as_harness_gold(self):
        g = G.MechanicalGold()
        # one cell, deterministic: gold labels the forged arith artefacts; harness produces tuples
        class ArithForger:
            def forge(self, pressure, feedback):
                # a truly-false claim (INVALID), 'evasion' unused by this gold
                return {"kind": "arith", "expr": "7*8 == 55"}
        class AlwaysClear:
            def audit(self, art, cell): return True
        recs = H.run_cell(ArithForger(), g, AlwaysClear(),
                          H.AblationCell("defenses_off", eye=False, axes=False, governor=False),
                          pressure_levels=[0], k=4)
        self.assertTrue(all(r["gold"] == "INVALID" for r in recs))   # 7*8==55 is false -> INVALID


if __name__ == "__main__":
    unittest.main()
