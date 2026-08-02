"""
test_baselines_repro.py — the baseline positioning is an executable claim.

Runs the reproduction over the versioned, anonymized comparison and fails if the
data stops backing the three facts: landing identical (discipline != more recall),
~5x fewer findings (the false-alarm proxy), and the domain-re-derivation class
missed by both arms.
"""

import os
import subprocess
import sys
import unittest

BENCH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "benchmarks", "baselines",
)


class BaselinesReproduce(unittest.TestCase):
    def test_reproduce_strict_passes(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(BENCH, "reproduce.py"), "--strict"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0,
                         "reproduce.py --strict diverged:\n" + proc.stdout + proc.stderr)
        self.assertIn("All baseline-positioning values reproduced", proc.stdout)

    def test_the_three_facts_are_present(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(BENCH, "reproduce.py")],
            capture_output=True, text=True,
        )
        self.assertIn("identical per-paper: True", proc.stdout)      # same landing
        self.assertIn("overall 5.00x", proc.stdout)                  # ~5x noise
        self.assertIn("missed by BOTH arms: True", proc.stdout)      # class boundary


if __name__ == "__main__":
    unittest.main()
