"""test_deep_causal_policy.py — A1: deep-causal deploys on a deterministic STRUCTURAL trigger, and the
product path ENFORCES it (a warranted-but-absent deep-causal is flagged, not silently skipped).

Grounded in the 10-run measurement (deep_causal is CONTEXTUAL, 7/10): not a blanket mandate, not the
agent's whim — it fires on HIGH posta AND something to cluster (enough findings, or findings sharing a
cell, or a conceptual-novel finding). On a small/sparse run it correctly stays off.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from aae.layer_policy import deep_causal_warranted  # noqa: E402
from aae.pipeline import discipline  # noqa: E402
from aae.schema import (Finding, Accusation, Defense, DefectClass, EvidenceBase, Posta)  # noqa: E402


def _f(cell, cls=DefectClass.NON_LOCAL_MECHANICAL):
    return Finding(id="x", element="e", taxonomy_cell=cell, defect_class=cls, posta=Posta.HIGH,
                   accusation=Accusation(text="t", base=EvidenceBase.READING, evidence="e",
                                         sections=["s1", "s2"]),
                   defense=Defense(attempted=True), source_role="propagator", source_grade=1)


class Predicate(unittest.TestCase):
    def test_medium_never(self):
        self.assertFalse(deep_causal_warranted([_f("mechanisms")] * 9, Posta.MEDIUM))

    def test_high_enough_findings(self):
        five = [_f(c) for c in ("premises", "inputs", "mechanisms", "outputs", "boundary")]
        self.assertTrue(deep_causal_warranted(five, Posta.HIGH))

    def test_high_two_sharing_a_cell(self):
        self.assertTrue(deep_causal_warranted([_f("mechanisms"), _f("mechanisms")], Posta.HIGH))

    def test_high_conceptual_novel(self):
        self.assertTrue(deep_causal_warranted([_f("mechanisms", DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL)],
                                              Posta.HIGH))

    def test_high_sparse_not_warranted(self):
        sparse = [_f("mechanisms"), _f("inputs"), _f("outputs")]   # 3 distinct, <5, no share, not novel
        self.assertFalse(deep_causal_warranted(sparse, Posta.HIGH))


def _payload(cells, deep_ran=False):
    findings = [{"source_role": "propagator", "element": f"e{i}", "taxonomy_cell": c,
                 "defect_class": "non_local_mechanical", "posta": "high",
                 "accusation": {"text": "t", "base": "reading", "evidence": "e", "sections": ["s1", "s2"]},
                 "defense": {"attempted": True, "present": True, "fact": "d"},
                 "cost_to_fix": "low", "sources": ["s"], "source_grade": 1, "action_state": "open"}
                for i, c in enumerate(cells)]
    execution = {"layers": {"deep_causal": {"status": "ran", "justification": "x"}}} if deep_ran else None
    return {"artifact_name": "x", "internal_identity": "anthropic:x", "max_posta": "high",
            "triage": {"dimensions_present": ["mechanisms"], "deploy_roles": ["verifier", "propagator"]},
            "execution": execution, "findings": findings}


class Enforcement(unittest.TestCase):
    def test_warranted_but_absent_is_flagged(self):
        led = discipline(_payload(["premises", "inputs", "mechanisms", "outputs", "boundary"])).ledger
        self.assertTrue(any("DEEP-CAUSAL WARRANTED BUT NOT RUN" in f for f in led.flags))

    def test_warranted_and_ran_no_flag(self):
        led = discipline(_payload(["premises", "inputs", "mechanisms", "outputs", "boundary"],
                                  deep_ran=True)).ledger
        self.assertFalse(any("DEEP-CAUSAL WARRANTED" in f for f in led.flags))

    def test_not_warranted_no_flag(self):
        led = discipline(_payload(["mechanisms", "inputs", "outputs"])).ledger   # sparse
        self.assertFalse(any("DEEP-CAUSAL WARRANTED" in f for f in led.flags))


if __name__ == "__main__":
    unittest.main()
