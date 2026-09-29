"""
test_goodhart_typeI.py — the Type-I control: false-positive metric, mixed forger, and the fraud it exposes.

Pins:
  1. false_positive_rate: among gold==VALID, fraction condemned (not cleared);
  2. MixedArithForger emits BOTH gold-VALID (true) and gold-INVALID (false) claims; every true tactic is VALID;
  3. run_typeI on an over-condemning auditor (always 'defect:true') -> escape ~0 BUT false-positive ~1: the
     low escape is exposed as a fraud (the whole point of the control);
  4. a fooled auditor (always 'defect:false') -> escape ~1, false-positive ~0.
"""
import json
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "goodhart"))

import analysis as A          # noqa: E402
import forger as F            # noqa: E402
import gold_mechanical as G   # noqa: E402
import ollama_client as OC    # noqa: E402
import run_typeI as T         # noqa: E402


class TestFalsePositive(unittest.TestCase):
    def test_metric(self):
        recs = [{"gold": "VALID", "cleared": True}, {"gold": "VALID", "cleared": False},
                {"gold": "INVALID", "cleared": True}]
        fp = A.false_positive_rate(recs)
        self.assertEqual(fp["n_valid"], 2)
        self.assertEqual(fp["n_condemned"], 1)
        self.assertEqual(fp["rate"], 0.5)


class TestMixedForger(unittest.TestCase):
    def test_emits_both_and_true_are_valid(self):
        g = G.MechanicalGold()
        mf = F.MixedArithForger(seed=2, p_valid=0.5)
        labels = [g.label(mf.forge(4, [])) for _ in range(120)]
        self.assertIn("VALID", labels)
        self.assertIn("INVALID", labels)
        # every TRUE-ladder tactic yields VALID (guaranteed by embedding the exact value)
        import random
        rng = random.Random(0)
        for lvl in F._TRUE_LADDER:
            for t in lvl:
                self.assertEqual(g.label({"kind": "arith", "expr": t(rng)}), "VALID")


class TestTypeIRun(unittest.TestCase):
    def _run(self, answer):
        orig = OC.make_chat
        OC.make_chat = lambda *a, **k: (lambda prompt: answer)
        try:
            with tempfile.TemporaryDirectory() as d:
                out = os.path.join(d, "t.json")
                T.main(["--model", "mock", "--cell", "defenses_off",
                        "--pressures", "8", "--k", "12", "--seeds", "2", "--out", out])
                return json.load(open(out, encoding="utf-8"))
        finally:
            OC.make_chat = orig

    def test_over_condemner_is_exposed(self):
        res = self._run('{"defect": true}')          # condemns EVERYTHING
        c = res["curve"]["8"]
        self.assertEqual(c["escape"]["mean"], 0.0)            # catches all invalid -> escape 0 (looks great)
        self.assertEqual(c["false_positive"]["mean"], 1.0)   # ...but condemns all valid -> fraud exposed

    def test_fooled_auditor(self):
        res = self._run('{"defect": false}')          # clears EVERYTHING
        c = res["curve"]["8"]
        self.assertEqual(c["escape"]["mean"], 1.0)           # lets all invalid through
        self.assertEqual(c["false_positive"]["mean"], 0.0)   # but never wrongly condemns a valid


if __name__ == "__main__":
    unittest.main()
