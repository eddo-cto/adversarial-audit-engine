"""test_api_surface.py — pins the PUBLIC API frozen for 1.x (see API.md).

The contract an agent builds against (the `--schema` payload/finding keys, the enum vocabularies, the
rules), the `run_core.py` CLI, and `pipeline.discipline`'s signature must not drift silently. Enum members
are checked as a SUBSET (appending is allowed in 1.x; removing/renaming is a 2.0 break), so additive
changes pass and breaking ones fail here rather than in a client's integration.
"""
import inspect
import json
import os
import subprocess
import sys
import unittest

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_CORE = os.path.join(PLUGIN_DIR, "scripts", "run_core.py")
sys.path.insert(0, PLUGIN_DIR)


def _schema():
    out = subprocess.run([sys.executable, RUN_CORE, "--schema"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out.lstrip("﻿ \n\t"))


class SchemaContract(unittest.TestCase):
    def setUp(self):
        self.d = _schema()

    def test_top_level_keys(self):
        for k in ("payload_template", "finding_template", "vocabularies", "rules"):
            self.assertIn(k, self.d)

    def test_payload_keys(self):
        for k in ("artifact_name", "internal_identity", "external_identity", "max_posta",
                  "source_primary_reachable", "source_text", "excluded_cells", "triage", "findings"):
            self.assertIn(k, self.d["payload_template"], f"payload lost stable key {k}")

    def test_finding_keys(self):
        for k in ("source_role", "element", "taxonomy_cell", "defect_class", "posta", "accusation",
                  "defense", "cost_to_fix", "action", "declared_limit", "sources", "severity",
                  "source_grade", "action_state"):
            self.assertIn(k, self.d["finding_template"], f"finding lost stable key {k}")

    def test_enum_members_are_a_stable_subset(self):
        expected = {
            "taxonomy_cell": {"premises", "inputs", "mechanisms", "outputs", "boundary", "interface"},
            "defect_class": {"lookup", "numeric", "idiosyncratic_local", "non_local_mechanical",
                             "non_local_conceptual_documented", "non_local_conceptual_novel",
                             "epistemic", "ethical", "phenomenological"},
            "posta": {"low", "medium", "high"},
            "evidence_base": {"reading", "execution", "domain_knowledge", "pattern"},
            "cost_to_fix": {"trivial", "low", "medium", "high"},
            "action_state": {"open", "done", "deferred", "deliberately_discarded"},
        }
        vocab = self.d["vocabularies"]
        for name, members in expected.items():
            self.assertIn(name, vocab, f"vocabulary {name} disappeared")
            missing = members - set(vocab[name])
            self.assertEqual(set(), missing, f"{name} dropped stable members: {missing}")


class CliAndCore(unittest.TestCase):
    def test_version_flag(self):
        out = subprocess.run([sys.executable, RUN_CORE, "--version"],
                             capture_output=True, text=True, check=True).stdout
        self.assertIn("adversarial-audit-engine", out)

    def test_discipline_signature(self):
        from aae.pipeline import discipline
        sig = inspect.signature(discipline)
        params = list(sig.parameters.values())
        self.assertEqual(params[0].name, "payload")
        ai = sig.parameters.get("attested_identity")
        self.assertIsNotNone(ai, "attested_identity must stay in the signature")
        self.assertEqual(ai.kind, inspect.Parameter.KEYWORD_ONLY,
                         "attested_identity must remain keyword-only")


if __name__ == "__main__":
    unittest.main()
