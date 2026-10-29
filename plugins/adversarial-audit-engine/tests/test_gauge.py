"""Gauge invariance (1.20) — a SEVERITY declaration (posta, cost_to_fix) must never decide the TRUTH class.

Pins: the F-12 escape (REDUCED on a non-primary datum slipping past the source-grade gate) is closed; the probe finds
zero leaks on a mixed payload; the probe DETECTS a leak when the old gate is put back; a seeded property test over random
findings; the probe is record-only (verdicts identical with and without it); the summary is serialized.
"""
import json
import random
import unittest
from unittest import mock

from aae.pipeline import discipline
from aae.gauge import truth_class, gauge_probe
from aae.schema import Verdict

SRC = "La relazione cita la norma. Il calcolo è nel prospetto. La data è indicata in nota."


def _f(i, **over):
    f = {"id": f"F{i:02d}", "element": f"E{i}", "taxonomy_cell": "inputs", "defect_class": "lookup",
         "posta": "low", "cost_to_fix": "trivial", "source_grade": 1,
         "accusation": {"text": "t", "base": "reading", "evidence": "La relazione cita la norma.",
                        "sections": ["§1"]},
         "defense": {"attempted": True, "present": False}, "attack": {"attempted": True, "vector": "v"},
         "action": "correggere", "declared_limit": "l"}
    f.update(over)
    return f


def _payload(findings):
    return {"artifact_name": "t", "artifact_id": "g1", "source_text": SRC, "max_posta": "low",
            "findings": findings}


class TestGauge(unittest.TestCase):

    def test_truth_class(self):
        self.assertEqual(truth_class("accusa_vince"), "condemn")
        self.assertEqual(truth_class("accusa_ridimensionata"), "condemn")
        self.assertEqual(truth_class("artefatto_regge"), "holds")
        for v in ("da_leggere", "conteso", "pending"):
            self.assertEqual(truth_class(v), "open")

    def test_f12_escape_closed(self):
        # CT 2800/2025 F-12: lookup on a grade-2 source, primary reachable, cost trivial -> was REDUCED
        f = _f(1, source_grade=2, accusation={"text": "t", "base": "domain_knowledge",
                                              "evidence": "x", "sections": ["§1"]})
        L = discipline(_payload([f])).ledger
        self.assertEqual(L.findings[0].verdict, Verdict.NEEDS_READING)
        self.assertEqual(L.gauge_summary["dependent"], 0)

    def test_no_leak_on_mixed_payload(self):
        fs = [_f(1), _f(2, cost_to_fix="high"), _f(3, source_grade=2, cost_to_fix="trivial"),
              _f(4, source_grade=2, cost_to_fix="medium"),
              _f(5, defense={"attempted": True, "present": True, "fact": "la nota lo dice"}),
              _f(6, requires_docs=["assente"]), _f(7, posta="high")]
        L = discipline(_payload(fs)).ledger
        self.assertEqual(L.gauge_summary["checked"], 7)
        self.assertEqual(L.gauge_report, [])

    def test_detects_leak_when_old_gate_is_restored(self):
        def old_gate(ledger, *, primary_reachable=True):
            for f in ledger.findings:
                if f.verdict == Verdict.ARTIFACT_DEFECTIVE and int(f.source_grade or 9) > 1 and primary_reachable:
                    f.verdict = Verdict.NEEDS_READING
            return []
        with mock.patch("aae.pipeline.enforce_source_grade_gate", old_gate):
            L = discipline(_payload([_f(1, source_grade=2, cost_to_fix="trivial")])).ledger
        self.assertEqual(L.gauge_summary["dependent"], 1)
        self.assertTrue(any(r["lever"] == "cost_to_fix" for r in L.gauge_report))
        self.assertTrue(any("GAUGE" in n for n in L.flags))

    def test_property_random_findings(self):
        rng = random.Random(1720)
        fs = []
        for i in range(60):
            fs.append(_f(i, defect_class=rng.choice(["lookup", "numeric", "normative", "epistemic"]),
                         posta=rng.choice(["low", "medium", "high"]),
                         cost_to_fix=rng.choice(["trivial", "low", "medium", "high"]),
                         source_grade=rng.choice([1, 2, 3, 9]),
                         rests_on_authority=rng.random() < 0.3,
                         authority_cited=rng.choice([None, "art. 1"]),
                         requires_docs=rng.choice([[], ["assente"]]),
                         accusation={"text": "t", "base": rng.choice(["reading", "execution", "domain_knowledge"]),
                                     "evidence": rng.choice(["La relazione cita la norma.", "non nel testo"]),
                                     "sections": ["§1"]},
                         defense={"attempted": rng.random() < 0.9, "present": rng.random() < 0.3,
                                  "fact": rng.choice(["", "fatto"])}))
        for chunk in (fs[:20], fs[20:40], fs[40:]):
            L = discipline(_payload(chunk)).ledger
            self.assertEqual(L.gauge_report, [], L.gauge_report[:3])

    def test_record_only(self):
        fs = [_f(1), _f(2, source_grade=2), _f(3, cost_to_fix="high", source_grade=3)]
        a = [f.verdict for f in discipline(_payload(fs)).ledger.findings]
        b = [f.verdict for f in discipline(_payload(fs), _probe=True).ledger.findings]
        self.assertEqual(a, b)

    def test_serialized(self):
        d = json.loads(discipline(_payload([_f(1)])).ledger.to_json())
        self.assertIn("gauge_summary", d)
        self.assertEqual(d["gauge_summary"]["checked"], 1)


if __name__ == "__main__":
    unittest.main()
