"""test_no_dead_verdict.py — pins the removal of the unreachable `REDUCED` verdict.

A third-party audit (on a stale 0.6.0 bundle) found, and re-derivation on 0.14.0 confirmed,
that `Verdict.REDUCED` ("accusa_ridimensionata", "real but minor") was never producible by the
adjudication state machine: PATTERN is caught by Rule 1 and the three remaining evidence bases by
Rule 5, leaving the REDUCED fall-through with no entry. It was removed; severity of a real-but-minor
defect lives in `cost_to_fix`, not in a distinct verdict. These tests keep it removed and keep the
verdict-keyed tables free of orphan entries.
"""
import itertools
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae.schema import (Verdict, EvidenceBase, DefectClass, Finding, Accusation,  # noqa: E402
                        Defense, Posta)
from aae import dedup as DEDUP  # noqa: E402


class NoDeadVerdict(unittest.TestCase):
    def test_reduced_is_gone(self):
        self.assertFalse(hasattr(Verdict, "REDUCED"))
        self.assertNotIn("accusa_ridimensionata", {v.value for v in Verdict})

    def test_verdict_membership_is_exactly_the_reachable_set(self):
        self.assertEqual(
            {"accusa_vince", "artefatto_regge", "da_leggere", "conteso", "pending"},
            {v.value for v in Verdict})

    def test_no_orphan_rank_in_dedup(self):
        # every severity_rank key must be a real Verdict value (no rank for a verdict
        # the machine cannot emit)
        valid = {v.value for v in Verdict}
        # reach the table without depending on a private name: build a tiny group and dedup
        rank_keys = set(DEDUP.severity_rank.keys()) if hasattr(DEDUP, "severity_rank") else None
        if rank_keys is None:  # table is local to the function; assert via source
            import inspect
            src = inspect.getsource(DEDUP)
            self.assertNotIn("accusa_ridimensionata", src)
        else:
            self.assertTrue(rank_keys <= valid, f"orphan ranks: {rank_keys - valid}")

    def test_adjudicate_never_yields_a_value_outside_the_enum(self):
        # exhaustively walk base × defect_class × defense state; every verdict must be a
        # current Verdict member (and, in particular, never the removed one)
        valid = set(Verdict)
        for base, dc, attempted, present, fact in itertools.product(
                EvidenceBase, DefectClass, (True, False), (True, False), (True, False)):
            f = Finding(id="x", element="e", taxonomy_cell="mechanisms", defect_class=dc,
                        posta=Posta.HIGH,
                        accusation=Accusation(text="t", base=base, evidence="ev", sections=["s"]),
                        defense=Defense(attempted=attempted, present=present,
                                        fact=("f" if fact else None)))
            v = f.adjudicate()
            self.assertIn(v, valid)


if __name__ == "__main__":
    unittest.main()
