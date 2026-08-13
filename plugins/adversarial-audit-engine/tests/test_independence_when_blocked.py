"""test_independence_when_blocked.py — an attested cross-vendor eye must be recorded on the
ledger EVEN when the run is BLOCKED on open items.

A real EIA-study audit (Claude Code, local Ollama eye) genuinely called a different-vendor model
that corroborated a defect, yet the ledger read independence_level 1: `evaluate_completion` returned
BLOCKED_OPEN_ITEMS before crediting the attested reviewer, so the independence fact was lost from the
record. Completion STATE and independence LEVEL are separate; the level must reflect who reviewed.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae.schema import (Ledger, Finding, Accusation, Defense, DefectClass,  # noqa: E402
                        EvidenceBase, Posta, IndependenceLevel)
from aae.gates import evaluate_completion  # noqa: E402


def _open_blocker_finding():
    # a PATTERN-based finding adjudicates to NEEDS_READING -> an open blocker
    return Finding(id="P-1", element="pattern flag", taxonomy_cell="mechanisms",
                   defect_class=DefectClass.NON_LOCAL_MECHANICAL, posta=Posta.HIGH,
                   accusation=Accusation(text="looks off", base=EvidenceBase.PATTERN,
                                         evidence="pattern", sections=["§1", "§2"]),
                   defense=Defense(attempted=True), source_role="propagator", source_grade=1)


class IndependenceSurvivesBlock(unittest.TestCase):
    def test_attested_level_recorded_even_when_blocked(self):
        led = Ledger(artifact_name="eia.pdf")
        led.add(_open_blocker_finding())
        led.adjudicate_all()
        st = evaluate_completion(
            led, max_posta=Posta.HIGH, external_identity=None,
            internal_identity="anthropic:claude-opus-5",
            attested_identity="ollama-local:llama3.1:8b")
        # the run is honestly blocked...
        self.assertEqual(st.state, "BLOCKED_OPEN_ITEMS")
        # ...but the attested cross-vendor eye is on record at its true level (3)
        self.assertEqual(led.independence_level,
                         IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR)

    def test_no_eye_blocked_stays_level_1(self):
        led = Ledger(artifact_name="eia.pdf")
        led.add(_open_blocker_finding())
        led.adjudicate_all()
        st = evaluate_completion(
            led, max_posta=Posta.HIGH, external_identity=None,
            internal_identity="anthropic:claude-opus-5", attested_identity=None)
        self.assertEqual(st.state, "BLOCKED_OPEN_ITEMS")
        self.assertEqual(led.independence_level, IndependenceLevel.SAME_INSTANCE_ROLES)


if __name__ == "__main__":
    unittest.main()
