"""Competence gate (1.14) — the authority axis.

A finding whose defect turns on an EXTERNAL rule is confirmable only if it cites the
governing authority. Pins: hard route of a declared-but-uncited condemnation to
NEEDS_EXPERT; no-op when the norm IS cited; non-condemning verdicts keep their state
but carry the limit; the regulated-domain completeness flag; and — the measured design
choice — NO demotion of a legitimate internal finding that never declared authority.
"""
import unittest

from aae.pipeline import discipline


def _finding(fid, **over):
    f = {
        "id": fid, "element": "E", "taxonomy_cell": "boundary",
        "defect_class": "normative", "posta": "high",
        "accusation": {"text": "violates rule Y", "base": "reading",
                       "evidence": "X violates rule Y.", "sections": ["§1", "§2"]},
        "defense": {"attempted": True, "present": False},
        "attack": {"attempted": True, "vector": "norm-check"},
        "cost_to_fix": "high", "severity": "alta", "source_grade": 1,
        "rests_on_authority": True,
    }
    f.update(over)
    return f


def _payload(findings, **over):
    p = {"artifact_name": "t", "domain_regulated": True,
         "source_text": "X violates rule Y.", "findings": findings}
    p.update(over)
    return p


def _by_id(ledger):
    return {f.id: f for f in ledger.findings}


class TestCompetenceGate(unittest.TestCase):

    def test_condemning_authority_dependent_without_norm_routed_to_expert(self):
        r = discipline(_payload([_finding("N1")]))
        f = _by_id(r.ledger)["N1"]
        self.assertEqual(f.verdict.value, "conteso")   # NEEDS_EXPERT
        self.assertIn("COMPETENCE", (f.declared_limit or ""))

    def test_authority_cited_is_not_routed_by_competence_gate(self):
        # cite the norm + make the quote verbatim so the grounding gate stays out of it
        r = discipline(_payload([_finding("N2", authority_cited="art. 10 c.p.c.")]))
        f = _by_id(r.ledger)["N2"]
        # competence gate must NOT add its limit when a norm is cited
        self.assertNotIn("regola esterna non citata", (f.declared_limit or ""))
        notes = [x for x in r.ledger.flags if "COMPETENCE: N2:" in x]
        self.assertEqual(notes, [])

    def test_normative_defect_class_triggers_even_without_rests_flag(self):
        r = discipline(_payload([_finding("N3", rests_on_authority=False,
                                          defect_class="normative")]))
        f = _by_id(r.ledger)["N3"]
        self.assertEqual(f.verdict.value, "conteso")

    def test_non_condemning_keeps_verdict_but_carries_limit(self):
        # a HOLDING finding that rests on an uncited authority: stays regge, gains the limit
        r = discipline(_payload([_finding("N4", defense={"attempted": True, "present": True,
                                                         "fact": "a real defending fact"})]))
        f = _by_id(r.ledger)["N4"]
        self.assertEqual(f.verdict.value, "artefatto_regge")
        self.assertIn("COMPETENCE", (f.declared_limit or ""))

    def test_completeness_flag_lists_unclassified_nonmechanical_high(self):
        # an epistemic HIGH-posta finding that never declared the authority axis
        epi = _finding("E1", defect_class="epistemic", rests_on_authority=False)
        r = discipline(_payload([epi]))
        flag = [x for x in r.ledger.flags if "classify the authority axis" in x]
        self.assertTrue(flag and "E1" in flag[0])

    def test_mechanical_finding_is_never_demoted_or_flagged(self):
        # a numeric internal finding must be untouched by the competence gate
        num = _finding("M1", defect_class="numeric", rests_on_authority=False,
                       accusation={"text": "70 != 68", "base": "execution",
                                   "evidence": "X violates rule Y.", "sections": ["§1"]})
        r = discipline(_payload([num]))
        f = _by_id(r.ledger)["M1"]
        self.assertNotIn("COMPETENCE", (f.declared_limit or ""))
        self.assertFalse([x for x in r.ledger.flags
                          if "classify the authority axis" in x and "M1" in x])

    def test_gate_dormant_outside_regulated_domain_for_unclassified(self):
        # not a regulated domain → no completeness flag, but a DECLARED uncited normative
        # claim is still routed (authority dependence is suspect in any domain)
        epi = _finding("E2", defect_class="epistemic", rests_on_authority=False)
        r = discipline(_payload([epi], domain_regulated=False))
        self.assertFalse([x for x in r.ledger.flags if "classify the authority axis" in x])


if __name__ == "__main__":
    unittest.main()
