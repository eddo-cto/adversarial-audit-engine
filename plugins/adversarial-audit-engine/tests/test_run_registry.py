"""
test_run_registry.py — the single longitudinal run registry (round 21, record-only).

Pins three properties:
  1. record_from_ledger DERIVES the first-class fields (independence_level, eye_vendor,
     governor verdict, calibration) — the independence of a run is recorded, not
     reconstructed by hand.
  2. a completed core run APPENDS exactly one line to ONE registry, and successive runs
     with DIFFERENT out_dirs still accrue into the SAME registry file.
  3. the write is best-effort: a failure NEVER raises (an audit is never broken by
     registry bookkeeping), and malformed lines are skipped on read.
"""
import json
import os
import sys
import tempfile
import types
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(_HERE, ".."))

import run_core                       # noqa: E402
from aae import run_registry as reg   # noqa: E402


def _valid_payload():
    return {
        "artifact_name": "smoke",
        "internal_identity": "anthropic:claude-x",
        "source_text": "The declared value is 5 units.",
        "max_posta": "low",
        "triage": {"dimensions_present": ["inputs"], "deploy_roles": ["verifier"]},
        "findings": [{
            "source_role": "verifier", "element": "the declared value",
            "taxonomy_cell": "inputs", "defect_class": "numeric", "posta": "low",
            "accusation": {"text": "unverified", "base": "reading",
                           "evidence": "The declared value is 5 units.", "sections": []},
            "defense": {"attempted": True, "present": False, "fact": None},
            "action": "verify at source", "source_grade": 1, "action_state": "open",
        }],
    }


def _fake_ledger(**kw):
    """A minimal stand-in exposing only what record_from_ledger reads."""
    d = dict(created_at=1_700_000_000.0, content_digest="abc123def456ff", artifact_name="art",
             independence_level=3, external_attested_identity="meta:llama3.1", internal_identity="anthropic:claude-x",
             completion_state="CROSS_MODEL_REVIEWED", run_manifest={"run_validity": "VALID"}, flags=[])
    d.update(kw)
    return types.SimpleNamespace(**d)


def _fake_rec(**kw):
    return types.SimpleNamespace(verdicts=kw.get("verdicts", {"artefatto_regge": 8, "accusa_vince": 1}))


class TestRecordDerivation(unittest.TestCase):
    def test_first_class_fields(self):
        rec = reg.record_from_ledger(_fake_ledger(), _fake_rec(), ledger_path="/x/y.ledger.json", box="claude-plus-local")
        self.assertEqual(rec["independence_level"], 3)
        self.assertEqual(rec["eye_vendor"], "meta")                 # derived from the attested identity
        self.assertEqual(rec["eye_identity"], "meta:llama3.1")
        self.assertEqual(rec["governor_completion"], "CROSS_MODEL_REVIEWED")
        self.assertEqual(rec["run_validity"], "VALID")
        self.assertEqual(rec["box"], "claude-plus-local")
        self.assertEqual(rec["verdicts"], {"artefatto_regge": 8, "accusa_vince": 1})
        self.assertTrue(rec["run_id"].endswith("abc123def456"))     # created + digest[:12]
        self.assertEqual(rec["ledger_path"], "/x/y.ledger.json")

    def test_no_eye_means_no_vendor(self):
        rec = reg.record_from_ledger(_fake_ledger(external_attested_identity="", independence_level=1,
                                                  completion_state="EXTERNAL_REVIEW_PENDING"),
                                     _fake_rec(), box="")
        self.assertEqual(rec["eye_vendor"], "")
        self.assertEqual(rec["independence_level"], 1)

    def test_calibration_read_from_flags(self):
        calibrated = reg.record_from_ledger(_fake_ledger(flags=[]), _fake_rec())
        not_cal = reg.record_from_ledger(
            _fake_ledger(flags=["TYPE-I: Type-I (false-demolition) NOT CALIBRATED for this auditor."]), _fake_rec())
        self.assertEqual(calibrated["calibration"], "calibrated")
        self.assertEqual(not_cal["calibration"], "NOT_CALIBRATED")


