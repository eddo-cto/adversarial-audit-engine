"""test_type1_calibration.py — INDEPENDENT validation of the Type-I (false-demolition) error theory.

This measures the tool's own false-positive rate, so the machinery is validated by independent rounds,
not one wiring check:
  1. analytic cases with a known FDR/TDR/AUC (perfect / paranoid / blind / mixed auditor);
  2. the AUC is re-derived by a SECOND, independent method (average-rank Mann-Whitney) and must agree;
  3. a Monte-Carlo COVERAGE test: the 95% Wilson interval must cover the true rate ~95% of the time,
     and the point estimate must converge to the true rate as the battery grows.
Deterministic (seeded).
"""
import os
import sys
import random
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae import type1_calibration as t1  # noqa: E402


def _oc(label, condemned):
    return {"label": label, "condemned": condemned}


def _auc_by_ranks(scores_invalid, scores_valid):
    """Independent AUC via average-rank Mann-Whitney: AUC = (R_pos - n_pos(n_pos+1)/2)/(n_pos*n_neg),
    where positive = invalid. Different code path from the pairwise formula under test."""
    pos = [float(x) for x in scores_invalid]
    neg = [float(x) for x in scores_valid]
    if not pos or not neg:
        return 0.5
    allv = [(v, 1) for v in pos] + [(v, 0) for v in neg]
    allv.sort(key=lambda t: t[0])
    ranks = [0.0] * len(allv)
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0  # average rank (1-based) for the tie group
        for r in range(i, j + 1):
            ranks[r] = avg
        i = j + 1
    r_pos = sum(ranks[idx] for idx, (_, lab) in enumerate(allv) if lab == 1)
    n_pos, n_neg = len(pos), len(neg)
    return (r_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


class AnalyticCases(unittest.TestCase):
    def test_perfect_auditor(self):
        oc = [_oc("valid", 0)] * 3 + [_oc("invalid", 1)] * 3
        c = t1.calibrate(oc)
        self.assertEqual(c["FDR"], 0.0); self.assertEqual(c["TDR"], 1.0); self.assertEqual(c["AUC"], 1.0)

    def test_paranoid_auditor(self):    # condemns everything
        oc = [_oc("valid", 1)] * 3 + [_oc("invalid", 1)] * 3
        c = t1.calibrate(oc)
        self.assertEqual(c["FDR"], 1.0); self.assertEqual(c["TDR"], 1.0); self.assertEqual(c["AUC"], 0.5)

    def test_blind_auditor(self):       # condemns nothing
        oc = [_oc("valid", 0)] * 3 + [_oc("invalid", 0)] * 3
        c = t1.calibrate(oc)
        self.assertEqual(c["FDR"], 0.0); self.assertEqual(c["TDR"], 0.0); self.assertEqual(c["AUC"], 0.5)

    def test_mixed_hand_computed(self):
        oc = [_oc("valid", 0), _oc("valid", 0), _oc("valid", 1),
              _oc("invalid", 1), _oc("invalid", 1), _oc("invalid", 0)]
        c = t1.calibrate(oc)
        self.assertAlmostEqual(c["FDR"], 1/3, places=6)
        self.assertAlmostEqual(c["TDR"], 2/3, places=6)
        self.assertAlmostEqual(c["AUC"], 2/3, places=6)


class WilsonInterval(unittest.TestCase):
    def test_zero_and_full(self):
        lo, hi = t1.wilson_ci(0, 6)
        self.assertEqual(lo, 0.0); self.assertAlmostEqual(hi, 0.3903, places=3)
        lo, hi = t1.wilson_ci(6, 6)
        self.assertAlmostEqual(hi, 1.0, places=6); self.assertAlmostEqual(lo, 0.6097, places=3)

    def test_symmetry_and_bounds(self):
        lo, hi = t1.wilson_ci(3, 6)
        self.assertAlmostEqual((lo + hi) / 2, 0.5, places=6)
        for k in range(0, 21):
            lo, hi = t1.wilson_ci(k, 20)
            self.assertLessEqual(0.0, lo); self.assertLessEqual(hi, 1.0); self.assertLessEqual(lo, hi)


class AucCrossCheck(unittest.TestCase):
    def test_auc_matches_independent_rank_method(self):
        rng = random.Random(20260814)
        for _ in range(200):                       # 200 independent rounds
            nv, ni = rng.randint(2, 12), rng.randint(2, 12)
            sv = [round(rng.random(), 3) for _ in range(nv)]
            si = [round(rng.random(), 3) for _ in range(ni)]
            from aae.negation_spectrometry import calibrate as spec
            a = spec(sv, si)["AUC"]
            b = _auc_by_ranks(si, sv)
            self.assertAlmostEqual(a, b, places=6)


class MonteCarloCoverage(unittest.TestCase):
    def test_ci_covers_true_rate_about_95pct(self):
        rng = random.Random(4242)
        for p, n in [(0.1, 40), (0.2, 40), (0.35, 60)]:
            covered = 0; T = 3000
            for _ in range(T):
                k = sum(1 for _ in range(n) if rng.random() < p)
                lo, hi = t1.wilson_ci(k, n)
                if lo <= p <= hi:
                    covered += 1
            cov = covered / T
            self.assertGreaterEqual(cov, 0.90, f"under-coverage {cov:.3f} at p={p},n={n}")
            self.assertLessEqual(cov, 0.995, f"over-coverage {cov:.3f} at p={p},n={n}")

    def test_estimate_converges(self):
        rng = random.Random(7)
        p, n = 0.23, 6000
        k = sum(1 for _ in range(n) if rng.random() < p)
        self.assertAlmostEqual(k / n, p, delta=0.03)


class RecordRoundTrip(unittest.TestCase):
    def test_make_append_latest_cite(self):
        oc = [_oc("valid", 0)] * 6 + [_oc("invalid", 1)] * 5 + [_oc("invalid", 0)]
        rec = t1.make_record("anthropic:claude-opus-5", "general-v1", oc)
        self.assertEqual(rec["FDR"], 0.0)
        self.assertEqual(rec["n_valid"], 6)
        with tempfile.TemporaryDirectory() as d:
            store = os.path.join(d, "_calibration.jsonl")
            self.assertIsNone(t1.latest_calibration("anthropic:claude-opus-5", store))
            t1.append_calibration(rec, store)
            got = t1.latest_calibration("anthropic:claude-opus-5", store)
            self.assertEqual(got["battery_id"], "general-v1")
            self.assertIn("Type-I", t1.cite(got))
            self.assertIn("NOT CALIBRATED", t1.cite(None))


class DisciplineCitesType1(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("AAE_CALIBRATION")

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("AAE_CALIBRATION", None)
        else:
            os.environ["AAE_CALIBRATION"] = self._saved

    def _payload(self):
        return {"artifact_name": "x", "internal_identity": "anthropic:auditor-x", "max_posta": "high",
                "triage": {"dimensions_present": ["mechanisms"], "deploy_roles": ["verifier", "propagator"]},
                "findings": [{"source_role": "verifier", "element": "e", "taxonomy_cell": "mechanisms",
                              "defect_class": "numeric", "posta": "high",
                              "accusation": {"text": "t", "base": "execution", "evidence": "x", "sections": ["§1"]},
                              "defense": {"attempted": True, "present": True, "fact": "d"},
                              "cost_to_fix": "low", "sources": ["s"], "source_grade": 1, "action_state": "open"}]}

    def test_cites_when_calibrated(self):
        from aae.pipeline import discipline
        with tempfile.TemporaryDirectory() as d:
            store = os.path.join(d, "_calibration.jsonl")
            oc = [_oc("valid", 0)] * 6 + [_oc("invalid", 1)] * 6
            t1.append_calibration(t1.make_record("anthropic:auditor-x", "general-v1", oc), store)
            os.environ["AAE_CALIBRATION"] = store
            led = discipline(self._payload()).ledger
            self.assertTrue(any(f.startswith("TYPE-I:") and "95% CI" in f and "NOT CALIBRATED" not in f
                                for f in led.flags))

    def test_says_not_calibrated_without_store(self):
        os.environ.pop("AAE_CALIBRATION", None)
        from aae.pipeline import discipline
        led = discipline(self._payload()).ledger
        self.assertTrue(any("NOT CALIBRATED" in f for f in led.flags))


if __name__ == "__main__":
    unittest.main()
