"""
test_evidence_span.py — accusation.evidence_span (1.13, record-only clickable-citation byte offsets).

Pins:
  1. a malformed span is an integrity flag; a well-formed one / None is fine;
  2. discipline AUTO-STAMPS the span from source_text (exact byte offsets of the verbatim quote);
  3. parse round-trips a provided span; to_dict emits it;
  4. VERDICT-NEUTRAL: stamping never changes a verdict.
"""
import copy
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

from aae.schema import Finding, Accusation, Defense, EvidenceBase, DefectClass, Posta, Verdict  # noqa: E402
from aae.orchestrator import parse_finding                                                      # noqa: E402
from aae import pipeline                                                                        # noqa: E402

SRC = "foo the value is 5 bar"
EV = "the value is 5"
OFF = SRC.index(EV)


def _mk(span):
    f = Finding(id="F", element="v", taxonomy_cell="mechanisms", defect_class=DefectClass.NUMERIC,
               posta=Posta.LOW,
               accusation=Accusation(text="t", base=EvidenceBase.EXECUTION, evidence=EV, evidence_span=span),
               defense=Defense(attempted=True, present=True, fact="ok"))
    f.verdict = Verdict.ARTIFACT_HOLDS
    return f


class TestValidation(unittest.TestCase):
    def test_bad_span_flagged(self):
        self.assertTrue(any("evidence_span" in p for p in _mk([5, 2]).validate()))
        self.assertTrue(any("evidence_span" in p for p in _mk([-1, 3]).validate()))

    def test_good_and_none_ok(self):
        self.assertFalse(any("evidence_span" in p for p in _mk([0, 5]).validate()))
        self.assertFalse(any("evidence_span" in p for p in _mk(None).validate()))


def _payload(with_src):
    pl = {"artifact_name": "x", "internal_identity": "anthropic:c", "max_posta": "low",
          "excluded_cells": {c: "n/a" for c in ("premises", "inputs", "mechanisms", "outputs", "boundary", "interface")},
          "findings": [{"source_role": "verifier", "element": "v", "taxonomy_cell": "mechanisms",
                        "defect_class": "numeric", "posta": "low", "source_grade": 1,
                        "accusation": {"text": "t", "base": "execution", "evidence": EV},
                        "defense": {"attempted": True, "present": True, "fact": "ok"}, "action": ""}]}
    if with_src:
        pl["source_text"] = SRC
    return pl


class TestAutoStamp(unittest.TestCase):
    def test_stamped_from_source(self):
        led = pipeline.discipline(copy.deepcopy(_payload(True))).ledger
        self.assertEqual(led.findings[0].accusation.evidence_span, [OFF, OFF + len(EV)])

    def test_no_source_no_span(self):
        led = pipeline.discipline(copy.deepcopy(_payload(False))).ledger
        self.assertIsNone(led.findings[0].accusation.evidence_span)


class TestRoundTripAndNeutral(unittest.TestCase):
    def test_parse_round_trip(self):
        raw = {"element": "v", "defect_class": "numeric", "posta": "low",
               "accusation": {"text": "t", "base": "execution", "evidence": EV, "evidence_span": [4, 18]},
               "defense": {"attempted": True, "present": True, "fact": "ok"}}
        f = parse_finding(raw, role_key="verifier")
        self.assertEqual(f.accusation.evidence_span, [4, 18])
        self.assertEqual(f.to_dict()["accusation"]["evidence_span"], [4, 18])

    def test_verdict_neutral(self):
        v_src = pipeline.discipline(copy.deepcopy(_payload(True))).ledger.findings[0].verdict
        v_no = pipeline.discipline(copy.deepcopy(_payload(False))).ledger.findings[0].verdict
        self.assertEqual(v_src, v_no)   # stamping a span never changes a verdict


if __name__ == "__main__":
    unittest.main()
