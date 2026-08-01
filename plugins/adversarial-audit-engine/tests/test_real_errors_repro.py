"""
test_real_errors_repro.py — the real-error validation is an executable claim.

Ground truth = published Matters Arising (third-party experts). This test runs
the reproduction over the versioned, anonymized targets and fails if the data
stops backing the method-calibration numbers: 0 decoy false positives, the
general-reasoning-only boundary, and the honest synthetic→real drop.
"""

import os
import subprocess
import sys
import unittest

BENCH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "benchmarks", "real_errors",
)


class RealErrorsReproduce(unittest.TestCase):
    def test_reproduce_strict_passes(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(BENCH, "reproduce.py"), "--strict"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0,
                         "reproduce.py --strict diverged:\n" + proc.stdout + proc.stderr)
        self.assertIn("All values reproduced", proc.stdout)

    def test_the_headline_is_the_discipline_not_the_recall(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(BENCH, "reproduce.py")],
            capture_output=True, text=True,
        )
        # specificity + boundary must be present and correct
        self.assertIn("false positives on cross-domain decoys: 0/7", proc.stdout)
        self.assertIn("general reasoning", proc.stdout)
        self.assertIn("needs domain re-derivation:                         0/3",
                      proc.stdout)
        # the honest calibration drop must be shown, not hidden
        self.assertIn("88% -> 25%", proc.stdout)


if __name__ == "__main__":
    unittest.main()
