"""test_refusal_shared.py — the A+B non-bypassable refusal is SHARED, not tied to one door.

A real 0.14.2 run (via the orchestrator, not run_core.py) reported run_manifest INCOMPLETE yet a
non-INVALID completion: the round-18 refusal lived only in run_core.py, so the orchestrator entry point
bypassed it. The refusal was moved into a shared helper (`enforce_run_validity`) applied on every entry
point. These tests pin that: the helper enforces on demand, and an incomplete orchestrator run is forced
to INVALID_RUN.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae.schema import (Ledger, Finding, Accusation, Defense, DefectClass,  # noqa: E402
                        EvidenceBase, Posta)
from aae.run_manifest import build_manifest, enforce_run_validity  # noqa: E402
from aae import Orchestrator, MockLLMClient, AuditConfig  # noqa: E402


def _finding(role):
    return Finding(id=role, element="e", taxonomy_cell="outputs",
                   defect_class=DefectClass.NUMERIC, posta=Posta.HIGH,
                   accusation=Accusation(text="t", base=EvidenceBase.EXECUTION,
                                         evidence="ev", sections=["s1"]),
                   defense=Defense(attempted=True), source_role=role, source_grade=1)


class SharedRefusal(unittest.TestCase):
    def test_helper_forces_invalid_run_when_not_valid(self):
        led = Ledger(artifact_name="x")
        led.add(_finding("verifier"))
        led.completion_state = "EXTERNAL_REVIEW_PENDING"      # some prior state
        m = build_manifest(led, None)                          # required layers missing -> INVALID
        self.assertNotEqual("VALID", m.run_validity)
        enforce_run_validity(led, m)
        self.assertEqual("INVALID_RUN", led.completion_state)  # overridden
        self.assertTrue(any("INVALID_RUN" in str(f) for f in led.flags))
        self.assertTrue(led.run_manifest)                      # manifest recorded

    def test_helper_leaves_a_valid_run_untouched(self):
        led = Ledger(artifact_name="x")
        for r in ("verifier", "propagator"):
            led.add(_finding(r))
        led.findings[0].sources = ["src A"]                    # oracle measured from a cited source
        led.completion_state = "EXTERNAL_REVIEW_PENDING"
        m = build_manifest(
            led, {"layers": {"external_auditor": {"status": "not_applicable", "justification": "single-vendor"},
                             "deep_causal": {"status": "not_applicable", "justification": "thin"}}},
            triage={"dimensions_present": ["outputs"], "deploy_roles": ["verifier", "propagator"]},
            governor_ran=True)
        self.assertEqual("VALID", m.run_validity)
        enforce_run_validity(led, m)
        self.assertEqual("EXTERNAL_REVIEW_PENDING", led.completion_state)  # not overridden
        self.assertFalse(any("INVALID_RUN" in str(f) for f in led.flags))

    def test_orchestrator_entry_point_also_refuses(self):
        # The orchestrator path (not run_core.py) must now apply the same refusal.
        res = Orchestrator(MockLLMClient()).run(
            "artefatto di prova con numeri.", AuditConfig(artifact_path="prova.md"),
            artifact_name="prova.md")
        self.assertTrue(res.ledger.run_manifest)               # manifest built on this path
        # the mock run under-runs the required layers -> INVALID -> refused
        self.assertEqual("INVALID_RUN", res.ledger.completion_state)


if __name__ == "__main__":
    unittest.main()
