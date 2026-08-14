"""test_deep_layers_autodeploy.py — G2: deep layers deploy by STAKES, not by a config flag.

Datapoint 1 (an OEPV tender annex, HIGH posta) ran with only the roles: triadic/construens/deep-causal
stayed off because the run script never set the flags. That is the A1 gap. G2 makes the deep passes
auto-deploy when the run warrants depth — HIGH posta, or a conceptual-novel finding — with the Freno
still holding below that. These tests pin the policy and its wiring, including that an auto-run
deep-causal is recorded RAN in the manifest (honest measurement, not a silent extra).
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae import Orchestrator, MockLLMClient, AuditConfig  # noqa: E402
from aae.orchestrator import _deep_layers_warranted  # noqa: E402
from aae.schema import (Ledger, Finding, Accusation, Defense, DefectClass,  # noqa: E402
                        EvidenceBase, Posta)


def _res(posta, **cfg_kwargs):
    cfg = AuditConfig(artifact_path="x", max_posta=posta, **cfg_kwargs)
    return Orchestrator(MockLLMClient()).run("artefatto con numeri.", cfg, artifact_name="x")


def _finding(cls):
    return Finding(id="F", element="e", taxonomy_cell="mechanisms",
                   defect_class=cls, posta=Posta.MEDIUM,
                   accusation=Accusation(text="t", base=EvidenceBase.READING,
                                         evidence="ev", sections=["s"]),
                   defense=Defense(attempted=True), source_role="propagator", source_grade=1)


class DeepLayersAutoDeploy(unittest.TestCase):
    def test_high_posta_autodeploys_triadic_and_deep_causal(self):
        r = _res(Posta.HIGH)   # no enable_* flags set
        self.assertIsNotNone(r.triadic, "HIGH posta must auto-deploy triadic")
        # A1: the mock emits 2 findings that share the 'mechanisms' cell -> a candidate common root, so
        # deep-causal IS warranted here (structural trigger fires on shared structure, not bare posta).
        self.assertIsNotNone(r.deep_causal, "2 findings sharing a cell -> deep-causal warranted (A1)")

    def test_forced_deep_causal_is_recorded_ran_in_manifest(self):
        r = _res(Posta.HIGH, enable_deep_causal=True)   # explicit flag forces it
        layers = r.ledger.run_manifest["layers"]
        self.assertEqual(layers["deep_causal"]["status"], "ran",
                         "a deployed deep-causal must show RAN, not NOT_APPLICABLE")

    def test_low_posta_leaves_deep_layers_off(self):
        r = _res(Posta.LOW)    # the Freno: small artifact, no depth forced
        self.assertIsNone(r.triadic)
        self.assertIsNone(r.deep_causal)

    def test_policy_conceptual_novel_warrants_even_on_medium(self):
        cfg = AuditConfig(artifact_path="x", max_posta=Posta.MEDIUM)
        led = Ledger(artifact_name="x")
        led.add(_finding(DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL))
        self.assertTrue(_deep_layers_warranted(cfg, led.findings))
        # medium posta with no conceptual-novel signal -> not warranted
        self.assertFalse(_deep_layers_warranted(cfg, Ledger(artifact_name="x").findings))


if __name__ == "__main__":
    unittest.main()
