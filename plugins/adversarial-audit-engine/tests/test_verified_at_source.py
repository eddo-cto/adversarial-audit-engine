"""
test_verified_at_source.py — the verified-at-source gate (#88), the DUAL of the
round-12 source-grade gate. Born from two real misattributions an L3 audit caught:
a "Premier Partner" absent from the official directory, and a "Clutch 5.0" that
belonged to a different company. A reputation/credential claim earns the "verified"
badge ONLY if read on the PRIMARY authoritative source (grade 1); asserted on an
aggregator / snippet / the subject's own page (grade > 1), it is downgraded to
self-declared and flagged. Record-only: it NEVER touches the verdict.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN = os.path.dirname(_HERE)
sys.path.insert(0, _PLUGIN)

from aae.schema import (Ledger, Finding, Accusation, Defense, DefectClass,  # noqa: E402
                        EvidenceBase, Posta, Verdict)
from aae.source_grade import (SourceGrade, enforce_verified_at_source_gate,  # noqa: E402
                              verified_at_source_coverage)


def _credential(fid, grade, *, asserted_verified):
    """A reputation/credential claim finding. It is NOT a condemnation — the badge
    axis is orthogonal to the verdict, so we build a benign ARTIFACT_HOLDS finding."""
    f = Finding(id=fid, element="reputation", taxonomy_cell="outputs",
                defect_class=DefectClass.IDIOSYNCRATIC_LOCAL, posta=Posta.MEDIUM,
                accusation=Accusation(text="claims Premier Partner",
                                      base=EvidenceBase.READING, evidence="ev",
                                      sections=["s1"]),
                defense=Defense(attempted=True, present=True, fact="present on page"),
                action="verify", source_grade=grade,
                credential_claim=True, verified_at_source=asserted_verified)
    f.adjudicate()
    return f


class VerifiedAtSourceGate(unittest.TestCase):
    def test_verified_badge_on_aggregator_is_downgraded_and_flagged(self):
        led = Ledger(artifact_name="x")
        led.add(_credential("F1", SourceGrade.GENERALIST, asserted_verified=True))
        v0 = led.findings[0].verdict
        notes = enforce_verified_at_source_gate(led)
        self.assertIs(False, led.findings[0].verified_at_source)  # downgraded
        self.assertTrue(any("VERIFIED-AT-SOURCE" in n for n in notes))
        self.assertEqual(v0, led.findings[0].verdict)  # verdict untouched

    def test_verified_badge_on_institutional_is_downgraded(self):
        led = Ledger(artifact_name="x")
        led.add(_credential("F1", SourceGrade.INSTITUTIONAL, asserted_verified=True))
        enforce_verified_at_source_gate(led)
        self.assertIs(False, led.findings[0].verified_at_source)

    def test_verified_badge_on_primary_stands(self):
        led = Ledger(artifact_name="x")
        led.add(_credential("F1", SourceGrade.PRIMARY_FILED, asserted_verified=True))
        notes = enforce_verified_at_source_gate(led)
        self.assertIs(True, led.findings[0].verified_at_source)  # earned, kept
        self.assertEqual([], notes)

    def test_self_declared_claim_is_not_touched(self):
        led = Ledger(artifact_name="x")
        led.add(_credential("F1", SourceGrade.GENERALIST, asserted_verified=False))
        notes = enforce_verified_at_source_gate(led)
        self.assertIs(False, led.findings[0].verified_at_source)
        self.assertEqual([], notes)  # never asserted verified -> nothing to flag

    def test_non_credential_finding_is_ignored(self):
        led = Ledger(artifact_name="x")
        f = _credential("F1", SourceGrade.GENERALIST, asserted_verified=True)
        f.credential_claim = False
        led.add(f)
        notes = enforce_verified_at_source_gate(led)
        self.assertEqual([], notes)

    def test_coverage_tallies_verified_declared_unearned(self):
        led = Ledger(artifact_name="x")
        led.add(_credential("F1", SourceGrade.PRIMARY_FILED, asserted_verified=True))
        led.add(_credential("F2", SourceGrade.GENERALIST, asserted_verified=False))
        led.add(_credential("F3", SourceGrade.GENERALIST, asserted_verified=True))
        cov_before = verified_at_source_coverage(led)
        self.assertEqual(1, cov_before["verified"])
        self.assertEqual(1, cov_before["unearned"])   # F3 before the gate
        self.assertEqual(1, cov_before["declared"])
        # after the gate, F3 is corrected to declared and 'unearned' clears
        enforce_verified_at_source_gate(led)
        cov_after = verified_at_source_coverage(led)
        self.assertEqual(1, cov_after["verified"])
        self.assertEqual(0, cov_after["unearned"])
        self.assertEqual(2, cov_after["declared"])


class VerifiedAtSourceInDiscipline(unittest.TestCase):
    """The gate must be wired into the ONE discipline both product paths run."""

    def test_discipline_flags_unearned_verified_badge(self):
        from aae.pipeline import discipline
        payload = {
            "artifact_name": "agency-report",
            "findings": [{
                "source_role": "oracle",
                "element": "Eactive Google Premier Partner",
                "taxonomy_cell": "outputs",
                "defect_class": "idiosyncratic_local",
                "posta": "medium",
                "accusation": {"text": "the report presents this as verified",
                               "base": "reading", "evidence": "ev", "sections": ["s1"]},
                "defense": {"attempted": True, "present": True, "fact": "on the agency page"},
                "action": "read the official directory",
                "declared_limit": "not read on the official Google Partners directory",
                "sources": ["agency about-page"],
                "source_grade": 3,
                "credential_claim": True,
                "verified_at_source": True,
            }],
        }
        result = discipline(payload)
        led = result.ledger
        self.assertTrue(any("VERIFIED-AT-SOURCE" in f for f in led.flags))
        self.assertIs(False, led.findings[0].verified_at_source)
        self.assertEqual(1, led.verified_at_source_coverage.get("declared"))
        # round-trips through JSON with the new coverage present
        self.assertIn("verified_at_source_coverage", led.to_json())


if __name__ == "__main__":
    unittest.main()
