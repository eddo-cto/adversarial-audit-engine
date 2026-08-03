"""
test_benchmarks_guards.py — the benchmark guards must be NON-VACUOUS.

Round-9 F-FALSIFIABILITY fix: the paper claims each benchmark's reproduce.py is
"verified non-vacuous by perturbing one datum". This turns that claim into a
shipped test: for every benchmark we copy its data, flip ONE load-bearing datum,
run reproduce.py --strict, and require a non-zero exit. A guard that still passes
after the data is corrupted would be checking nothing.
"""
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.join(os.path.dirname(_HERE), "benchmarks")

# (benchmark dir, csv file, row index (0-based data row), column, new value)
CASES = [
    ("calibration", "dataset_injections.csv", 0, "detected", "0"),
    ("real_errors", "dataset_targets.csv", 2, "landed", "0"),   # T3 general-reasoning 1->0
    ("inter_nature", "dataset_landings.csv", 2, "nature_A", "0"),
    ("baselines", "dataset_llm_judge.csv", 0, "n_vanilla", "1"),
]


class BenchmarkGuardsAreNonVacuous(unittest.TestCase):
    def _perturb_and_run(self, bench, csv_name, row_idx, col, new_val):
        with tempfile.TemporaryDirectory() as tmp:
            dst = os.path.join(tmp, bench)
            shutil.copytree(os.path.join(_BENCH, bench), dst)
            path = os.path.join(dst, csv_name)
            with open(path, newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
                fields = rows[0].keys()
            self.assertIn(col, fields, f"{bench}/{csv_name} has no column {col}")
            old = rows[row_idx][col]
            self.assertNotEqual(old, new_val, "perturbation must change the value")
            rows[row_idx][col] = new_val
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(fields))
                w.writeheader()
                w.writerows(rows)
            proc = subprocess.run(
                [sys.executable, os.path.join(dst, "reproduce.py"), "--strict"],
                capture_output=True, text=True)
            return proc

    def test_each_benchmark_guard_catches_a_perturbation(self):
        for bench, csv_name, row_idx, col, new_val in CASES:
            with self.subTest(benchmark=bench):
                proc = self._perturb_and_run(bench, csv_name, row_idx, col, new_val)
                self.assertNotEqual(
                    0, proc.returncode,
                    f"{bench}: reproduce.py --strict still passed after flipping "
                    f"{csv_name}:{col} — the guard is VACUOUS.\n{proc.stdout}\n{proc.stderr}")


if __name__ == "__main__":
    unittest.main()
