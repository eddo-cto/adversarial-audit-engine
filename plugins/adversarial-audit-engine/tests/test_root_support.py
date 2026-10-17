"""Root support (1.19) — declared common causes scored by a blind external judge; record-only.

Pins: deterministic probe with no key leakage; perfect judge -> 'sostenuta'; lenient judge (controls sustained) ->
everything downgraded to 'ipotesi'; no judgment -> 'non_verificato'; unknown members -> 'non_verificabile';
verdicts unchanged; referto_guard forbids presenting a non-sustained root as a conclusion.
"""
import json
import unittest

from aae.pipeline import discipline
from aae.referto_guard import check_referto_consistency
from aae import root_support as RS

SRC = " ".join(f"Frase numero {i} con contenuto distinto." for i in range(12))


def _f(i):
    return {"id": f"F{i:02d}", "element": f"E{i}", "taxonomy_cell": "inputs", "defect_class": "numeric",
            "posta": "low", "accusation": {"text": "t", "base": "reading",
                                            "evidence": f"Frase numero {i} con contenuto distinto.",
                                            "sections": ["§1", "§2"]},
            "defense": {"attempted": True, "present": False}, "attack": {"attempted": True, "vector": "v"},
            "cost_to_fix": "trivial", "severity": "bassa", "source_grade": 1, "declared_limit": "l"}


def _payload(**over):
    p = {"artifact_name": "t", "artifact_id": "a1", "source_text": SRC, "max_posta": "low",
         "findings": [_f(i) for i in range(12)],
         "deep_causal_roots": [{"id": "R1", "statement": "causa uno", "finding_ids": ["F00", "F01", "F02"]},
                               {"id": "R2", "statement": "causa due", "finding_ids": ["F05", "F06"]}]}
    p.update(over)
    return p


def _answers(p, root_sup="pieno", root_ok=True, ctrl_sup="assente", ctrl_ok=False):
    _, key, _ = RS._plan(p)
    out = []
    for q, k in key.items():
        if k["kind"] == "root":
            out.append({"id": q, "supporto": root_sup, "intruso": k["intruder"] if root_ok else "Z"})
        else:
            out.append({"id": q, "supporto": ctrl_sup, "intruso": k["intruder"] if ctrl_ok else "Z"})
    return out


class TestRootSupport(unittest.TestCase):

    def test_probe_deterministic_and_blind(self):
        p = _payload()
        a, b = RS.build_probe(p), RS.build_probe(p)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 4)                     # 2 roots x (root + control)
        blob = json.dumps(a)
        self.assertNotIn("control", blob)
        self.assertNotIn("R1", blob)

    def test_perfect_judge_sustains(self):
        p = _payload(); p["root_judgments"] = _answers(p)
        L = discipline(p).ledger
        self.assertEqual({r["id"]: r["label"] for r in L.root_support}, {"R1": "sostenuta", "R2": "sostenuta"})

    def test_wrong_intruder_is_hypothesis(self):
        p = _payload(); p["root_judgments"] = _answers(p, root_ok=False)
        L = discipline(p).ledger
        self.assertTrue(all(r["label"] == "ipotesi" for r in L.root_support))

    def test_lenient_judge_downgrades_all(self):
        p = _payload(); p["root_judgments"] = _answers(p, ctrl_sup="parziale", ctrl_ok=True)
        L = discipline(p).ledger
        self.assertTrue(all(r["label"] == "ipotesi" for r in L.root_support))
        self.assertTrue(any("LENIENT" in f for f in L.flags))

    def test_no_judgment_is_not_verified(self):
        L = discipline(_payload()).ledger
        self.assertTrue(all(r["label"] == "non_verificato" for r in L.root_support))

    def test_unknown_members_not_verifiable(self):
        p = _payload(deep_causal_roots=[{"id": "R9", "statement": "x", "finding_ids": ["F00", "ZZ"]}])
        L = discipline(p).ledger
        self.assertEqual(L.root_support[0]["label"], "non_verificabile")

    def test_verdicts_unchanged(self):
        p = _payload(); base = [f.verdict.value for f in discipline(dict(p, deep_causal_roots=[])).ledger.findings]
        p["root_judgments"] = _answers(p)
        self.assertEqual([f.verdict.value for f in discipline(p).ledger.findings], base)

    def test_referto_guard_roots(self):
        p = _payload(); p["root_judgments"] = _answers(p, root_ok=False)
        L = discipline(p).ledger
        v = check_referto_consistency(L, [{"root_id": "R1", "presented_as": "conclusion"}])
        self.assertTrue(any("hypothesis" in x for x in v))
        self.assertEqual(check_referto_consistency(L, [{"root_id": "R1", "presented_as": "hypothesis"}]), [])
        p2 = _payload(); p2["root_judgments"] = _answers(p2)
        L2 = discipline(p2).ledger
        self.assertEqual(check_referto_consistency(L2, [{"root_id": "R1", "presented_as": "conclusion"}]), [])

    def test_serialized(self):
        p = _payload(); p["root_judgments"] = _answers(p)
        d = json.loads(discipline(p).ledger.to_json())
        self.assertEqual(d["root_support_summary"]["sostenuta"], 2)


if __name__ == "__main__":
    unittest.main()
