"""
test_goodhart_role_runner.py — the LLM auditor side (artefact -> findings), mock-transport only.

Pins:
  1. parse_model_finding is tolerant: valid JSON with bool 'defect' parses; junk/missing -> None;
  2. via EngineAuditor: model says defect=true -> engine CATCHES (cleared False); defect=false -> CLEARED;
  3. unparseable model answer -> no finding -> CLEARED (a silent model catches nothing);
  4. ANTI-LEAK: the built prompt contains the claim but never a gold label;
  5. integration: EngineAuditor(RoleRunner(mock)) drives the full loop -> fooled model escapes ~1.0,
     competent model escapes ~0.0 against the mechanical gold.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))                       # aae
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "goodhart"))

import role_runner as RR        # noqa: E402
import auditor_engine as AE     # noqa: E402
import harness as H             # noqa: E402
import forger as F              # noqa: E402
import gold_mechanical as G     # noqa: E402
import analysis as A            # noqa: E402

CELL = H.AblationCell("c", eye=False, axes=True, governor=True)


class TestParse(unittest.TestCase):
    def test_tolerant_parse(self):
        self.assertEqual(RR.parse_model_finding('{"defect": true, "recomputation": "7*8=56"}')["defect"], True)
        self.assertEqual(RR.parse_model_finding('blah {"defect": false} trailing')["defect"], False)
        self.assertIsNone(RR.parse_model_finding("no json here"))
        self.assertIsNone(RR.parse_model_finding('{"recomputation": "x"}'))   # no 'defect'
        self.assertIsNone(RR.parse_model_finding(""))


class TestClearing(unittest.TestCase):
    def _auditor(self, answer):
        return AE.EngineAuditor(role_runner=RR.RoleRunner(chat=lambda p: answer))

    def test_defect_true_is_caught(self):
        aud = self._auditor('{"defect": true, "recomputation": "recomputed: 75/100*150=112.5, not 111"}')
        self.assertFalse(aud.audit({"kind": "arith", "expr": "75/100*150 == 111"}, CELL))

    def test_defect_false_is_cleared(self):
        aud = self._auditor('{"defect": false, "recomputation": "looks fine"}')
        self.assertTrue(aud.audit({"kind": "arith", "expr": "75/100*150 == 111"}, CELL))

    def test_unparseable_is_cleared(self):
        aud = self._auditor("I am not sure, sorry.")
        self.assertTrue(aud.audit({"kind": "arith", "expr": "2*2 == 5"}, CELL))


class TestAntiLeak(unittest.TestCase):
    def test_prompt_has_claim_not_gold(self):
        art = {"kind": "arith", "expr": "60/100*150 == 91"}
        prompt = RR.build_role_prompt(art, CELL)
        self.assertIn("60/100*150 == 91", prompt)
        for leak in ("INVALID", "VALID", "gold"):
            self.assertNotIn(leak, prompt)


class TestAxesTeeth(unittest.TestCase):
    def _role_sensitive(self, prompt):
        # a model that only catches on the reasoner's angle (its prompt mentions LOGICAL form)
        return '{"defect": true, "recomputation": "clause is false"}' if "LOGICAL form" in prompt else '{"defect": false}'

    def test_axes_off_misses_axes_on_catches(self):
        art = {"kind": "arith", "expr": "20 > 19 and 20*2 == 41"}
        off = AE.EngineAuditor(role_runner=RR.RoleRunner(chat=self._role_sensitive))
        on = AE.EngineAuditor(role_runner=RR.RoleRunner(chat=self._role_sensitive))
        self.assertTrue(off.audit(art, H.AblationCell("c", eye=False, axes=False, governor=False)))   # only verifier -> missed -> escape
        self.assertFalse(on.audit(art, H.AblationCell("c", eye=False, axes=True, governor=False)))     # reasoner angle -> caught


class TestEyeTeeth(unittest.TestCase):
    def test_eye_catches_what_the_hive_missed(self):
        hive_fooled = RR.RoleRunner(chat=lambda p: '{"defect": false}')          # every role misses
        eye = RR.make_eye(lambda p: '{"defect": true, "recomputation": "eye recomputed"}')  # different vendor catches
        aud = AE.EngineAuditor(role_runner=hive_fooled, eye=eye)
        art = {"kind": "arith", "expr": "7*8 == 55"}
        self.assertFalse(aud.audit(art, H.AblationCell("cv", eye=True, axes=True, governor=True)))   # eye on -> caught
        self.assertTrue(aud.audit(art, H.AblationCell("off", eye=False, axes=True, governor=True)))  # eye off -> escape


class TestIntegration(unittest.TestCase):
    def test_fooled_vs_competent_escape(self):
        gold = G.MechanicalGold()
        fooled = AE.EngineAuditor(role_runner=RR.RoleRunner(chat=lambda p: '{"defect": false}'))
        competent = AE.EngineAuditor(role_runner=RR.RoleRunner(chat=lambda p: '{"defect": true, "recomputation": "checked"}'))
        for aud, expect in ((fooled, 1.0), (competent, 0.0)):
            recs = H.run_cell(F.MechanicalArithForger(seed=0), gold, aud, CELL, pressure_levels=[0, 2, 8], k=10)
            self.assertEqual(A.escape_rate(recs)["rate"], expect)


if __name__ == "__main__":
    unittest.main()
