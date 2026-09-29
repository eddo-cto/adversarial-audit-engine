"""
test_goodhart_engine_audit.py — the FAITHFUL auditor (real defense-first contract), mock transport only.

Pins:
  1. parse_audit tolerant; defense-first mapping;
  2. model defends the claim (defense_holds=true) -> HELD -> CLEARED (this is what kills the false-positive
     the strawman produced by hard-coding present=False);
  3. defence fails (defect=true, defense_holds=false) -> condemned -> CAUGHT;
  4. anti-leak: prompt has the claim, never a gold label.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "goodhart"))

import engine_audit as EA      # noqa: E402
import auditor_engine as AE    # noqa: E402
import harness as H            # noqa: E402

CELL = H.AblationCell("c", eye=False, axes=True, governor=True)
V = {"id": "V", "artifact": "7+13+19+31 = 70", "class_hint": "numeric"}
I = {"id": "I", "artifact": "12+17+26 = 45", "class_hint": "numeric"}


class TestParse(unittest.TestCase):
    def test_tolerant(self):
        self.assertEqual(EA.parse_audit('{"defense_holds": true, "defect": false}')["defect"], False)
        self.assertIsNone(EA.parse_audit("no json"))


class TestFaithfulClearing(unittest.TestCase):
    def test_defended_claim_is_cleared(self):
        aud = AE.EngineAuditor(role_runner=EA.RealRoleRunner(chat=lambda p: '{"defense_holds": true, "fact": "sum is 70", "defect": false}'))
        self.assertTrue(aud.audit(V, CELL))       # defended -> cleared -> NO false positive

    def test_failed_defence_is_caught(self):
        aud = AE.EngineAuditor(role_runner=EA.RealRoleRunner(chat=lambda p: '{"defense_holds": false, "defect": true, "fact": "sum is 55 not 45"}'))
        self.assertFalse(aud.audit(I, CELL))      # defence fails -> condemned -> caught


class TestAntiLeak(unittest.TestCase):
    def test_prompt_has_claim_not_gold(self):
        p = EA.build_audit_prompt("12+17+26 = 45", "verifier")
        self.assertIn("12+17+26 = 45", p)
        for leak in ("invalid", "VALID", "gold", "label"):
            self.assertNotIn(leak, p)


if __name__ == "__main__":
    unittest.main()
