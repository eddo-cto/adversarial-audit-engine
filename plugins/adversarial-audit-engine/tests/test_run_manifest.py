"""
test_run_manifest.py — round-13 execution manifest (standardization step 2).
Measures which layers ran (record-only); the A+B gate stays dormant until
REQUIRED_LAYERS is populated from measurement.
"""
import importlib.util
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_PLUGIN, "scripts")
sys.path.insert(0, _PLUGIN)

from aae.schema import (Ledger, Finding, Accusation, Defense, DefectClass,  # noqa: E402
                        EvidenceBase, Posta)
from aae import run_manifest as RM  # noqa: E402
from aae.run_manifest import build_manifest, LayerStatus  # noqa: E402


def _f(role, fid="F"):
    return Finding(id=fid, element="e", taxonomy_cell="mechanisms",
                   defect_class=DefectClass.NUMERIC, posta=Posta.HIGH,
                   accusation=Accusation(text="t", base=EvidenceBase.EXECUTION,
                                         evidence="ev", sections=["s1"]),
                   defense=Defense(attempted=True), source_role=role)


def _ledger(roles):
    L = Ledger(artifact_name="x")
    for i, r in enumerate(roles):
        L.add(_f(r, f"F{i}"))
    return L


class Manifest(unittest.TestCase):
    def test_emitting_layers_measured_from_data(self):
        m = build_manifest(_ledger(["verifier", "verifier", "propagator"]),
                           {"artifact_class": "finance"})
        self.assertEqual(LayerStatus.RAN, m.layers["verifier"].status)
        self.assertTrue(m.layers["verifier"].measured)   # from data, not self-report
        self.assertEqual(2, m.layers["verifier"].findings)
        self.assertEqual(1, m.layers["propagator"].findings)
        self.assertEqual("finance", m.artifact_class)
        # required scaffolding (triage/oracle/reasoner/governor) neither emitted
        # nor declared here -> A+B judgment is live -> INVALID
        self.assertEqual("INVALID", m.run_validity)

    def test_non_emitting_layers_take_declared_status(self):
        m = build_manifest(_ledger(["verifier"]), {"layers": {
            "oracle": {"status": "ran"},
            "external_auditor": {"status": "not_applicable",
                                 "justification": "single-vendor run"}}})
        self.assertEqual(LayerStatus.RAN, m.layers["oracle"].status)
        self.assertFalse(m.layers["oracle"].measured)    # self-reported, flagged as such
        self.assertEqual(LayerStatus.NOT_APPLICABLE, m.layers["external_auditor"].status)
        self.assertEqual(LayerStatus.MISSING, m.layers["governor"].status)

    def test_specialists_are_recorded_not_lost(self):
        m = build_manifest(_ledger(["verifier", "epistemologo"]), None)
        self.assertEqual(1, m.specialists.get("epistemologo"))

    def test_required_is_populated_from_measurement(self):
        self.assertEqual(
            ("triage", "oracle", "verifier", "reasoner", "propagator", "governor"),
            RM.REQUIRED_LAYERS)

    def test_fully_adjudicated_run_is_valid(self):
        layers = {"triage": {"status": "ran"}, "oracle": {"status": "ran"},
                  "governor": {"status": "ran"},
                  "deep_causal": {"status": "not_applicable", "justification": "thin artifact"},
                  "external_auditor": {"status": "not_applicable", "justification": "single-vendor"}}
        m = build_manifest(_ledger(["verifier", "reasoner", "propagator"]), {"layers": layers})
        self.assertEqual("VALID", m.run_validity)

    def test_missing_required_layer_is_invalid(self):
        # propagator is required; here it neither emits nor is declared -> MISSING
        layers = {"triage": {"status": "ran"}, "oracle": {"status": "ran"},
                  "governor": {"status": "ran"},
                  "deep_causal": {"status": "not_applicable", "justification": "x"},
                  "external_auditor": {"status": "not_applicable", "justification": "x"}}
        m = build_manifest(_ledger(["verifier", "reasoner"]), {"layers": layers})
        self.assertEqual("INVALID", m.run_validity)
        self.assertTrue(any("propagator" in g for g in m.gaps))

    def test_AB_gate_fires_once_required_is_populated(self):
        old = RM.REQUIRED_LAYERS
        try:
            RM.REQUIRED_LAYERS = ("verifier", "oracle")
            # condition A fails: oracle neither ran nor declared -> MISSING -> INVALID
            self.assertEqual("INVALID", build_manifest(_ledger(["verifier"]), None).run_validity)
            # everything adjudicated: verifier RAN (data), oracle RAN (declared),
            # the rest NOT_APPLICABLE -> VALID
            layers = {n: {"status": "not_applicable", "justification": "n/a"}
                      for n in RM.DECLARED_LAYERS if n != "verifier"}
            layers["oracle"] = {"status": "ran"}
            self.assertEqual("VALID",
                             build_manifest(_ledger(["verifier"]), {"layers": layers}).run_validity)
        finally:
            RM.REQUIRED_LAYERS = old


class RunCoreEmitsManifest(unittest.TestCase):
    def _load_run_core(self):
        spec = importlib.util.spec_from_file_location(
            "run_core", os.path.join(_SCRIPTS, "run_core.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _finding(self, fid, role):
        return {"id": fid, "element": "e", "taxonomy_cell": "mechanisms",
                "defect_class": "numeric", "posta": "high",
                "accusation": {"text": "t", "base": "execution", "evidence": "ev",
                               "sections": ["s1"]},
                "defense": {"attempted": True}, "action": "fix",
                "declared_limit": "x", "source_role": role, "source_grade": 1}

    def test_run_core_emits_live_validity_valid(self):
        rc = self._load_run_core()
        payload = {"artifact_name": "t", "internal_identity": "anthropic:opus",
                   "execution": {"artifact_class": "finance", "layers": {
                       "triage": {"status": "ran"}, "oracle": {"status": "ran"},
                       "governor": {"status": "ran"}, "reasoner": {"status": "ran"},
                       "deep_causal": {"status": "not_applicable", "justification": "thin"},
                       "external_auditor": {"status": "not_applicable", "justification": "single-vendor"}}},
                   "findings": [self._finding("V-1", "verifier"),
                                self._finding("P-1", "propagator")]}
        with tempfile.TemporaryDirectory() as d:
            man = rc.run(payload, d).ledger.run_manifest
            self.assertEqual("finance", man["artifact_class"])
            self.assertTrue(man["layers"]["verifier"]["measured"])
            self.assertEqual("VALID", man["run_validity"])

    def test_run_core_flags_an_incomplete_run(self):
        rc = self._load_run_core()
        payload = {"artifact_name": "t", "internal_identity": "anthropic:opus",
                   "execution": {"artifact_class": "finance"},
                   "findings": [self._finding("V-1", "verifier")]}
        with tempfile.TemporaryDirectory() as d:
            man = rc.run(payload, d).ledger.run_manifest
            self.assertEqual("INVALID", man["run_validity"])   # required scaffolding missing


if __name__ == "__main__":
    unittest.main()
