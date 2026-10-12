"""Routing sentinel (1.16) — expose condemnations avoided ONLY by a self-declared lever.

Pins: a requires_docs/source_grade routing that alone avoids a condemnation is recorded; content gates
(defense, competence, grounding) are kept in the counterfactual; a held finding or a satisfied evidence
base yields no delta; no verdict is ever changed; the field serializes. Born from the real run
R.G.E. 95/2025 (0 -> 5 condemnations once the levers were removed).
"""
import json
import unittest

from aae.pipeline import discipline

SRC = "Gli oneri totali sono pari a euro 9.900 per spese tecniche e diritti."
QUOTE = "Gli oneri totali sono pari a euro 9.900"


def _f(fid, **over):
    f = {
        "id": fid, "element": "E-" + fid, "taxonomy_cell": "inputs",
        "defect_class": "non_local_mechanical", "posta": "medium",
        "accusation": {"text": "oneri incompleti", "base": "reading",
                       "evidence": QUOTE, "sections": ["§1", "§2"]},
        "defense": {"attempted": True, "present": False},
        "attack": {"attempted": True, "vector": "check"},
        "cost_to_fix": "medium", "severity": "media", "source_grade": 1,
        "declared_limit": "stima",
    }
    f.update(over)
    return f


def _run(findings, **over):
    p = {"artifact_name": "t", "source_text": SRC, "evidence_base": ["perizia"], "findings": findings}
    p.update(over)
    return discipline(p).ledger


def _delta_ids(ledger):
    return [d["id"] for d in ledger.routing_delta]


class TestRoutingSentinel(unittest.TestCase):

    def test_requires_docs_alone_avoiding_condemnation_is_recorded(self):
        L = _run([_f("R1", requires_docs=["planimetria"])])
        f = L.findings[0]
        self.assertEqual(f.verdict.value, "conteso")                 # verdict unchanged by the sentinel
        self.assertEqual(_delta_ids(L), ["R1"])
        d = L.routing_delta[0]
        self.assertEqual(d["counterfactual"], "accusa_vince")
        self.assertIn("requires_docs=planimetria", d["levers"])
        self.assertTrue(any(x.startswith("ROUTING SENTINEL") for x in L.flags))

    def test_source_grade_lever_recorded_only_when_primary_reachable(self):
        L = _run([_f("G1", source_grade=2)])
        self.assertEqual(L.findings[0].verdict.value, "da_leggere")
        self.assertEqual(_delta_ids(L), ["G1"])
        L2 = _run([_f("G2", source_grade=2)], source_primary_reachable=False)
        self.assertEqual(_delta_ids(L2), [])

    def test_satisfied_evidence_base_is_not_a_lever(self):
        L = _run([_f("R2", requires_docs=["perizia"])])
        self.assertEqual(_delta_ids(L), [])

    def test_held_finding_never_in_delta(self):
        L = _run([_f("H1", requires_docs=["planimetria"],
                     defense={"attempted": True, "present": True, "fact": "la tabella lo dichiara"})])
        self.assertEqual(L.findings[0].verdict.value, "artefatto_regge")
        self.assertEqual(_delta_ids(L), [])

    def test_competence_gate_kept_in_counterfactual(self):
        # normative without a cited norm would be routed anyway -> the lever is not the cause
        L = _run([_f("C1", requires_docs=["planimetria"], defect_class="normative",
                     rests_on_authority=True)])
        self.assertEqual(_delta_ids(L), [])
        L2 = _run([_f("C2", requires_docs=["planimetria"], defect_class="normative",
                      rests_on_authority=True, authority_cited="art. 46 DPR 380/2001")])
        self.assertEqual(_delta_ids(L2), ["C2"])

    def test_grounding_kept_in_counterfactual(self):
        bad = _f("Q1", requires_docs=["planimetria"])
        bad["accusation"] = dict(bad["accusation"], evidence="frase che non compare nella fonte")
        L = _run([bad])
        self.assertEqual(_delta_ids(L), [])

    def test_no_defense_attempt_is_not_a_lever(self):
        L = _run([_f("D1", requires_docs=["planimetria"], defense={"attempted": False, "present": False})])
        self.assertEqual(_delta_ids(L), [])

    def test_trivial_cost_counterfactual_is_reduced(self):
        L = _run([_f("T1", requires_docs=["ordinanza"], cost_to_fix="trivial")])
        self.assertEqual(L.routing_delta[0]["counterfactual"], "accusa_ridimensionata")

    def test_verdicts_identical_with_and_without_sentinel_inputs(self):
        fs = [_f("A1", requires_docs=["x"]), _f("A2", source_grade=3), _f("A3")]
        L = _run(fs)
        self.assertEqual([f.verdict.value for f in L.findings],
                         ["conteso", "da_leggere", "accusa_vince"])

    def test_serialized(self):
        L = _run([_f("S1", requires_docs=["planimetria"])])
        d = json.loads(L.to_json())
        self.assertEqual(d["routing_delta"][0]["id"], "S1")
        L0 = _run([_f("S2")])
        self.assertEqual(json.loads(L0.to_json())["routing_delta"], [])


if __name__ == "__main__":
    unittest.main()
