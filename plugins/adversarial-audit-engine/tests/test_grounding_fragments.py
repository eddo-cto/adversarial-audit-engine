"""test_grounding_fragments.py — footnote-tolerant, fragment-aware grounding (real-doc hardening).

A real-use run on a footnoted EU legal opinion (EDPB Opinion 28/2024) showed that legitimate verbatim
quotes were flagged 'absent' only because the source had inline footnote markers ('interest 53, an
interest') or the auditor joined two real passages with '...'. This pins the fix: such quotes recover to
STRICT, while a genuinely fabricated/paraphrased fragment still fails (the 'no fabrication condemns'
guarantee must hold).
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae.grounding import (classify, is_grounded, is_grounded_fragments,  # noqa: E402
                           _atomic_fragments)

SOURCE = (
    "As recalled by the EDPB in its Guidelines on legitimate interest 53, an interest may be regarded "
    "as legitimate if the following three cumulative criteria are met. The EDPB recalls that the GDPR "
    "does not establish any hierarchy between the different legal bases laid down in Article 6(1) GDPR 40. "
    "The development of an AI model covers all stages before any deployment of the AI model."
)


class FootnoteTolerant(unittest.TestCase):
    def test_inline_footnote_number_no_longer_blocks(self):
        # auditor omitted the '53' footnote marker present in the source
        q = '"an interest may be regarded as legitimate if the following three cumulative criteria are met"'
        self.assertFalse(is_grounded(q, SOURCE), "whole-string strict should miss it (footnote gap)")
        self.assertTrue(is_grounded_fragments(q, SOURCE))
        self.assertEqual(classify(q, SOURCE), "strict")

    def test_composite_ellipsis_join_both_present(self):
        q = ('"The EDPB recalls that the GDPR does not establish any hierarchy...'
             'The development of an AI model covers all stages before any deployment"')
        self.assertTrue(is_grounded_fragments(q, SOURCE))
        self.assertEqual(classify(q, SOURCE), "strict")

    def test_fabricated_fragment_still_fails(self):
        # first fragment is real, second is invented -> must NOT recover
        q = ('"an interest may be regarded as legitimate if the following three cumulative criteria..."'
             ' "the Board hereby imposes a binding fine of two million euro"')
        self.assertFalse(is_grounded_fragments(q, SOURCE))
        self.assertEqual(classify(q, SOURCE), "absent")

    def test_editorial_glue_outside_quotes_ignored(self):
        # only the quoted part must match; the '-- vs. para 60:' glue is not a quote
        q = 'Executive Summary: "does not establish any hierarchy between the different legal bases" -- vs. para 60:'
        self.assertTrue(is_grounded_fragments(q, SOURCE))

    def test_no_quotes_no_recovery(self):
        self.assertFalse(is_grounded_fragments("a bare paraphrase with no quotation marks at all", SOURCE))

    def test_atomic_fragments_splits_quotes_and_ellipsis(self):
        frags = _atomic_fragments('"alpha beta gamma delta...epsilon zeta eta theta" plain text')
        self.assertEqual(len(frags), 2)


if __name__ == "__main__":
    unittest.main()
