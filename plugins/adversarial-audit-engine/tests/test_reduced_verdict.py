"""test_reduced_verdict.py — REDUCED is a DERIVED, reachable verdict, not dead code.

History: `Verdict.REDUCED` ("accusa_ridimensionata") was once dead (no trigger) and was removed. It is
reintroduced as a *derived* verdict: a real defect (would be ARTIFACT_DEFECTIVE) whose `cost_to_fix` is
TRIVIAL is "real but minor". Because it is computed from `cost_to_fix` (one-way), it cannot drift from it.
These tests pin that it is now reachable, that the trigger is exactly `cost_to_fix == TRIVIAL`, and that
the verdict-keyed tables carry no orphan ranks.
"""
import itertools
import inspect
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae.schema import (Verdict, EvidenceBase, DefectClass, Finding, Accusation,  # noqa: E402
                        Defense, Posta, CostToFix)
from aae import dedup as DEDUP  # noqa: E402


def _real_defect(cost):
    """A finding that Rule 5 would condemn (solid base, defense attempted, no fact)."""
    return Finding(id="x", element="e", taxonomy_cell="outputs",
                   defect_class=DefectClass.NUMERIC, posta=Posta.HIGH,
                   accusation=Accusation(text="t", base=EvidenceBase.EXECUTION,
                                         evidence="1+1=3", sections=["s1"]),
                   defense=Defense(attempted=True, present=False, fact=None),
                   cost_to_fix=cost)


class ReducedVerdict(unittest.TestCase):
    def test_reduced_exists(self):
        self.assertTrue(hasattr(Verdict, "REDUCED"))
        self.assertEqual("accusa_ridimensionata", Verdict.REDUCED.value)

    def test_trivial_real_defect_is_reduced(self):
        self.assertEqual(Verdict.REDUCED, _real_defect(CostToFix.TRIVIAL).adjudicate())

    def test_costlier_real_defect_is_full_condemnation(self):
        for c in (CostToFix.LOW, CostToFix.MEDIUM, CostToFix.HIGH, None):
            self.assertEqual(Verdict.ARTIFACT_DEFECTIVE, _real_defect(c).adjudicate(),
                             f"cost_to_fix={c} should be a full win, not reduced")

    def test_no_orphan_rank_in_dedup(self):
        valid = {v.value for v in Verdict}
        rank = getattr(DEDUP, "severity_rank", None)
        if rank is None:
            self.assertIn("accusa_ridimensionata", inspect.getsource(DEDUP))
        else:
            self.assertTrue(set(rank) <= valid, f"orphan ranks: {set(rank) - valid}")
            self.assertIn("accusa_ridimensionata", rank)  # the reduced verdict is ranked

    def test_adjudicate_only_yields_enum_members(self):
        valid = set(Verdict)
        for base, dc, att, pres, fact, cost in itertools.product(
                EvidenceBase, DefectClass, (True, False), (True, False),
                (True, False), list(CostToFix) + [None]):
            f = Finding(id="x", element="e", taxonomy_cell="mechanisms", defect_class=dc,
                        posta=Posta.HIGH,
                        accusation=Accusation(text="t", base=base, evidence="e", sections=["s"]),
                        defense=Defense(attempted=att, present=pres, fact=("f" if fact else None)),
                        cost_to_fix=cost)
            self.assertIn(f.adjudicate(), valid)


if __name__ == "__main__":
    unittest.main()