class TestRegistryPath(unittest.TestCase):
    def setUp(self):
        self._env = {k: os.environ.get(k) for k in ("AAE_REGISTRY", "AAE_HOME")}

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_explicit_wins(self):
        os.environ["AAE_REGISTRY"] = "/tmp/explicit.jsonl"
        os.environ["AAE_HOME"] = "/tmp/home"
        self.assertEqual(reg.registry_path(), "/tmp/explicit.jsonl")

    def test_home_fallback(self):
        os.environ.pop("AAE_REGISTRY", None)
        os.environ["AAE_HOME"] = "/tmp/home"
        self.assertEqual(reg.registry_path(), os.path.join("/tmp/home", "RUN_REGISTRY.jsonl"))


class TestAppendAndAccrual(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.registry = os.path.join(self.tmp, "reg", "RUN_REGISTRY.jsonl")
        self._prev = {k: os.environ.get(k) for k in ("AAE_OUT", "AAE_REGISTRY", "AAE_EXTERNAL_ATTESTED_IDENTITY")}
        os.environ["AAE_REGISTRY"] = self.registry

    def tearDown(self):
        for k, v in self._prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_completed_run_appends_one_line_to_single_registry(self):
        # two runs, DIFFERENT out_dirs -> still ONE registry with two lines
        for i in range(2):
            os.environ["AAE_OUT"] = os.path.join(self.tmp, f"out{i}")
            fp = os.path.join(self.tmp, f"f{i}.json")
            json.dump(_valid_payload(), open(fp, "w", encoding="utf-8"))
            run_core.main([fp])
        rows = reg.load(self.registry)
        self.assertEqual(len(rows), 2, "each completed run must add exactly one registry line")
        self.assertTrue(all("independence_level" in r and "governor_completion" in r for r in rows))

    def test_cross_vendor_eye_is_recorded(self):
        os.environ["AAE_OUT"] = os.path.join(self.tmp, "outx")
        os.environ["AAE_EXTERNAL_ATTESTED_IDENTITY"] = "meta:llama3.1"
        fp = os.path.join(self.tmp, "fx.json")
        json.dump(_valid_payload(), open(fp, "w", encoding="utf-8"))
        run_core.main([fp])
        rows = reg.load(self.registry)
        self.assertEqual(rows[-1]["eye_vendor"], "meta")
        self.assertGreaterEqual(rows[-1]["independence_level"], 3,
                                "an attested different-vendor eye must be recorded at level >= 3")


class TestBestEffort(unittest.TestCase):
    def test_append_never_raises_on_bad_path(self):
        # a path whose parent cannot be created -> append returns None, does not raise
        bad = os.path.join(os.devnull, "cannot", "RUN_REGISTRY.jsonl")
        self.assertIsNone(reg.append({"x": 1}, path=bad))

    def test_load_skips_malformed_lines(self):
        tmp = tempfile.mkdtemp()
        p = os.path.join(tmp, "r.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write('{"ok": 1}\n')
            fh.write("not json\n")
            fh.write('{"ok": 2}\n')
        self.assertEqual([r.get("ok") for r in reg.load(p)], [1, 2])

    def test_render_empty(self):
        tmp = tempfile.mkdtemp()
        self.assertIn("Nessun run registry", reg.render(os.path.join(tmp, "none.jsonl")))


class TestAxesCovered(unittest.TestCase):
    def test_axes_from_covered_cells_dict(self):
        led = _fake_ledger(covered_cells={"inputs": "N", "mechanisms": "T"})
        rec = reg.record_from_ledger(led, _fake_rec())
        self.assertEqual(rec["axes_covered"], ["inputs", "mechanisms"])

    def test_axes_fallback_to_findings(self):
        f1 = types.SimpleNamespace(taxonomy_cell="outputs")
        f2 = types.SimpleNamespace(taxonomy_cell="premises")
        led = _fake_ledger(covered_cells=None, findings=[f1, f2])
        rec = reg.record_from_ledger(led, _fake_rec())
        self.assertEqual(rec["axes_covered"], ["outputs", "premises"])


class TestConsolidate(unittest.TestCase):
    """Back-fill from serialized ledgers: idempotent, dedup by run_id, best-effort."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.registry = os.path.join(self.tmp, "RUN_REGISTRY.jsonl")

    def _write_ledger(self, name, created, digest, ind, verdicts, cells=None, eye=""):
        d = {
            "artifact_name": name, "created_at": created, "content_digest": digest,
            "independence_level": ind, "external_attested_identity": eye,
            "internal_identity": "anthropic:claude-x", "completion_state": "X",
            "run_manifest": {"run_validity": "VALID"}, "flags": [],
            "covered_cells": cells or {},
            "findings": [{"verdict": v, "taxonomy_cell": (cells or {}) and list(cells)[0] or "inputs"}
                         for v, n in verdicts.items() for _ in range(n)],
        }
        p = os.path.join(self.tmp, f"{name}.ledger.json")
        json.dump(d, open(p, "w", encoding="utf-8"))
        return p

    def test_consolidate_adds_then_is_idempotent(self):
        self._write_ledger("a", 1_700_000_000.0, "deadbeef0001", 1, {"accusa_vince": 2})
        self._write_ledger("b", 1_700_000_100.0, "deadbeef0002", 3, {"artefatto_regge": 3}, eye="meta:llama")
        rep1 = reg.consolidate([self.tmp], path=self.registry)
        self.assertEqual(rep1["added"], 2)
        rows = reg.load(self.registry)
        self.assertEqual(len(rows), 2)
        # a second sweep must add nothing (dedup by run_id)
        rep2 = reg.consolidate([self.tmp], path=self.registry)
        self.assertEqual(rep2["added"], 0)
        self.assertEqual(len(reg.load(self.registry)), 2)
        # the cross-vendor eye and independence were recorded on back-fill
        b = [r for r in rows if r["artifact"] == "b"][0]
        self.assertEqual(b["independence_level"], 3)
        self.assertEqual(b["eye_vendor"], "meta")


class TestSignature(unittest.TestCase):
    """The diachronic cross-vendor signature: descriptive, honest, no single score."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.registry = os.path.join(self.tmp, "RUN_REGISTRY.jsonl")

    def _rec(self, name, ind, verdicts, eye=""):
        return {"artifact": name, "independence_level": ind, "verdicts": verdicts,
                "eye_vendor": eye, "run_id": f"{name}-{ind}"}

    def test_signature_reports_deflation_when_independence_rises(self):
        # same artefact: L1 condemns 4/4, L3 condemns 0/4 (all hold) -> condemn deflates
        reg.append(self._rec("Fascicolo X", 1, {"accusa_vince": 4}), path=self.registry)
        reg.append(self._rec("Fascicolo X", 3, {"artefatto_regge": 4}, eye="meta"), path=self.registry)
        out = reg.signature(self.registry)
        self.assertIn("SIGNATURE", out)
        self.assertIn("1->3", out)
        self.assertIn("deflaziona", out.lower() + out)  # narrative present
        # aggregate line: one pair, cross-vendor at high, condemn deflated
        self.assertIn("coppie: 1", out)
        self.assertIn("1/1", out)  # both "cross-vendor" and "deflated" roll-ups are 1/1

    def test_signature_needs_two_levels(self):
        reg.append(self._rec("Solo L1", 1, {"accusa_vince": 1}), path=self.registry)
        out = reg.signature(self.registry)
        self.assertIn(">=2 livelli", out)

    def test_signature_is_honest_about_not_being_a_proof(self):
        reg.append(self._rec("Y", 1, {"accusa_vince": 2}), path=self.registry)
        reg.append(self._rec("Y", 3, {"artefatto_regge": 2}, eye="meta"), path=self.registry)
        out = reg.signature(self.registry)
        self.assertIn("non una dimostrazione", out.lower())
        self.assertIn("Goodhart", out)


if __name__ == "__main__":
    unittest.main()
