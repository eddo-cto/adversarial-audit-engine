"""
test_independence_ledger.py — the independence ledger is an executable invariant.

The engine must be able to STATE, for any run, how independent it actually was —
never claiming more than the identities present earn, and never reaching
VALIDATED on machine grounds alone (the red line). This pins the four scopes and
the ceiling rule.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aae.independence_ledger import build_independence_ledger  # noqa: E402
from aae.schema import IndependenceLevel  # noqa: E402


class Scopes(unittest.TestCase):
    def test_single_nature_is_level_1_not_independent(self):
        L = build_independence_ledger(auditors=["anthropic:claude"])
        self.assertEqual(L.achieved_level, IndependenceLevel.SAME_INSTANCE_ROLES)
        self.assertEqual(L.scope, "single")
        self.assertEqual(L.ceiling, "EXTERNAL_REVIEW_PENDING")

    def test_same_vendor_different_model_is_intra_nature_level_2(self):
        L = build_independence_ledger(
            auditors=["anthropic:claude-opus", "anthropic:claude-haiku"])
        self.assertEqual(L.achieved_level, IndependenceLevel.DIFFERENT_MODEL_SAME_VENDOR)
        self.assertEqual(L.scope, "intra-nature")
        self.assertEqual(L.ceiling, "EXTERNAL_REVIEW_PENDING")

    def test_different_vendor_is_inter_nature_level_3(self):
        L = build_independence_ledger(
            auditors=["anthropic:claude", "openai:gpt"],
            adjudicator="anthropic:claude-fresh")
        self.assertEqual(L.achieved_level,
                         IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR)
        self.assertEqual(L.scope, "inter-nature")
        self.assertEqual(L.ceiling, "CROSS_MODEL_REVIEWED")
        self.assertEqual(L.natures, ("anthropic", "openai"))

    def test_human_closes_to_level_4_and_only_then_validated(self):
        L = build_independence_ledger(
            auditors=["anthropic:claude", "openai:gpt"],
            external="human:domain-expert")
        self.assertEqual(L.achieved_level, IndependenceLevel.HUMAN_DOMAIN_EXPERT)
        self.assertEqual(L.scope, "human-closed")
        self.assertEqual(L.ceiling, "VALIDATED")


class RedLine(unittest.TestCase):
    def test_no_machine_only_run_reaches_validated(self):
        # every machine-only combination must cap below VALIDATED
        for auditors, adj, ext in [
            (["anthropic:claude"], None, None),
            (["anthropic:a", "anthropic:b"], "anthropic:c", None),
            (["anthropic:a", "openai:b"], "google:c", "openai:d"),
        ]:
            L = build_independence_ledger(auditors=auditors, adjudicator=adj, external=ext)
            self.assertNotEqual(L.ceiling, "VALIDATED",
                                f"machine-only run wrongly reached VALIDATED: {L.to_dict()}")

    def test_caveat_names_rho_when_not_inter_nature(self):
        L = build_independence_ledger(auditors=["anthropic:a", "anthropic:b"])
        self.assertIn("ρ", L.caveat)


class Shape(unittest.TestCase):
    def test_to_dict_and_render_are_consistent(self):
        L = build_independence_ledger(auditors=["anthropic:claude", "openai:gpt"])
        d = L.to_dict()
        self.assertEqual(d["achieved_level"], int(L.achieved_level))
        self.assertEqual(d["scope"], "inter-nature")
        self.assertIn("INDEPENDENCE LEDGER", L.render())
        self.assertIn("openai", L.render())

    def test_natures_deduplicated_and_sorted(self):
        L = build_independence_ledger(
            auditors=["openai:gpt-a", "anthropic:x", "openai:gpt-b"])
        self.assertEqual(L.natures, ("anthropic", "openai"))


if __name__ == "__main__":
    unittest.main()
