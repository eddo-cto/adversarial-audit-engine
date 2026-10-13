"""1.18 — the referto may not sell a defense-only or unsettled hold as solid; ids are unique.

RN95 A/B pilot: the biggest risks (leases, roof) held on "the expert declares the limit" defenses; a referto could
present them as solid. And payloads without ids produced duplicate "<role>-?" ids, making per-finding checks ambiguous.
"""
import json
import unittest

from aae.pipeline import discipline
from aae.referto_guard import check_referto_consistency

SRC = "Il terrazzo non e' stato ispezionato in quanto la scala era pericolante."
QUOTE = "Il terrazzo non e' stato ispezionato"


def _f(fid=None, **over):
    f = {
        "element": "E", "taxonomy_cell": "inputs", "defect_class": "non_local_mechanical", "posta": "high",
        "accusation": {"text": "stato non verificato", "base": "reading", "evidence": QUOTE, "sections": ["§1", "§2"]},
        "defense": {"attempted": True, "present": True, "fact": "il perito dichiara il limite"},
        "attack": {"attempted": True, "vector": "check"},
        "cost_to_fix": "medium", "severity": "alta", "source_grade": 1, "declared_limit": "limite",
        "source_role": "verifier",
    }
    if fid:
        f["id"] = fid
    f.update(over)
    return f


def _ledger(findings):
    return discipline({"artifact_name": "t", "source_text": SRC, "evidence_base": ["perizia"],
                       "max_posta": "high", "findings": findings}).ledger


class TestRefertoGuard118(unittest.TestCase):

    def test_defense_hold_cannot_be_presented_as_solid(self):
        L = _ledger([_f("D1")])
        self.assertEqual(L.defense_holds, ["D1"])
        v = check_referto_consistency(L, [{"id": "D1", "presented_as": "holds", "presented_posta": "high"}])
        self.assertTrue(any("DEFENSE LEVER" in x and "'open'" in x for x in v))
        self.assertEqual(check_referto_consistency(L, [{"id": "D1", "presented_as": "open",
                                                        "presented_posta": "high"}]), [])

    def test_unsettled_hold_cannot_be_presented_as_solid(self):
        L = _ledger([_f("U1", posta="low", requires_docs=["foto"])])
        v = check_referto_consistency(L, [{"id": "U1", "presented_as": "holds", "presented_posta": "low"}])
        self.assertTrue(any("UNSETTLED" in x for x in v))

    def test_must_open_finding_cannot_be_omitted(self):
        L = _ledger([_f("D2"), _f("K1", defense={"attempted": True, "present": False})])
        v = check_referto_consistency(L, [{"id": "K1", "presented_as": "defect", "presented_posta": "high"}])
        self.assertTrue(any(x.startswith("D2:") and "omitted" in x for x in v))

    def test_works_on_serialized_ledger(self):
        L = _ledger([_f("D3")])
        d = json.loads(L.to_json())
        v = check_referto_consistency(d, [{"id": "D3", "presented_as": "holds", "presented_posta": "high"}])
        self.assertTrue(v)

    def test_ordinary_hold_still_presentable_as_solid(self):
        L = _ledger([_f("H1", posta="low")])
        self.assertEqual(check_referto_consistency(L, [{"id": "H1", "presented_as": "holds",
                                                        "presented_posta": "low"}]), [])

    def test_ids_unique_when_missing_or_duplicated(self):
        L = _ledger([_f(), _f(), _f("X"), _f("X")])
        ids = [f.id for f in L.findings]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("X", ids)                      # a declared unique id is kept


if __name__ == "__main__":
    unittest.main()
