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

from aae.attestation import content_digest, make_human_token  # noqa: E402


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

    def _write_ledger(self, d, completion_state, independence_level=1):
        led = {"artifact_name": "t", "independence_level": independence_level, "flags": [],
               "completion_state": completion_state,
               "findings": [{"verdict": "artefatto_regge", "declared_limit": "x",
                             "action": ""}]}
        p = os.path.join(d, "t.ledger.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(led, fh)
        return p

    def _valid_token(self, key):
        # the HMAC an honest operator would compute for the ledger _write_ledger makes
        digest = content_digest("t", [{"verdict": "artefatto_regge"}])
        return make_human_token(digest, key)

    def _run_hook(self, out_dir, token=None, key=None):
        gc = _load("governor_check")
        saved = {k: os.environ.get(k) for k in
                 ("AAE_OUT", "AAE_HUMAN_ATTESTATION", "AAE_HUMAN_KEY")}
        os.environ["AAE_OUT"] = out_dir
        for var, val in (("AAE_HUMAN_ATTESTATION", token), ("AAE_HUMAN_KEY", key)):
            os.environ.pop(var, None) if val is None else os.environ.__setitem__(var, val)
        try:
            rc = gc.main()
        finally:
            for var, val in saved.items():
                os.environ.pop(var, None) if val is None else os.environ.__setitem__(var, val)
        return rc

    def test_no_attestation_validated_is_downgraded(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._write_ledger(d, "VALIDATED")
            rc = self._run_hook(d, token=None, key=None)
            self.assertEqual(0, rc)  # informs, does not crash
            after = json.load(open(p, encoding="utf-8"))
            self.assertEqual("EXTERNAL_REVIEW_PENDING", after["completion_state"])
            self.assertTrue(any("HOOK-DOWNGRADE" in f for f in after["flags"]))

    def test_plain_token_no_longer_counts(self):
        # Round-11 (C2): a non-empty but non-HMAC token must NOT preserve VALIDATED.
        with tempfile.TemporaryDirectory() as d:
            p = self._write_ledger(d, "VALIDATED")
            rc = self._run_hook(d, token="dr-rossi-2026", key="operator-secret")
            self.assertEqual(0, rc)
            after = json.load(open(p, encoding="utf-8"))
            self.assertEqual("EXTERNAL_REVIEW_PENDING", after["completion_state"])

    def test_downgrade_also_resets_independence_level(self):
        # Round-10 B1: a downgraded ledger must not keep independence_level 4
        # (HUMAN_DOMAIN_EXPERT), or it still presents as human-closed downstream.
        with tempfile.TemporaryDirectory() as d:
            p = self._write_ledger(d, "VALIDATED", independence_level=4)
            rc = self._run_hook(d, token=None, key=None)
            self.assertEqual(0, rc)
            after = json.load(open(p, encoding="utf-8"))
            self.assertEqual("EXTERNAL_REVIEW_PENDING", after["completion_state"])
            self.assertLess(int(after["independence_level"]), 4)

    def test_verified_hmac_validated_is_left_alone(self):
        # Round-11: a VALIDATED backed by a valid HMAC under the operator key stays.
        with tempfile.TemporaryDirectory() as d:
            key = "operator-secret"
            p = self._write_ledger(d, "VALIDATED")
            rc = self._run_hook(d, token=self._valid_token(key), key=key)
            self.assertEqual(0, rc)
            after = json.load(open(p, encoding="utf-8"))
            self.assertEqual("VALIDATED", after["completion_state"])


if __name__ == "__main__":
    unittest.main()
