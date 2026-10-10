"""governor_check coverage count (1.14.1).

Regression: the Stop-hook governor counted len(flags) as "N dimension(s) uncovered",
so any EVIDENCE-BASE / COMPETENCE / TYPE-I flag inflated a false coverage gap (and the
ac score). Only the coverage gate's own 'COVERAGE INCOMPLETE' flags are uncovered
dimensions. Pins the fix against meta_epistemic's correct behavior.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))
import governor_check  # noqa: E402


def _ledger(flags, independence=3):
    # a minimally plausible, fully-covered ledger with one CONTESO so clean/calibration
    # signals stay quiet and we isolate the coverage signal
    return {
        "independence_level": independence,
        "flags": flags,
        "findings": [
            {"verdict": "artefatto_regge", "declared_limit": "x"},
            {"verdict": "conteso", "declared_limit": "y"},
        ],
    }


class TestGovernorCoverageCount(unittest.TestCase):

    def test_non_coverage_flags_are_not_counted_as_uncovered(self):
        led = _ledger([
            "EVIDENCE-BASE: F05: missing evidence [...] → NEEDS_EXPERT",
            "COMPETENCE: regulated domain — classify the authority axis on F08",
            "TYPE-I: not calibrated",
        ])
        _verdict, _ac, notes = governor_check.verdict_from_ledger(led)
        self.assertFalse([n for n in notes if "dimension(s) uncovered" in n],
                         "non-coverage flags must not be reported as uncovered dimensions")

    def test_real_coverage_incomplete_flag_is_counted(self):
        led = _ledger([
            "COVERAGE INCOMPLETE: 'boundary' neither covered nor excluded-with-justification",
            "TYPE-I: not calibrated",
        ])
        _verdict, _ac, notes = governor_check.verdict_from_ledger(led)
        hits = [n for n in notes if "dimension(s) uncovered" in n]
        self.assertTrue(hits)
        self.assertIn("1 dimension(s)", hits[0])   # exactly one real coverage gap, not two flags


if __name__ == "__main__":
    unittest.main()
