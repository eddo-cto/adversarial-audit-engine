"""
test_grounding.py — the deterministic anti-hallucination gate.

The README makes two distinct promises. This file separates them, because the
value of the module is precisely that it does not conflate them:

  GUARANTEED  : existence. A fabricated or altered quote can never condemn.
  NOT GUARANTEED : meaning. Quote-mining a real substring out of a negated
                   clause is caught best-effort by a sentence-scope check that
                   deliberately over-flags toward the human.

A test suite that asserted the second as strongly as the first would be making
the exact overclaim the engine exists to prevent.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aae import grounding as G  # noqa: E402
from aae.schema import (Accusation, Defense, DefectClass, EvidenceBase,  # noqa: E402
                        Finding, Posta, Verdict)

SOURCE = (
    "La perizia non conferma che l'immobile sia conforme alle norme edilizie. "
    "Il valore stimato e' 133.500 euro. "
    "Salvo il caso di sanatoria, il deposito risulta abusivo."
)


class ExistenceIsGuaranteed(unittest.TestCase):
    """The strong, deterministic half of the contract."""

    def test_verbatim_quote_is_grounded(self):
        self.assertTrue(G.is_grounded("Il valore stimato e' 133.500 euro", SOURCE))

    def test_fabricated_quote_is_rejected(self):
        self.assertFalse(G.is_grounded("Il valore stimato e' 210.000 euro", SOURCE))

    def test_altered_digit_is_rejected(self):
        """The nastiest real-world failure: a quote that is 99% right."""
        self.assertFalse(G.is_grounded("Il valore stimato e' 133.600 euro", SOURCE))

    def test_invented_sentence_is_rejected(self):
        self.assertFalse(G.is_grounded("La perizia conferma la conformita'", SOURCE))

    def test_empty_source_grounds_nothing(self):
        self.assertFalse(G.is_grounded("qualunque cosa", ""))


class RobustToDocumentNoise(unittest.TestCase):
    """Round-3 hardening: PDF noise must not cause FALSE NEGATIVES, because a
    false negative here silently lets a real finding through as ungrounded."""

    def test_zero_width_characters_are_stripped(self):
        quote = "Il valore\u200b stimato e' 133.500\u200c euro"
        self.assertTrue(G.is_grounded(quote, SOURCE))

    def test_hyphenation_across_linebreak(self):
        quote = "Il valore sti-\nmato e' 133.500 euro"
        self.assertTrue(G.is_grounded(quote, SOURCE))

    def test_curly_quotes_normalize_to_straight(self):
        curly = ("L\u2019immobile e\u2019 conforme \u201csecondo perizia\u201d "
                 "agli atti.")
        self.assertTrue(G.is_grounded("L'immobile e' conforme", curly))
        self.assertTrue(G.is_grounded('"secondo perizia"', curly))

    def test_normalize_is_idempotent(self):
        once = G.normalize(SOURCE)
        self.assertEqual(once, G.normalize(once))


class MeaningIsNotGuaranteed(unittest.TestCase):
    """The honest half. The check is conservative: when in doubt it BLOCKS and
    routes to the human, accepting over-flagging as the safe direction."""

    def test_quote_mined_from_negated_clause_is_flagged(self):
        mined = "l'immobile sia conforme alle norme edilizie"
        self.assertTrue(G.is_grounded(mined, SOURCE),
                        "the substring really is present — existence holds")
        self.assertTrue(G.negation_context_risk(mined, SOURCE),
                        "but it sits inside a negated clause and must be flagged")

    def test_quote_mined_from_exception_clause_is_flagged(self):
        mined = "il deposito risulta abusivo"
        self.assertTrue(G.negation_context_risk(mined, SOURCE),
                        "'Salvo il caso di...' is an exception marker")

    def test_clean_quote_carries_no_negation_risk(self):
        self.assertFalse(G.negation_context_risk(
            "Il valore stimato e' 133.500 euro", SOURCE))

    def test_over_flagging_is_the_accepted_cost(self):
        """Documented trade-off: ~6% of legitimate findings get routed to a
        human. This test pins the DIRECTION of the error, not its size: the
        gate must never resolve doubt in favour of condemning."""
        verdict = G.classify("l'immobile sia conforme alle norme edilizie", SOURCE)
        self.assertNotIn("condemn", verdict.lower(),
                         "a doubtful quote must never be cleared to condemn")


class EnforcementOnFindings(unittest.TestCase):
    """The gate applied to a real ledger: a condemnation resting on a quote
    that is not in the source must be downgraded, not merely annotated."""

    @staticmethod
    def _finding(quote, verdict=Verdict.ARTIFACT_DEFECTIVE):
        return Finding(
            id="F-1", element="valore", taxonomy_cell="outputs",
            defect_class=DefectClass.NUMERIC, posta=Posta.HIGH,
            accusation=Accusation(text="cifra errata", base=EvidenceBase.READING,
                                  evidence=quote, sections=["§2"]),
            defense=Defense(attempted=True, present=False, fact=None),
            verdict=verdict,
        )

    def test_fabricated_quote_cannot_keep_a_condemnation(self):
        f = self._finding("Il valore stimato e' 999.999 euro")
        notes = G.enforce_grounding([f], SOURCE)
        self.assertEqual(Verdict.NEEDS_READING, f.verdict,
                         "a hallucinated quote must never sustain a condemnation")
        self.assertTrue(notes)
        self.assertTrue(f.declared_limit, "the reason must be recorded, not silent")

    def test_grounded_quote_survives_untouched(self):
        f = self._finding("Il valore stimato e' 133.500 euro")
        notes = G.enforce_grounding([f], SOURCE)
        self.assertEqual(Verdict.ARTIFACT_DEFECTIVE, f.verdict)
        self.assertEqual([], notes)

    def test_ocr_source_downgrades_even_a_verbatim_match(self):
        """If the source itself was OCR'd, a perfect string match proves
        nothing about the original document."""
        f = self._finding("Il valore stimato e' 133.500 euro")
        G.enforce_grounding([f], SOURCE, source_trust="ocr")
        self.assertEqual(Verdict.NEEDS_READING, f.verdict)


if __name__ == "__main__":
    unittest.main()
