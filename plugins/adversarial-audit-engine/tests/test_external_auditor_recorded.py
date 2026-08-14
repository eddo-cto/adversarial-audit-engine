"""test_external_auditor_recorded.py — on the PRODUCT path (run_core.py), an attested eye is
recorded as external_auditor RAN, not left to the agent's payload.

The first real Claude Code /audit called a genuine cross-vendor eye that corroborated a defect, yet
the manifest read external_auditor NOT_APPLICABLE because that came from the agent-authored payload.
When AAE_EXTERNAL_ATTESTED_IDENTITY is set (the eye actually ran), run_core.py now records
external_auditor RAN deterministically — the record can no longer understate the independence.
"""
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(_HERE)
sys.path.insert(0, PLUGIN)
sys.path.insert(0, os.path.join(PLUGIN, "scripts"))

import run_core  # noqa: E402


def _finding(role, cell, cls, sections):
    return {"source_role": role, "element": f"{role} elem", "taxonomy_cell": cell,
            "defect_class": cls, "posta": "high",
            "accusation": {"text": "t", "base": "reading", "evidence": "ev", "sections": sections},
            "defense": {"attempted": True, "present": True, "fact": "defended"},
            "cost_to_fix": "low", "action": "", "declared_limit": "needs human",
            "sources": ["primary src"], "severity": "media", "source_grade": 1,
            "action_state": "open"}


def _payload():
    return {
        "artifact_name": "t.md",
        "internal_identity": "anthropic:claude-opus-5",
        "external_identity": None,
        "max_posta": "high",
        "source_primary_reachable": True,
        "triage": {"dimensions_present": ["mechanisms", "outputs"],
                   "deploy_roles": ["verifier", "propagator"]},
        # the agent UNDER-declares the eye — run_core must override when attested
        "execution": {"layers": {
            "external_auditor": {"status": "not_applicable", "justification": "agent said so"},
            "deep_causal": {"status": "not_applicable", "justification": "thin"}}},
        "findings": [
            _finding("verifier", "mechanisms", "numeric", ["§1"]),
            _finding("propagator", "outputs", "non_local_mechanical", ["§1", "§2"]),
        ],
    }


class ExternalAuditorRecorded(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("AAE_EXTERNAL_ATTESTED_IDENTITY")

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("AAE_EXTERNAL_ATTESTED_IDENTITY", None)
        else:
            os.environ["AAE_EXTERNAL_ATTESTED_IDENTITY"] = self._saved

    def test_attested_eye_marks_external_auditor_ran(self):
        os.environ["AAE_EXTERNAL_ATTESTED_IDENTITY"] = "ollama-local:llama3.1:8b"
        with tempfile.TemporaryDirectory() as d:
            res = run_core.run(_payload(), d)
        layers = res.ledger.run_manifest["layers"]
        self.assertEqual(layers["external_auditor"]["status"], "ran")  # overrode payload NA
        self.assertEqual(int(res.ledger.independence_level), 3)         # different vendor

    def test_no_attestation_leaves_payload_declaration(self):
        os.environ.pop("AAE_EXTERNAL_ATTESTED_IDENTITY", None)
        with tempfile.TemporaryDirectory() as d:
            res = run_core.run(_payload(), d)
        layers = res.ledger.run_manifest["layers"]
        self.assertNotEqual(layers["external_auditor"]["status"], "ran")


if __name__ == "__main__":
    unittest.main()
