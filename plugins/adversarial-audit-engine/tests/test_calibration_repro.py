"""
test_calibration_repro.py — the calibration benchmark is an executable claim.

INVARIANTI_metodo.md §4 cites hard numbers (present 14/16 vs absent 2/8,
p=0.0047; 1 FP/42). This test runs the reproduction over the versioned,
anonymized dataset and fails if the data stops backing those numbers — turning
the paper's empirical claim into something CI checks on every push.
"""

import os
import subprocess
import sys
import unittest

BENCH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "benchmarks", "calibration",
)


class CalibrationReproduces(unittest.TestCase):
    def test_reproduce_strict_passes_over_the_versioned_dataset(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(BENCH, "reproduce.py"), "--strict"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0,
                         "reproduce.py --strict diverged from claims.json:\n"
                         + proc.stdout + proc.stderr)
        self.assertIn("All headline numbers reproduced", proc.stdout)

    def test_the_headline_boundary_is_present_in_the_output(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(BENCH, "reproduce.py")],
            capture_output=True, text=True,
        )
        self.assertIn("present: 14/16", proc.stdout)
        self.assertIn("absent: 2/8", proc.stdout)
        self.assertIn("0.0047", proc.stdout)


if __name__ == "__main__":
    unittest.main()
