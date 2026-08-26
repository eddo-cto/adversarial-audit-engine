"""
test_temporal_axis.py — the record-only temporal/epistemic axis (round 19).

The axis types a finding's status ACROSS turns in longitudinal use. It is
orthogonal to the taxonomy (WHERE) and to the verdict (this turn's truth), and
it is RECORD-ONLY: adjudicate() must never read it. These tests pin exactly
that — the axis is carried, honest, and inert with respect to the state machine.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aae.schema import (Finding, Accusation, Defense, DefectClass, EvidenceBase,  # noqa: E402
                        Posta, Verdict, CostToFix, TemporalStatus)
from aae.orchestrator import parse_finding, _finding_to_payload  # noqa: E402


def _mk(**kw) -> Finding:
    base = dict(
        id="F-1",
        element="DOC §3 the load-bearing figure",
        taxonomy_cell="inputs",
        defect_class=DefectClass.IDIOSYNCRATIC_LOCAL,
        posta=Posta.MEDIUM,
        accusation=Accusation(text="the figure is unverified at source",
                              base=EvidenceBase.READING, evidence="", sections=[]),
        defense=Defense(attempted=True, present=False, fact=None),
        action="verify at primary source",
    )
    base.update(kw)
    return Finding(**base)


class TestDefaultsAndClaimKey(unittest.TestCase):
    def test_defaults_are_unset(self):
        f = _mk()
        self.assertIsNone(f.temporal_status)
        self.assertIsNone(f.likelihood)
        self.assertEqual(f.conflict_with, [])
        self.assertFalse(f.perishable_pivot)
        self.assertIsNone(f.claim_key)
        self.assertIsNone(f.superseded_by)

    def test_claim_key_is_deterministic_and_verdict_independent(self):
        f1 = _mk()
        f2 = _mk(id="OTHER-99")           # different per-run id
        f2.verdict = Verdict.ARTIFACT_DEFECTIVE
        self.assertEqual(f1.compute_claim_key(), f2.compute_claim_key(),
                         "claim_key must not depend on id or verdict")
        self.assertTrue(f1.compute_claim_key().startswith("ck_"))

    def test_claim_key_changes_with_where_or_what(self):
        f1 = _mk()
        f2 = _mk(taxonomy_cell="outputs")
        self.assertNotEqual(f1.compute_claim_key(), f2.compute_claim_key())

    def test_to_dict_autofills_claim_key_and_serializes_status(self):
        f = _mk(temporal_status=TemporalStatus.STABLE)
        d = f.to_dict()
        self.assertEqual(d["temporal_status"], "stable")
        self.assertTrue(d["claim_key"].startswith("ck_"))
        self.assertEqual(d["claim_key"], f.compute_claim_key())


class TestRecordOnly(unittest.TestCase):
    """The axis must NOT change adjudication: same finding, same verdict, whether
    or not the temporal fields are populated."""

    def test_adjudicate_unaffected(self):
        plain = _mk()
        loaded = _mk(temporal_status=TemporalStatus.PROVISIONAL,
                     likelihood=0.3, likelihood_basis="one aggregator, not primary",
                     perishable_pivot=True, pivot_valid_until="2027-07-01")
        self.assertEqual(plain.adjudicate(), loaded.adjudicate())

    def test_conflicted_finding_still_condemns_normally(self):
        f = _mk(temporal_status=TemporalStatus.CONFLICTED,
                conflict_with=["ck_abcdef0123456789"])
        f.accusation.base = EvidenceBase.EXECUTION
        # defense attempted, no defending fact, solid base -> real defect
        self.assertEqual(f.adjudicate(), Verdict.ARTIFACT_DEFECTIVE)


class TestSoftValidation(unittest.TestCase):
    def test_likelihood_requires_basis(self):
        f = _mk(temporal_status=TemporalStatus.PROVISIONAL, likelihood=0.4)
        self.assertTrue(any("requires a declared basis" in p for p in f.validate()))

    def test_likelihood_range(self):
        f = _mk(temporal_status=TemporalStatus.PROVISIONAL,
                likelihood=1.4, likelihood_basis="x")
        self.assertTrue(any("in [0,1]" in p for p in f.validate()))

    def test_likelihood_only_on_provisional(self):
        f = _mk(temporal_status=TemporalStatus.STABLE,
                likelihood=0.4, likelihood_basis="x")
        self.assertTrue(any("only meaningful on a provisional" in p for p in f.validate()))

    def test_conflict_requires_conflicted(self):
        f = _mk(conflict_with=["ck_deadbeefdeadbeef"])
        self.assertTrue(any("requires temporal_status=conflicted" in p for p in f.validate()))

    def test_wellformed_provisional_adds_no_problem(self):
        f = _mk(temporal_status=TemporalStatus.PROVISIONAL,
                likelihood=0.35, likelihood_basis="single non-primary source")
        # no temporal-axis problem (there may be others unrelated; assert none of ours)
        probs = f.validate()
        self.assertFalse(any(k in p for p in probs
                             for k in ("likelihood", "conflict_with")))


class TestRoundTrip(unittest.TestCase):
    def test_payload_roundtrip_preserves_axis(self):
        f = _mk(temporal_status=TemporalStatus.PROVISIONAL,
                likelihood=0.6, likelihood_basis="aggregator claim, unverified",
                perishable_pivot=True, pivot_valid_until="2027-07-01",
                superseded_by="ck_1111222233334444")
        payload = _finding_to_payload(f)
        g = parse_finding(payload, role_key="verifier")
        self.assertEqual(g.temporal_status, TemporalStatus.PROVISIONAL)
        self.assertEqual(g.likelihood, 0.6)
        self.assertEqual(g.likelihood_basis, "aggregator claim, unverified")
        self.assertTrue(g.perishable_pivot)
        self.assertEqual(g.pivot_valid_until, "2027-07-01")
        self.assertEqual(g.superseded_by, "ck_1111222233334444")
        # claim_key travels through the payload (auto-filled on serialize)
        self.assertEqual(g.claim_key, f.compute_claim_key())

    def test_absent_axis_roundtrips_to_unset(self):
        f = _mk()
        g = parse_finding(_finding_to_payload(f), role_key="verifier")
        self.assertIsNone(g.temporal_status)
        self.assertEqual(g.conflict_with, [])


if __name__ == "__main__":
    unittest.main()
