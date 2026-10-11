"""1.15 — qualify deceptive metrics.

Two signals that stop a reassuring number from being read as quality:
 (1) LEVEL-3 NOMINAL: a different-vendor eye lifts independence to 3, but if it corroborated
     nothing grounded the ledger says so (eye_corroboration='none' + flag). Conservative default.
 (2) cite() NULL-DETECTOR: a 0% false-positive rate with 0 power / AUC~0.5 is flagged, not sold
     as quality (the qwen2.5:7b local calibration).
"""
import unittest

from aae.pipeline import discipline
from aae import type1_calibration as t1


def _payload(findings=None, **over):
    p = {"artifact_name": "t", "findings": findings or [{
        "id": "F1", "element": "e", "taxonomy_cell": "outputs", "defect_class": "numeric",
        "posta": "low", "accusation": {"text": "t", "base": "execution", "evidence": "e",
                                       "sections": ["§1"]},
        "defense": {"attempted": True, "present": True, "fact": "f"},
        "attack": {"attempted": True, "vector": "v"}}]}
    p.update(over)
    return p


class TestEyeCorroboration(unittest.TestCase):

    def test_eye_called_but_nothing_corroborated_is_nominal(self):
        r = discipline(_payload(), attested_identity="meta:llama3.1:8b")
        self.assertEqual(r.ledger.eye_corroboration, "none")
        self.assertTrue(any("LEVEL-3 NOMINAL" in f for f in r.ledger.flags))

    def test_eye_corroboration_via_declared_count(self):
        r = discipline(_payload(eye_corroborations=2), attested_identity="meta:llama3.1:8b")
        self.assertEqual(r.ledger.eye_corroboration, "corroborated")
        self.assertFalse(any("LEVEL-3 NOMINAL" in f for f in r.ledger.flags))

    def test_eye_corroboration_via_source_role_in_findings(self):
        f = [{"id": "E1", "element": "e", "taxonomy_cell": "outputs", "defect_class": "numeric",
              "posta": "low", "source_role": "external-auditor",
              "accusation": {"text": "t", "base": "execution", "evidence": "e", "sections": ["§1"]},
              "defense": {"attempted": True, "present": True, "fact": "f"},
              "attack": {"attempted": True, "vector": "v"}}]
        r = discipline(_payload(findings=f), attested_identity="meta:llama3.1:8b")
        self.assertEqual(r.ledger.eye_corroboration, "corroborated")

    def test_no_eye_called_leaves_field_empty_and_no_flag(self):
        r = discipline(_payload())   # no attested_identity
        self.assertEqual(r.ledger.eye_corroboration, "")
        self.assertFalse(any("LEVEL-3 NOMINAL" in f for f in r.ledger.flags))

    def test_eye_corroboration_serializes(self):
        r = discipline(_payload(), attested_identity="meta:llama3.1:8b")
        import json
        self.assertEqual(json.loads(r.ledger.to_json())["eye_corroboration"], "none")


class TestCiteNullDetector(unittest.TestCase):

    def _rec(self, fdr, tdr, auc, n_valid=24, n_invalid=12):
        return {"FDR": fdr, "FDR_ci95": [0.0, 0.14], "TDR": tdr, "AUC": auc,
                "n_valid": n_valid, "n_invalid": n_invalid, "battery_id": "general-v2",
                "date": "2026-10-11"}

    def test_null_detector_is_flagged(self):
        s = t1.cite(self._rec(fdr=0.0, tdr=0.0, auc=0.5))
        self.assertIn("NULL DETECTOR", s)

    def test_real_discriminator_not_flagged(self):
        s = t1.cite(self._rec(fdr=0.04, tdr=0.83, auc=0.9))
        self.assertNotIn("NULL DETECTOR", s)
        self.assertIn("Type-I", s)

    def test_not_calibrated_unchanged(self):
        self.assertIn("NOT CALIBRATED", t1.cite(None))


if __name__ == "__main__":
    unittest.main()
