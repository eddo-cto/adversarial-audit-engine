"""
test_closure_hardening.py — regression tests for the round-9 closure fixes, each
one turning an independent-audit finding on the engine itself into a passing test.

  F-SECTIONS : the schema's structural checks (>=2 sections for a non-local
               class) must fire on the DOCUMENTED entry point (scripts/run_core),
               not only via orchestrator.integrity_report.
  F-HOOK     : the Stop hook (scripts/governor_check) must ENFORCE non-closure by
               downgrading a persisted VALIDATED that lacks an out-of-band human
               attestation — not merely inform.
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_PLUGIN, "scripts")
sys.path.insert(0, _PLUGIN)  # aae importable


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_SCRIPTS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FSections(unittest.TestCase):
    """The >=2-sections rule is enforced on the run_core path."""

    def _payload_with_one_section_nonlocal(self):
        return {
            "artifact_name": "t",
            "internal_identity": "anthropic:opus",
            "findings": [{
                "element": "two sections disagree",
                "taxonomy_cell": "mechanisms",
                "defect_class": "non_local_mechanical",
                "posta": "low",
                "accusation": {"text": "incompatible values", "base": "execution",
                               "evidence": "recomputed", "sections": ["s1"]},
                "defense": {"attempted": True, "present": False, "fact": None},
                "action": "reconcile the two values",
                "declared_limit": "single-nature audit",
                "source_role": "verifier",
            }],
        }

    def test_run_core_surfaces_the_sections_integrity_problem(self):
        rc = _load("run_core")
        with tempfile.TemporaryDirectory() as d:
            result = rc.run(self._payload_with_one_section_nonlocal(), d)
            flags = result.ledger.flags
            self.assertTrue(
                any("INTEGRITY" in f and "section" in f.lower() for f in flags),
                f"expected an INTEGRITY flag about >=2 sections, got: {flags}")


class FHook(unittest.TestCase):
    """The Stop hook downgrades an unattested VALIDATED on disk."""

    def _write_ledger(self, d, completion_state):
        led = {"artifact_name": "t", "independence_level": 1, "flags": [],
               "completion_state": completion_state,
               "findings": [{"verdict": "artefatto_regge", "declared_limit": "x",
                             "action": ""}]}
        p = os.path.join(d, "t.ledger.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(led, fh)
        return p

    def _run_hook(self, out_dir, attest):
        gc = _load("governor_check")
        old_out = os.environ.get("AAE_OUT")
        old_att = os.environ.get("AAE_HUMAN_ATTESTATION")
        os.environ["AAE_OUT"] = out_dir
        if attest is None:
            os.environ.pop("AAE_HUMAN_ATTESTATION", None)
        else:
            os.environ["AAE_HUMAN_ATTESTATION"] = attest
        try:
            rc = gc.main()
        finally:
            os.environ.pop("AAE_OUT", None) if old_out is None else os.environ.__setitem__("AAE_OUT", old_out)
            if old_att is None:
                os.environ.pop("AAE_HUMAN_ATTESTATION", None)
            else:
                os.environ["AAE_HUMAN_ATTESTATION"] = old_att
        return rc

    def test_unattested_validated_is_downgraded(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._write_ledger(d, "VALIDATED")
            rc = self._run_hook(d, attest=None)
            self.assertEqual(0, rc)  # informs, does not crash
            after = json.load(open(p, encoding="utf-8"))
            self.assertEqual("EXTERNAL_REVIEW_PENDING", after["completion_state"])
            self.assertTrue(any("HOOK-DOWNGRADE" in f for f in after["flags"]))

    def test_attested_validated_is_left_alone(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._write_ledger(d, "VALIDATED")
            rc = self._run_hook(d, attest="dr-rossi-2026")
            self.assertEqual(0, rc)
            after = json.load(open(p, encoding="utf-8"))
            self.assertEqual("VALIDATED", after["completion_state"])


if __name__ == "__main__":
    unittest.main()
