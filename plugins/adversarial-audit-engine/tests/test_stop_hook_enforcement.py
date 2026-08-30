"""
test_stop_hook_enforcement.py — the deterministic core is NON-BYPASSABLE (round 20).

A real claude-plus-local run derailed: an unexpected error on the independent eye
threw, and the hive ended with a prose summary WITHOUT invoking run_core.py. No
ledger was produced, yet nothing failed — the trust protocol was silently bypassed
(verdicts would come from the model, not the code). These tests pin the engineered
fix: fetching the schema drops an `.audit_pending` marker that ONLY a completed core
run clears; the Stop hook rejects (exit 2) a session that started an audit but
produced no ledger.
"""
import json
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(_HERE, ".."))

import run_core          # noqa: E402
import governor_check    # noqa: E402

MARKER = ".audit_pending"


def _valid_payload():
    return {
        "artifact_name": "smoke",
        "source_text": "The declared value is 5 units.",
        "max_posta": "low",
        "triage": {"dimensions_present": ["inputs"], "deploy_roles": ["verifier"]},
        "findings": [{
            "source_role": "verifier", "element": "the declared value",
            "taxonomy_cell": "inputs", "defect_class": "numeric", "posta": "low",
            "accusation": {"text": "unverified", "base": "reading",
                           "evidence": "The declared value is 5 units.", "sections": []},
            "defense": {"attempted": True, "present": False, "fact": None},
            "action": "verify at source", "source_grade": 1, "action_state": "open",
        }],
    }


class TestNonBypassableCore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.out = os.path.join(self.tmp, "aae_out")
        self._prev = os.environ.get("AAE_OUT")
        os.environ["AAE_OUT"] = self.out

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("AAE_OUT", None)
        else:
            os.environ["AAE_OUT"] = self._prev

    def _marker(self):
        return os.path.join(self.out, MARKER)

    def test_schema_drops_marker(self):
        run_core.main(["--schema"])
        self.assertTrue(os.path.exists(self._marker()),
                        "fetching the schema must drop the .audit_pending marker")

    def test_core_run_clears_marker(self):
        run_core.main(["--schema"])
        fp = os.path.join(self.tmp, "findings.json")
        json.dump(_valid_payload(), open(fp, "w", encoding="utf-8"))
        run_core.main([fp])
        self.assertFalse(os.path.exists(self._marker()),
                         "a completed core run must clear the marker")
        self.assertTrue([f for f in os.listdir(self.out) if f.endswith(".ledger.json")],
                        "the core must have written a ledger")

    def test_stop_hook_rejects_derailed_audit(self):
        # audit started (marker) but core NEVER ran (no ledger) -> derailed
        run_core.main(["--schema"])
        self.assertEqual(governor_check.main(), 2,
                         "Stop hook must reject (exit 2) an audit with a marker and no ledger")

    def test_stop_hook_passes_completed_audit(self):
        run_core.main(["--schema"])
        fp = os.path.join(self.tmp, "findings.json")
        json.dump(_valid_payload(), open(fp, "w", encoding="utf-8"))
        run_core.main([fp])
        self.assertEqual(governor_check.main(), 0,
                         "a completed audit (ledger present) must pass the Stop hook")

    def test_stop_hook_ignores_non_audit_session(self):
        # no marker, no ledger -> not an audit, must not fail
        os.makedirs(self.out, exist_ok=True)
        self.assertEqual(governor_check.main(), 0,
                         "a non-audit session (no marker, no ledger) must pass quietly")

    def test_ledger_present_clears_stale_marker(self):
        run_core.main(["--schema"])
        fp = os.path.join(self.tmp, "findings.json")
        json.dump(_valid_payload(), open(fp, "w", encoding="utf-8"))
        run_core.main([fp])
        # re-plant a stale marker; a ledger exists, so the hook should clear it and pass
        open(self._marker(), "w").write("{}")
        self.assertEqual(governor_check.main(), 0)
        self.assertFalse(os.path.exists(self._marker()), "stale marker must be cleared")


if __name__ == "__main__":
    unittest.main()
