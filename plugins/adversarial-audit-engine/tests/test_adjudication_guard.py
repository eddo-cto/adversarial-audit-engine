"""
test_adjudication_guard.py — bias-resistant adjudication as executable invariants.

Pins the four immunities the 2026 LLM-as-judge literature says judges lack:
self-preference, position, length, and cross-nature closure. Each is a check the
run can fail, not a slogan.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aae.adjudication_guard import (  # noqa: E402
    is_self_adjudicating, blind_relabel, position_invariant, length_bias,
    assess_adjudication,
)


class SelfPreference(unittest.TestCase):
    def test_self_adjudication_is_detected(self):
        self.assertTrue(is_self_adjudicating("openai:gpt", ["anthropic:c", "openai:gpt"]))

    def test_separate_adjudicator_is_clean(self):
        self.assertFalse(is_self_adjudicating("anthropic:fresh",
                                              ["anthropic:c", "openai:gpt"]))


class Position(unittest.TestCase):
    def test_order_invariant_judge_passes(self):
        # decides YES for items whose value is even — independent of order
        def decide(order):
            return frozenset(x for x in order if x % 2 == 0)
        self.assertTrue(position_invariant(decide, [1, 2, 3, 4, 5, 6]))

    def test_position_biased_judge_is_caught(self):
        # a judge that says YES only to the first two items it sees = position bias
        def decide(order):
            return frozenset(order[:2])
        self.assertFalse(position_invariant(decide, [1, 2, 3, 4, 5, 6]))

    def test_blind_relabel_is_deterministic_and_hides_order(self):
        items = ["a", "b", "c", "d"]
        r1, k1 = blind_relabel(items, seed=7)
        r2, k2 = blind_relabel(items, seed=7)
        self.assertEqual(r1, r2)                      # deterministic
        self.assertEqual(set(k1.values()), set(items))  # nothing lost
        self.assertNotEqual([t for t, _ in r1], list(items))  # relabelled


class Length(unittest.TestCase):
    def test_length_correlated_judge_is_flagged(self):
        lengths = [10, 20, 30, 40, 50]
        yes = [0, 0, 1, 1, 1]           # YES tracks length
        r, flagged = length_bias(lengths, yes)
        self.assertTrue(flagged)
        self.assertGreater(r, 0.5)

    def test_length_orthogonal_judge_is_clean(self):
        lengths = [10, 20, 30, 40, 50, 60]
        yes = [1, 0, 1, 0, 1, 0]        # alternating, uncorrelated with length
        r, flagged = length_bias(lengths, yes)
        self.assertFalse(flagged)


class Report(unittest.TestCase):
    def test_clean_inter_nature_adjudication(self):
        rep = assess_adjudication(
            auditors=["anthropic:claude", "openai:gpt"],
            adjudicator="google:gemini",           # not an auditor, third vendor
            lengths=[10, 20, 30, 40], yes_flags=[1, 0, 1, 0],
        )
        self.assertTrue(rep.self_preference_blocked)
        self.assertFalse(rep.length_bias_flagged)
        self.assertEqual(rep.independence_scope, "inter-nature")
        self.assertTrue(rep.clean())

    def test_self_adjudication_makes_report_unclean(self):
        rep = assess_adjudication(
            auditors=["anthropic:claude", "openai:gpt"],
            adjudicator="openai:gpt",               # judges its own findings
        )
        self.assertFalse(rep.self_preference_blocked)
        self.assertFalse(rep.clean())
        self.assertTrue(any("SELF-PREFERENCE" in n for n in rep.notes))

    def test_position_bias_makes_report_unclean(self):
        def decide(order):
            return frozenset(order[:1])
        rep = assess_adjudication(
            auditors=["anthropic:a"], adjudicator="openai:b",
            decide=decide, items=[1, 2, 3, 4],
        )
        self.assertFalse(rep.position_immune)
        self.assertFalse(rep.clean())


if __name__ == "__main__":
    unittest.main()
