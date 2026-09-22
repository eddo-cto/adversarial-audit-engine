"""
test_attack_gate.py — the attack-gate, the dual of the defense-gate (round 23).

Pins:
  1. a cleared element (ARTIFACT_HOLDS) WITHOUT a declared attack is FLAGGED (record-only);
  2. a cleared element WITH attack.attempted + a vector is NOT flagged;
  3. the gate NEVER changes a verdict (record-only — unlike the defense-gate which downgrades);
  4. the attack-vector library is per defect_class and injected into role prompts;
  5. parse_finding reads the attack field end-to-end through the pipeline.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

from aae.schema import (Ledger, Finding, Accusation, Defense, Attack, Verdict, Posta,
                        DefectClass, EvidenceBase)                     # noqa: E402
from aae.gates import enforce_attack_gate                              # noqa: E402
from aae import attack_vectors as av                                  # noqa: E402
from aae import roles as roles_mod                                    # noqa: E402
from aae import pipeline                                              # noqa: E402


def _holds(attack=None, fid="H-1"):
    f = Finding(
        id=fid, element="a cleared element", taxonomy_cell="mechanisms",
        defect_class=DefectClass.NUMERIC, posta=Posta.LOW,
        accusation=Accusation(text="maybe wrong", base=EvidenceBase.EXECUTION, evidence="x"),
        defense=Defense(attempted=True, present=True, fact="it is actually correct"),
        attack=attack or Attack(),
    )
    f.verdict = Verdict.ARTIFACT_HOLDS
    return f


class TestAttackGate(unittest.TestCase):
    def test_holds_without_attack_is_flagged(self):
        led = Ledger(artifact_name="a"); led.add(_holds())
        notes = enforce_attack_gate(led)
        self.assertTrue(notes)
        self.assertTrue(any("ATTACK-GATE" in fl for fl in led.flags))

    def test_holds_with_declared_attack_is_not_flagged(self):
        led = Ledger(artifact_name="a")
        led.add(_holds(attack=Attack(attempted=True, vector="recompute the quantity independently")))
        notes = enforce_attack_gate(led)
        self.assertEqual(notes, [])
        self.assertFalse(any("ATTACK-GATE" in fl for fl in led.flags))

    def test_gate_never_changes_verdict(self):
        led = Ledger(artifact_name="a"); f = _holds(); led.add(f)
        enforce_attack_gate(led)
        self.assertEqual(f.verdict, Verdict.ARTIFACT_HOLDS)  # record-only

    def test_condemnation_is_ignored_by_attack_gate(self):
        # the attack-gate only speaks about clearances; a defect finding is not its business
        led = Ledger(artifact_name="a")
        f = _holds(); f.verdict = Verdict.ARTIFACT_DEFECTIVE; led.add(f)
        enforce_attack_gate(led)
        self.assertFalse(any("ATTACK-GATE" in fl for fl in led.flags))


class TestAttackVectorLibrary(unittest.TestCase):
    def test_vectors_per_defect_class(self):
        self.assertTrue(av.vectors_for("numeric"))
        self.assertTrue(av.vectors_for("epistemic"))
        self.assertEqual(av.vectors_for("does_not_exist"), [])

    def test_menu_rendered_into_role_prompt(self):
        menu = av.render_for_prompt()
        self.assertIn("ATTACK VECTORS", menu)
        r = roles_mod.CORE_ROLES["verifier"]
        system, _ = r.build_prompt(artifact="x", dossier="y", taxonomy=["mechanisms"])
        self.assertIn("ATTACK VECTORS", system)     # every role carries the menu


class TestEndToEnd(unittest.TestCase):
    def test_pipeline_reads_attack_and_flags(self):
        payload = {
            "artifact_name": "smoke", "internal_identity": "anthropic:claude-x", "max_posta": "low",
            "excluded_cells": {c: "n/a" for c in
                               ("premises", "inputs", "mechanisms", "outputs", "boundary", "interface")},
            "findings": [{
                "source_role": "verifier", "element": "the value", "taxonomy_cell": "mechanisms",
                "defect_class": "numeric", "posta": "low",
                "accusation": {"text": "maybe", "base": "execution", "evidence": "the value is 5"},
                "defense": {"attempted": True, "present": True, "fact": "5 is correct"},
                # NOTE: no attack declared -> should be flagged, verdict must stay HOLDS
                "action": "",
            }],
        }
        res = pipeline.discipline(payload)
        f = res.ledger.findings[0]
        self.assertEqual(f.verdict, Verdict.ARTIFACT_HOLDS)
        self.assertTrue(any("ATTACK-GATE" in fl for fl in res.ledger.flags))


if __name__ == "__main__":
    unittest.main()
