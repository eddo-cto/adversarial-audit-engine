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
        # round-18: reasoner dropped to optional after the 10-run consolidation
        self.assertEqual(
            ("triage", "oracle", "verifier", "propagator", "governor"),
            RM.REQUIRED_LAYERS)
        self.assertNotIn("reasoner", RM.REQUIRED_LAYERS)

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

    def test_run_core_refuses_an_incomplete_run(self):
        # round-18: a run that fails A+B is INVALID and CANNOT be closed —
        # completion is forced to INVALID_RUN (non-bypassable refusal).
        rc = self._load_run_core()
        payload = {"artifact_name": "t", "internal_identity": "anthropic:opus",
                   "execution": {"artifact_class": "finance"},
                   "findings": [self._finding("V-1", "verifier")]}
        with tempfile.TemporaryDirectory() as d:
            res = rc.run(payload, d)
            self.assertEqual("INVALID", res.ledger.run_manifest["run_validity"])
            self.assertEqual("INVALID_RUN", res.ledger.completion_state)
            self.assertTrue(any("INVALID_RUN" in fl for fl in res.ledger.flags))


class MeasuredScaffolding(unittest.TestCase):
    """Round-16: scaffolding measured from real outputs, triage optimizes optionals."""

    def test_oracle_measured_from_cited_sources(self):
        led = _ledger(["verifier"])
        led.findings[0].sources = ["https://issuer.example/report.pdf", "§4.2"]
        m = build_manifest(led, {"artifact_class": "paper"})
        self.assertEqual(LayerStatus.RAN, m.layers["oracle"].status)
        self.assertTrue(m.layers["oracle"].measured)
        self.assertEqual(2, m.layers["oracle"].findings)   # distinct sources

    def test_oracle_without_sources_is_not_measured(self):
        m = build_manifest(_ledger(["verifier"]), {"artifact_class": "paper"})
        self.assertFalse(m.layers["oracle"].measured)      # falls back / MISSING

    def test_triage_measured_and_deselects_optional_layer(self):
        led = _ledger(["verifier", "reasoner", "propagator"])
        m = build_manifest(led, {"artifact_class": "paper",
                                 "layers": {"oracle": {"status": "ran"},
                                            "governor": {"status": "ran"}}},
                           triage={"dimensions_present": ["premises", "outputs"],
                                   "deploy_roles": ["verifier", "reasoner", "propagator"]})
        self.assertEqual(LayerStatus.RAN, m.layers["triage"].status)
        self.assertTrue(m.layers["triage"].measured)
        # deep_causal + external_auditor not selected by triage -> data-driven N/A
        self.assertEqual(LayerStatus.NOT_APPLICABLE, m.layers["deep_causal"].status)
        self.assertTrue(m.layers["deep_causal"].measured)
        self.assertIn("triage", m.layers["deep_causal"].justification)
        self.assertEqual("VALID", m.run_validity)

    def test_declared_justification_wins_over_triage_deduction(self):
        # Round-17 regression: external_auditor is N/A for INDEPENDENCE (declared),
        # not "not selected by triage" — an explicit declaration must not be
        # overwritten by the auto-rule even when the layer is also unselected.
        led = _ledger(["verifier", "reasoner", "propagator"])
        m = build_manifest(led, {"layers": {
                "oracle": {"status": "ran"}, "governor": {"status": "ran"},
                "external_auditor": {"status": "not_applicable",
                                     "justification": "single-vendor (level 1)"}}},
            triage={"deploy_roles": ["verifier", "reasoner", "propagator"]})
        ea = m.layers["external_auditor"]
        self.assertEqual(LayerStatus.NOT_APPLICABLE, ea.status)
        self.assertIn("single-vendor", ea.justification)
        self.assertNotIn("triage", ea.justification)
        # a genuinely undeclared optional still gets the data-driven reason
        self.assertEqual("not selected by triage", m.layers["deep_causal"].justification)

    def test_triage_cannot_deselect_a_required_layer(self):
        # triage omits propagator (required); it neither runs nor is declared -> MISSING
        led = _ledger(["verifier", "reasoner"])
        m = build_manifest(led, {"layers": {"oracle": {"status": "ran"},
                                            "governor": {"status": "ran"}}},
                           triage={"deploy_roles": ["verifier", "reasoner"]})
        self.assertEqual(LayerStatus.MISSING, m.layers["propagator"].status)
        self.assertEqual("INVALID", m.run_validity)

    def test_run_core_measures_governor_from_meta(self):
        spec = importlib.util.spec_from_file_location(
            "run_core", os.path.join(_SCRIPTS, "run_core.py"))
        rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
        payload = {"artifact_name": "t", "internal_identity": "anthropic:opus",
                   "triage": {"dimensions_present": ["mechanisms"],
                              "deploy_roles": ["verifier", "reasoner", "propagator"]},
                   "findings": [
                       {"id": "V", "element": "e", "taxonomy_cell": "mechanisms",
                        "defect_class": "numeric", "posta": "high",
                        "accusation": {"text": "t", "base": "execution", "evidence": "e",
                                       "sections": ["a"]}, "defense": {"attempted": True},
                        "action": "fix", "source_role": r, "source_grade": 1,
                        "sources": ["https://x/doc.pdf"]}
                       for r in ("verifier", "reasoner", "propagator")]}
        with tempfile.TemporaryDirectory() as d:
            man = rc.run(payload, d).ledger.run_manifest
            self.assertTrue(man["layers"]["governor"]["measured"])   # from the meta verdict
            self.assertTrue(man["layers"]["oracle"]["measured"])     # from cited sources
            self.assertTrue(man["layers"]["triage"]["measured"])     # from the decision record
            self.assertEqual("VALID", man["run_validity"])


if __name__ == "__main__":
    unittest.main()
