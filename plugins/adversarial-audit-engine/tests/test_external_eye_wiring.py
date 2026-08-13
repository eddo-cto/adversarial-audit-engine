"""test_external_eye_wiring.py — G3: the independent eye is wired, attested, and vendor-agnostic.

Datapoint 1 stayed level 1: the run used a same-vendor CLAIMED red team, so independence was never
credited. G3 wires an eye into Orchestrator.run() that is CALLED (attested by its adapter), and credits
independence at its true level. The build must NOT be rigid: a LOCAL Ollama eye earns the same level-3
credit as a hosted one (confidential runs keep independence without leaving the host), and a missing or
unreachable eye degrades gracefully to level 1 instead of failing.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae import Orchestrator, MockLLMClient, AuditConfig  # noqa: E402
from aae.gates import evaluate_completion  # noqa: E402
from aae.schema import (Ledger, Finding, Accusation, Defense, DefectClass,  # noqa: E402
                        EvidenceBase, Posta, Verdict, IndependenceLevel)


class _FakeEye:
    """An injected different-vendor eye. Its `.identity` is what gets attested."""
    def __init__(self, identity="ollama:llama3.1:8b", fail=False):
        self.identity = identity
        self.fail = fail

    def complete(self, system, user, *, max_tokens=4096, temperature=0.2):
        if self.fail:
            raise ConnectionError("local server not running")
        return "UPHOLD: none decisive. DISPUTE: one. HUMAN: the rest."


def _holds_finding():
    # a defended finding -> ARTIFACT_HOLDS -> not an open blocker
    return Finding(id="H", element="e", taxonomy_cell="mechanisms",
                   defect_class=DefectClass.NUMERIC, posta=Posta.HIGH,
                   accusation=Accusation(text="t", base=EvidenceBase.EXECUTION,
                                         evidence="ev", sections=["s"]),
                   defense=Defense(attempted=True, present=True, fact="defended"),
                   source_role="verifier", source_grade=1)


def _run(external_eye):
    return Orchestrator(MockLLMClient(), external_eye=external_eye).run(
        "artefatto con numeri.", AuditConfig(artifact_path="x"), artifact_name="x")


class ExternalEyeWiring(unittest.TestCase):
    def test_local_ollama_attested_is_credited_level3(self):
        # THE non-rigidity test: a local Ollama identity is different-vendor -> level 3,
        # exactly like a hosted eye. No blockers, so completion reaches the independence branch.
        led = Ledger(artifact_name="x")
        led.add(_holds_finding())
        led.adjudicate_all()
        self.assertEqual(led.findings[0].verdict, Verdict.ARTIFACT_HOLDS)
        st = evaluate_completion(
            led, max_posta=Posta.HIGH, external_identity=None,
            internal_identity="anthropic:claude-opus-5",
            attested_identity="ollama:llama3.1:8b")
        self.assertEqual(st.state, "CROSS_MODEL_REVIEWED")
        self.assertEqual(led.independence_level,
                         IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR)

    def test_injected_eye_runs_and_is_recorded_in_manifest(self):
        res = _run(_FakeEye())
        layers = res.ledger.run_manifest["layers"]
        self.assertEqual(layers["external_auditor"]["status"], "ran")
        self.assertTrue(any("reviewed (attested by adapter)" in str(f) for f in res.ledger.flags))

    def test_no_eye_stays_level1_and_does_not_crash(self):
        res = _run(None)   # explicit: hermetic, no env lookup
        layers = res.ledger.run_manifest["layers"]
        self.assertNotEqual(layers.get("external_auditor", {}).get("status"), "ran")

    def test_unreachable_eye_degrades_gracefully(self):
        res = _run(_FakeEye(fail=True))   # e.g. Ollama not started
        layers = res.ledger.run_manifest["layers"]
        self.assertNotEqual(layers.get("external_auditor", {}).get("status"), "ran")
        self.assertTrue(any("configured but the call failed" in str(f) for f in res.ledger.flags))


if __name__ == "__main__":
    unittest.main()
