"""
test_negation_spectrometry.py — control of the falsifier's own Type-I error.

This module answers the question no other adversarial-audit tool asks: a
POWERFUL falsifier can demolish VALID artifacts too. The theorem it encodes is
that persistence across m independent auditors suppresses spurious negations
exponentially, P <= B(k; m, p). These tests check the maths, not the prose.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aae.negation_spectrometry import (admit, binom_tail, calibrate,  # noqa: E402
                                       empirical_type1)


class TheTheorem(unittest.TestCase):
    """B(k; m, p) = sum_{j>=k} C(m,j) p^j (1-p)^(m-j)."""

    def test_unanimity_gives_p_to_the_power_m(self):
        """k = m is the headline case: the bound collapses to p^m."""
        for p in (0.05, 0.1, 0.2, 0.5):
            for m in (2, 3, 5):
                with self.subTest(p=p, m=m):
                    self.assertAlmostEqual(p ** m, binom_tail(m, m, p), places=10)

    def test_k_equal_zero_is_certainty(self):
        self.assertAlmostEqual(1.0, binom_tail(0, 4, 0.3), places=10)

    def test_bound_decreases_as_we_demand_more_auditors(self):
        p, m = 0.2, 6
        bounds = [binom_tail(k, m, p) for k in range(1, m + 1)]
        self.assertEqual(bounds, sorted(bounds, reverse=True))

    def test_suppression_is_exponential_not_linear(self):
        """Going from 1 to 3 unanimous auditors must cut the bound by orders of
        magnitude, otherwise the whole cross-vendor argument is decoration."""
        p = 0.2
        self.assertLess(binom_tail(3, 3, p), binom_tail(1, 1, p) / 20)

    def test_bound_increases_with_a_worse_auditor(self):
        self.assertLess(binom_tail(2, 4, 0.05), binom_tail(2, 4, 0.30))

    def test_bound_is_a_probability(self):
        for k in range(0, 5):
            for p in (0.0, 0.1, 0.5, 1.0):
                b = binom_tail(k, 4, p)
                self.assertGreaterEqual(b, 0.0)
                self.assertLessEqual(b, 1.0)


class Calibration(unittest.TestCase):
    """FDR = P(demolishes | valid), TDR = P(demolishes | invalid)."""

    def test_a_perfect_discriminator(self):
        r = calibrate(scores_valid=[0.0, 0.1, 0.2], scores_invalid=[0.8, 0.9, 1.0])
        self.assertEqual(0.0, r["FDR"])
        self.assertEqual(1.0, r["TDR"])
        self.assertEqual(1.0, r["AUC"])

    def test_an_auditor_that_demolishes_everything_is_useless(self):
        """High power means nothing without discrimination: AUC exposes it."""
        r = calibrate(scores_valid=[0.9, 0.9], scores_invalid=[0.9, 0.9])
        self.assertEqual(1.0, r["TDR"], "it does demolish the invalid ones")
        self.assertEqual(1.0, r["FDR"], "but it demolishes the valid ones too")
        self.assertEqual(0.5, r["AUC"], "so it separates nothing — noise")

    def test_auc_is_half_for_identical_distributions(self):
        r = calibrate([0.3, 0.5, 0.7], [0.3, 0.5, 0.7])
        self.assertAlmostEqual(0.5, r["AUC"], places=10)

    def test_empty_input_does_not_crash(self):
        r = calibrate([], [])
        self.assertEqual(0.5, r["AUC"])


class Admission(unittest.TestCase):
    """A negation is admitted only if raised by >= k DISCRIMINATIVE auditors."""

    def test_unanimous_negation_is_admitted(self):
        out = admit({"N-1": [1, 1, 1]}, auditor_fdr=[0.05, 0.05, 0.05], k=3)
        self.assertEqual(["N-1"], [fid for fid, _ in out["admitted"]])
        self.assertEqual([], out["discounted"])

    def test_lone_negation_is_discounted_as_high_frequency(self):
        out = admit({"N-1": [1, 0, 0]}, auditor_fdr=[0.05, 0.05, 0.05], k=2)
        self.assertEqual([], out["admitted"])
        self.assertEqual(["N-1"], [fid for fid, _ in out["discounted"]])

    def test_non_discriminative_auditors_are_excluded_from_the_count(self):
        """An auditor that demolishes valid artifacts 90% of the time must not
        be allowed to lend support — otherwise k-of-m launders noise."""
        out = admit({"N-1": [1, 1, 0]}, auditor_fdr=[0.9, 0.05, 0.05], k=2)
        self.assertEqual(2, out["m_effective"],
                         "only the two discriminative auditors count")
        self.assertEqual([], out["admitted"],
                         "support from the 0.9-FDR auditor must not be laundered "
                         "into an admission")
        self.assertEqual([("N-1", 1)], out["discounted"],
                         "the raised-by count must exclude the noisy auditor")
        self.assertLessEqual(out["p_max"], 0.2,
                             "the reported bound must not be computed from an "
                             "auditor that was excluded")

    def test_reported_bound_uses_the_worst_admitted_auditor(self):
        out = admit({"N-1": [1, 1]}, auditor_fdr=[0.05, 0.15], k=2)
        self.assertAlmostEqual(0.15, out["p_max"], places=10)
        self.assertAlmostEqual(0.15 ** 2, out["type1_bound"], places=10)

    def test_the_bound_is_always_reported(self):
        out = admit({"N-1": [1]}, auditor_fdr=[0.1], k=1)
        for key in ("type1_bound", "k", "m_effective", "p_max"):
            self.assertIn(key, out)


class EmpiricalResidue(unittest.TestCase):
    def test_assumption_free_rate_is_computed_from_observed_demolitions(self):
        rate = empirical_type1([[1, 1], [0, 0], [1, 0], [0, 0]], k=2)
        self.assertGreaterEqual(rate, 0.0)
        self.assertLessEqual(rate, 1.0)


if __name__ == "__main__":
    unittest.main()
