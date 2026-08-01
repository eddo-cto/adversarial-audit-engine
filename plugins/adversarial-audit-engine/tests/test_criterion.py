"""
test_criterion.py — the engine owns beta, not the model.

The design claim: the LLM supplies SENSITIVITY (a graded 0-100 suspicion) and
the engine owns the CRITERION (how much evidence it demands before acting).
That separation is only real if the thresholds live in code and cannot be
argued away by the score alone. These tests pin that.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aae.criterion import CriterionConfig, decide  # noqa: E402


class Bands(unittest.TestCase):
    def test_high_score_with_trusted_source_condemns(self):
        self.assertEqual("condemn", decide(95, source_trust="high").band)

    def test_mid_score_lands_in_the_abstention_band(self):
        self.assertEqual("needs_reading", decide(60, source_trust="high").band)

    def test_low_score_holds(self):
        self.assertEqual("holds", decide(10, source_trust="high").band)

    def test_score_is_clamped_to_range(self):
        self.assertEqual("condemn", decide(10_000, source_trust="high").band)
        self.assertEqual("holds", decide(-50, source_trust="high").band)

    def test_abstention_is_an_explicit_band_not_a_gap(self):
        """Abstention must be a first-class outcome, not the absence of one."""
        bands = {decide(s, source_trust="high").band for s in range(0, 101, 5)}
        self.assertIn("needs_reading", bands)
        self.assertEqual({"condemn", "needs_reading", "holds"}, bands)


class OcrTrustContract(unittest.TestCase):
    """An OCR-sourced score may NEVER reach condemn — the text itself may be
    misread, so the evidence base is unsound no matter how confident the model
    is. This is the contract that stops a scanner artefact becoming a verdict."""

    def test_ocr_source_can_never_condemn(self):
        for score in (80, 90, 95, 100):
            with self.subTest(score=score):
                self.assertNotEqual("condemn", decide(score, source_trust="ocr").band)

    def test_ocr_high_score_is_routed_to_reading(self):
        self.assertEqual("needs_reading", decide(99, source_trust="ocr").band)

    def test_any_untrusted_source_is_capped(self):
        for trust in ("ocr", "low", "scan", "unknown"):
            with self.subTest(trust=trust):
                self.assertNotEqual("condemn", decide(100, source_trust=trust).band)

    def test_the_reason_is_stated_not_silent(self):
        d = decide(95, source_trust="ocr")
        self.assertTrue(d.reason.strip(), "a capped decision must say why")


class StakesShiftTheCriterion(unittest.TestCase):
    """High stakes lower the abstention entry: more cases go to a human."""

    def test_high_stakes_abstains_earlier_than_low_stakes(self):
        score = 35.0
        high = decide(score, source_trust="high", posta="high").band
        low = decide(score, source_trust="high", posta="low").band
        self.assertEqual("needs_reading", high)
        self.assertEqual("holds", low)

    def test_stakes_never_turn_an_abstention_into_a_condemnation(self):
        for posta in ("low", "medium", "high"):
            with self.subTest(posta=posta):
                self.assertNotEqual("condemn",
                                    decide(70, source_trust="high", posta=posta).band)


class CriterionIsTunable(unittest.TestCase):
    def test_raising_the_bar_withdraws_a_condemnation(self):
        strict = CriterionConfig(condemn_at=99.0, abstain_at=40.0)
        self.assertEqual("condemn", decide(90, source_trust="high").band)
        self.assertNotEqual("condemn",
                            decide(90, source_trust="high", cfg=strict).band)

    def test_the_same_score_can_yield_different_actions(self):
        """Sensitivity fixed, criterion moved: the whole point of the module."""
        lenient = CriterionConfig(condemn_at=50.0, abstain_at=20.0)
        strict = CriterionConfig(condemn_at=95.0, abstain_at=90.0)
        self.assertNotEqual(decide(60, cfg=lenient).band, decide(60, cfg=strict).band)

    def test_decision_is_deterministic(self):
        a = decide(72, source_trust="high", posta="high")
        b = decide(72, source_trust="high", posta="high")
        self.assertEqual((a.band, a.score), (b.band, b.score))


if __name__ == "__main__":
    unittest.main()
