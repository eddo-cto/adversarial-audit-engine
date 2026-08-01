"""
test_inter_nature_repro.py — the inter-nature check is an executable claim.

The one test the engine cannot run on itself (all its instances share a nature).
This runs the reproduction over the versioned, anonymized per-nature landings and
fails if the data stops backing the three certifications: nature-independent
boundary, different-nature gain (rho<1), and 0 decoy false positives per nature.
"""

import os
import subprocess
import sys
import unittest

BENCH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "benchmarks", "inter_nature",
)


class InterNatureReproduces(unittest.TestCase):
    def test_reproduce_strict_passes(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(BENCH, "reproduce.py"), "--strict"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0,
                         "reproduce.py --strict diverged:\n" + proc.stdout + proc.stderr)
        self.assertIn("All inter-nature claims reproduced", proc.stdout)

    def test_the_three_certifications_are_present(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(BENCH, "reproduce.py")],
            capture_output=True, text=True,
        )
        self.assertIn("P-target landing vectors identical across natures: True",
                      proc.stdout)
        self.assertIn("monotone non-decreasing A<=B<=C: True", proc.stdout)
        self.assertIn("0/7 false positives", proc.stdout)


if __name__ == "__main__":
    unittest.main()
