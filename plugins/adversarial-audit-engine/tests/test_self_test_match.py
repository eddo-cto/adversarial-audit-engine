"""
test_self_test_match.py — the G self-test matcher + metric (1.12 product release gate), deterministic.

Pins:
  1. a CONDEMNING finding whose verbatim quote overlaps a defect (compatible class) -> TP;
  2. a HELD finding on a defect location -> MISS (FN), not a match;
  3. a condemning finding matching no defect -> FP;
  4. class-incompatible finding -> no match;
  5. duplicate condemning findings on one defect -> counted once;
  6. aggregate(): recall / severity-recall / precision / fp_rate on a no-defect case.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "self_test"))

import match as M        # noqa: E402
import metrics_g as G    # noqa: E402

SRC = "Report: the total is 45 kg, but 12+17+26 equals 55. Revenue rose 80 to 100, a 25% increase."
#            ^ defect: "the total is 45 kg" is numerically wrong
DEF_START = SRC.index("the total is 45 kg")
DEFECTS = [{"defect_id": "d1", "defect_class": "numeric",
            "span": [DEF_START, DEF_START + len("the total is 45 kg")], "severity": 3}]


def _cond(ev, cls="numeric"):
    return {"verdict": "accusa_vince", "defect_class": cls, "accusation": {"evidence": ev}}


def _held(ev, cls="numeric"):
    return {"verdict": "artefatto_regge", "defect_class": cls, "accusation": {"evidence": ev}}


class TestMatch(unittest.TestCase):
    def test_true_positive(self):
        r = M.match_case([_cond("the total is 45 kg")], DEFECTS, SRC)
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (1, 0, 0))
        self.assertEqual(r["sev_hit"], 3)

    def test_held_finding_is_a_miss(self):
        r = M.match_case([_held("the total is 45 kg")], DEFECTS, SRC)
        self.assertEqual((r["tp"], r["fn"]), (0, 1))     # engine saw it but did not condemn -> miss

    def test_false_positive(self):
        r = M.match_case([_cond("a 25% increase")], DEFECTS, SRC)   # true statement, wrongly condemned
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (0, 1, 1))

    def test_class_incompatible_no_match(self):
        r = M.match_case([_cond("the total is 45 kg", cls="credential")], DEFECTS, SRC)
        self.assertEqual((r["tp"], r["fp"]), (0, 1))     # right place, wrong class -> not a match -> FP

    def test_duplicates_counted_once(self):
        r = M.match_case([_cond("the total is 45 kg"), _cond("the total is 45 kg")], DEFECTS, SRC)
        self.assertEqual(r["tp"], 1)                     # one defect credited once
        self.assertEqual(r["n_condemning"], 2)


class TestAggregate(unittest.TestCase):
    def test_corpus_metrics(self):
        with_defect = M.match_case([_cond("the total is 45 kg")], DEFECTS, SRC)   # TP
        no_defect = M.match_case([_cond("a 25% increase")], [], SRC)              # FP on a no-defect case
        g = G.aggregate([with_defect, no_defect], no_defect_flags=[False, True])
        self.assertEqual(g["recall"], 1.0)
        self.assertEqual(g["recall_severity"], 1.0)
        self.assertEqual(g["fp_rate"], 1.0)              # the one no-defect case produced a condemnation
        self.assertEqual(g["n_no_defect"], 1)


if __name__ == "__main__":
    unittest.main()
