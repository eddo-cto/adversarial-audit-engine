"""
test_cli.py — first contact must not be a stack trace.

`run_core.py --help` used to crash with a FileNotFoundError traceback, because
the flag was treated as a payload path. That is the very first command a new
user types. These tests cover the whole argument surface end to end, in a
subprocess, exactly as a user would invoke it.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_CORE = os.path.join(PLUGIN_DIR, "scripts", "run_core.py")

PAYLOAD = {
    "artifact_name": "perizia.md",
    "internal_identity": "anthropic:claude-opus",
    "external_identity": None,
    "max_posta": "high",
    "excluded_cells": {d: "fuori perimetro" for d in
                       ("premises", "inputs", "mechanisms", "boundary", "interface")},
    # round-18: a complete run (A+B satisfied) so run_core exits 0
    "triage": {"dimensions_present": ["outputs"],
               "deploy_roles": ["verifier", "propagator"]},
    "findings": [{
        "element": "totale",
        "taxonomy_cell": "outputs",
        "defect_class": "numeric",
        "posta": "high",
        "accusation": {"text": "il totale non riconcilia",
                       "base": "execution",
                       "evidence": "121000+4500+52000=177500 != 175000",
                       "sections": ["§3", "§5"]},
        "defense": {"attempted": True, "present": False, "fact": None},
        "source_role": "verifier", "sources": ["perizia.md §3"], "source_grade": 1,
    }, {
        "element": "premessa vs dispositivo",
        "taxonomy_cell": "outputs",
        "defect_class": "non_local_mechanical",
        "posta": "high",
        "accusation": {"text": "una premessa contraddice il dispositivo",
                       "base": "execution", "evidence": "§2 ↔ §6",
                       "sections": ["§2", "§6"]},
        "defense": {"attempted": True, "present": False, "fact": None},
        "source_role": "propagator", "sources": ["perizia.md §2"], "source_grade": 1,
    }],
}


def run_cli(*args, stdin=None, out_dir=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = PLUGIN_DIR + os.pathsep + env.get("PYTHONPATH", "")
    if out_dir:
        env["AAE_OUT"] = out_dir
    return subprocess.run([sys.executable, RUN_CORE, *args],
                          input=stdin, capture_output=True, text=True, env=env)


class HelpAndVersion(unittest.TestCase):
    def test_help_exits_cleanly(self):
        for flag in ("--help", "-h", "help"):
            with self.subTest(flag=flag):
                p = run_cli(flag)
                self.assertEqual(0, p.returncode)
                self.assertIn("Usage", p.stdout)
                self.assertNotIn("Traceback", p.stdout + p.stderr)

    def test_help_documents_every_mode(self):
        out = run_cli("--help").stdout
        for token in ("--metrics", "AAE_OUT", "stdin"):
            self.assertIn(token, out)

    def test_help_states_the_red_line(self):
        """The one thing a user must know before trusting the output."""
        self.assertIn("VALIDATED", run_cli("--help").stdout)

    def test_version_matches_the_package(self):
        sys.path.insert(0, PLUGIN_DIR)
        import aae
        p = run_cli("--version")
        self.assertEqual(0, p.returncode)
        self.assertIn(aae.__version__, p.stdout)


class ErrorPaths(unittest.TestCase):
    """Every failure must be a readable message and a non-zero exit code, not
    a traceback. A traceback tells the user nothing and looks like a crash."""

    def _assert_clean_failure(self, proc, needle):
        self.assertEqual(2, proc.returncode)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn(needle, proc.stderr.lower())

    def test_unknown_option(self):
        self._assert_clean_failure(run_cli("--nope"), "unknown option")

    def test_missing_file(self):
        self._assert_clean_failure(run_cli("/nonexistent/payload.json"),
                                   "not found")

    def test_malformed_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write("{not json")
            path = fh.name
        try:
            self._assert_clean_failure(run_cli(path), "not valid json")
        finally:
            os.unlink(path)

    def test_payload_without_findings(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"artifact_name": "x"}, fh)
            path = fh.name
        try:
            self._assert_clean_failure(run_cli(path), "findings")
        finally:
            os.unlink(path)


class EndToEnd(unittest.TestCase):
    def test_runs_from_a_file_and_writes_a_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(PAYLOAD, fh)
            out_dir = os.path.join(tmp, "out")
            p = run_cli(path, out_dir=out_dir)
            self.assertEqual(0, p.returncode, p.stderr)
            self.assertIn("completion:", p.stdout)
            self.assertTrue(os.path.isdir(out_dir))
            self.assertTrue(os.listdir(out_dir), "no ledger was written")

    def test_runs_from_stdin(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = run_cli(stdin=json.dumps(PAYLOAD), out_dir=os.path.join(tmp, "out"))
            self.assertEqual(0, p.returncode, p.stderr)
            self.assertIn("Audit of:", p.stdout)

    def test_never_prints_validated_without_a_human(self):
        """The red line, checked at the outermost boundary of the system."""
        with tempfile.TemporaryDirectory() as tmp:
            p = run_cli(stdin=json.dumps(PAYLOAD), out_dir=os.path.join(tmp, "out"))
            self.assertNotIn("completion: VALIDATED", p.stdout)

    def test_governor_always_declares_its_own_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = run_cli(stdin=json.dumps(PAYLOAD), out_dir=os.path.join(tmp, "out"))
            self.assertIn("SELF-LIMIT", p.stdout.upper())

    def test_metrics_mode_runs_on_an_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = run_cli("--metrics", tmp)
            self.assertEqual(0, p.returncode, p.stderr)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
