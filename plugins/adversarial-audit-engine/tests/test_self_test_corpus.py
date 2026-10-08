"""
test_self_test_corpus.py — the G self-test corpus, seal, and release gate (1.12), deterministic.

Pins:
  1. generate() is deterministic and every defect span EXACTLY locates its verbatim (so match.py can find it);
  2. ~20% clean (no-defect) cases are produced;
  3. split is stratified by domain into dev/holdout;
  4. sealed_labels refuses an optimizer (env or flag) with LeakError;
  5. release_gate passes on stable G, fails on recall regression and on FP rise;
  6. end-to-end: a perfect run scores recall 1.0 / fp_rate 0; a degraded run fails the gate.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "self_test"))

import corpus_gen as C       # noqa: E402
import sealed_labels as S    # noqa: E402
import release_gate as RG    # noqa: E402
import match as M            # noqa: E402
import metrics_g as G        # noqa: E402


class TestCorpus(unittest.TestCase):
    def test_deterministic_and_exact_spans(self):
        a = C.generate(n=40); b = C.generate(n=40)
        self.assertEqual([c["id"] for c in a], [c["id"] for c in b])
        for c in a:
            for d in c["defects"]:
                s, e = d["span"]
                self.assertEqual(c["source_text"][s:e], d["verbatim"])   # exact by construction

    def test_has_clean_cases(self):
        cs = C.generate(n=40)
        n_clean = sum(1 for c in cs if c["label"] == "clean")
        self.assertGreater(n_clean, 0)
        self.assertLess(n_clean, len(cs))

    def test_split_stratified(self):
        cs = C.generate(n=40); sp = C.split(cs, holdout_frac=0.4)
        self.assertEqual(set(sp["dev"]) & set(sp["holdout"]), set())
        self.assertEqual(len(sp["dev"]) + len(sp["holdout"]), len(cs))


class TestSeal(unittest.TestCase):
    def test_normal_read_ok_optimizer_refused(self):
        cs = C.generate(n=20); sp = C.split(cs)
        labels = S.read_holdout_labels(cs, sp)
        self.assertTrue(set(labels).issubset(set(sp["holdout"])))
        with self.assertRaises(S.LeakError):
            S.read_holdout_labels(cs, sp, optimizer=True)

    def test_env_optimizer_refused(self):
        cs = C.generate(n=20); sp = C.split(cs)
        os.environ["AAE_SELFTEST_ROLE"] = "optimizer"
        try:
            with self.assertRaises(S.LeakError):
                S.read_holdout_defects(cs, sp)
        finally:
            del os.environ["AAE_SELFTEST_ROLE"]


class TestGate(unittest.TestCase):
    def test_stable_passes(self):
        base = {"recall_severity": 0.80, "fp_rate": 0.05}
        self.assertTrue(RG.evaluate(base, dict(base))["passed"])

    def test_recall_regression_fails(self):
        base = {"recall_severity": 0.80, "fp_rate": 0.05}
        new = {"recall_severity": 0.70, "fp_rate": 0.05}
        self.assertFalse(RG.evaluate(base, new)["passed"])

    def test_fp_rise_fails(self):
        base = {"recall_severity": 0.80, "fp_rate": 0.05}
        new = {"recall_severity": 0.80, "fp_rate": 0.20}
        self.assertFalse(RG.evaluate(base, new)["passed"])


class TestEndToEnd(unittest.TestCase):
    def _score(self, perfect: bool):
        cs = C.generate(n=30)
        results, flags = [], []
        for c in cs:
            findings = []
            if perfect:
                for d in c["defects"]:     # a perfect auditor condemns each defect with its verbatim
                    findings.append({"verdict": "accusa_vince", "defect_class": d["defect_class"],
                                     "accusation": {"evidence": d["verbatim"]}})
            # a degraded auditor finds nothing on defects AND wrongly condemns clean cases
            if not perfect and c["label"] == "clean":
                findings.append({"verdict": "accusa_vince", "defect_class": "numeric",
                                 "accusation": {"evidence": c["source_text"][:20]}})
            results.append(M.match_case(findings, c["defects"], c["source_text"]))
            flags.append(c["label"] == "clean")
        return G.aggregate(results, no_defect_flags=flags)

    def test_perfect_then_degraded(self):
        good = self._score(perfect=True)
        self.assertEqual(good["recall_severity"], 1.0)
        self.assertEqual(good["fp_rate"], 0.0)
        bad = self._score(perfect=False)
        gate = RG.evaluate(good, bad)
        self.assertFalse(gate["passed"])     # degraded run fails the release gate


if __name__ == "__main__":
    unittest.main()
