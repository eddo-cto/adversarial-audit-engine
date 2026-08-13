"""test_run_core_schema.py — `run_core.py --schema` is the contract that stops the
orchestrator from reverse-engineering the core.

A real Claude Code /audit run wasted a turn importing `aae.schema` by hand and guessing a
non-existent class (`TaxonomyCell`). The fix is a single deterministic call that emits the exact
payload template + the LIVE enum vocabulary. These tests pin that the emitted vocabulary is drawn
from the real enums (so it can never drift), and that the finding template never invites a verdict
(verdicts are output-only, assigned by the code).
"""
import os
import sys
import json
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(_HERE)
sys.path.insert(0, PLUGIN)
sys.path.insert(0, os.path.join(PLUGIN, "scripts"))

import run_core  # noqa: E402
from aae.schema import (DefectClass, Posta, EvidenceBase, CostToFix,  # noqa: E402
                        ActionState)
from aae.triage import TAXONOMY  # noqa: E402


class SchemaContract(unittest.TestCase):
    def setUp(self):
        self.s = json.loads(run_core.emit_schema())

    def test_emits_valid_contract(self):
        for k in ("payload_template", "finding_template", "vocabularies", "rules"):
            self.assertIn(k, self.s)

    def test_vocabulary_is_the_live_enums(self):
        v = self.s["vocabularies"]
        self.assertEqual(v["defect_class"], [e.value for e in DefectClass])
        self.assertEqual(v["posta"], [e.value for e in Posta])
        self.assertEqual(v["evidence_base"], [e.value for e in EvidenceBase])
        self.assertEqual(v["cost_to_fix"], [e.value for e in CostToFix])
        self.assertEqual(v["action_state"], [e.value for e in ActionState])
        self.assertEqual(v["taxonomy_cell"], list(TAXONOMY))

    def test_finding_template_invites_no_verdict(self):
        # verdicts are OUTPUT-ONLY; the template must not tempt the agent to set one
        self.assertNotIn("verdict", self.s["finding_template"])


if __name__ == "__main__":
    unittest.main()
