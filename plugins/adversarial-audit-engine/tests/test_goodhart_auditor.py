"""
test_goodhart_auditor.py — the BRIDGE from ablation toggles to the real engine (auditor_engine.py).

The LLM part (artefact -> findings) is injected as a deterministic mock role_runner, so the bridge's
own logic is pinned WITHOUT any model call:
  1. apply_ablation: axes OFF keeps only ONE role's findings; axes ON keeps them all;
  2. apply_ablation: eye ON -> different-vendor attested identity; cross_seed -> same-vendor; eye OFF -> None;
  3. EngineAuditor.audit derives CLEARED purely from engine verdicts (holds -> cleared; condemned -> caught);
  4. the bridge NEVER consults the gold (no gold argument anywhere in its surface).
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))                       # aae
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "goodhart"))

import auditor_engine as AE   # noqa: E402
import harness as H           # noqa: E402


def _payload(findings):
    return {
        "artifact_name": "smoke", "internal_identity": "anthropic:claude-x", "max_posta": "low",
        "excluded_cells": {c: "n/a" for c in
                           ("premises", "inputs", "mechanisms", "outputs", "boundary", "interface")},
        "findings": findings,
    }


def _holds_finding(role="verifier"):
    # defense present + fact -> ARTIFACT_HOLDS (not condemning) -> CLEARED
    return {"source_role": role, "element": "the value", "taxonomy_cell": "mechanisms",
            "defect_class": "numeric", "posta": "low",
            "accusation": {"text": "maybe wrong", "base": "execution", "evidence": "the value is 5"},
            "defense": {"attempted": True, "present": True, "fact": "5 is correct"},
            "attack": {"attempted": True, "vector": "recompute independently"}, "action": ""}


def _condemning_finding(role="verifier"):
    # defense attempted but NO decisive fact + solid base + non-trivial cost -> ARTIFACT_DEFECTIVE -> CAUGHT
    return {"source_role": role, "element": "the value", "taxonomy_cell": "mechanisms",
            "defect_class": "numeric", "posta": "low", "cost_to_fix": "substantial", "source_grade": 1,
            "accusation": {"text": "the sum is wrong", "base": "execution", "evidence": "2+2 stated as 5"},
            "defense": {"attempted": True, "present": False, "fact": ""},
            "attack": {"attempted": True, "vector": "recompute independently"},
            "action": "recompute the sum and correct it"}


class TestApplyAblation(unittest.TestCase):
    def test_axes_off_keeps_one_role(self):
        pl = _payload([_holds_finding("verifier"), _holds_finding("reasoner")])
        cell = H.AblationCell("x", eye=True, axes=False, governor=True)
        out, _ = AE.apply_ablation(pl, cell)
        roles = {f["source_role"] for f in out["findings"]}
        self.assertEqual(roles, {"verifier"})                 # single-axis

    def test_axes_on_keeps_all(self):
        pl = _payload([_holds_finding("verifier"), _holds_finding("reasoner")])
        cell = H.AblationCell("x", eye=True, axes=True, governor=True)
        out, _ = AE.apply_ablation(pl, cell)
        self.assertEqual(len(out["findings"]), 2)

    def test_eye_attestation_mapping(self):
        pl = _payload([_holds_finding()])
        _, att_cv = AE.apply_ablation(pl, H.AblationCell("x", eye=True, axes=True, governor=True))
        _, att_off = AE.apply_ablation(pl, H.AblationCell("x", eye=False, axes=True, governor=True))
        _, att_cs = AE.apply_ablation(
            pl, H.AblationCell("x", eye=True, axes=True, governor=True, eye_mode="cross_seed"))
        self.assertEqual(att_cv, AE.DIFFERENT_VENDOR_EYE)
        self.assertIsNone(att_off)
        self.assertEqual(att_cs, AE.SAME_VENDOR_SEED_EYE)


class TestEngineAuditorClearing(unittest.TestCase):
    def test_holds_is_cleared(self):
        auditor = AE.EngineAuditor(role_runner=lambda art, cell: _payload([_holds_finding()]))
        self.assertTrue(auditor.audit({"x": 1}, H.AblationCell("x", eye=True, axes=True, governor=True)))

    def test_condemned_is_caught(self):
        auditor = AE.EngineAuditor(role_runner=lambda art, cell: _payload([_condemning_finding()]))
        self.assertFalse(auditor.audit({"x": 1}, H.AblationCell("x", eye=True, axes=True, governor=True)))

    def test_bridge_never_sees_gold(self):
        # the role_runner signature is (artifact, cell) only — no gold channel exists in the bridge
        import inspect
        self.assertEqual(list(inspect.signature(AE.EngineAuditor.audit).parameters)[1:], ["artifact", "cell"])


if __name__ == "__main__":
    unittest.main()
