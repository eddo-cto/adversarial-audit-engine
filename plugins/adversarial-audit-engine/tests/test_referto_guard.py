"""referto_guard — the prose may not overstate the ledger (the CTU narrator bug)."""
import unittest

from aae.referto_guard import check_referto_consistency

# a tiny ledger-as-dicts, mirroring the CTU case verdicts
LEDGER = {"findings": [
    {"id": "F01", "verdict": "artefatto_regge", "posta": "high"},   # holds (material error, but holds)
    {"id": "F02", "verdict": "da_leggere", "posta": "high"},        # real coherence point
    {"id": "F03", "verdict": "conteso", "posta": "high"},           # routed to expert
    {"id": "F05", "verdict": "artefatto_regge", "posta": "high"},   # HOLDS — the false-positive one
]}


class TestRefertoGuard(unittest.TestCase):

    def test_consistent_referto_passes(self):
        manifest = [
            {"id": "F02", "presented_as": "defect", "presented_posta": "high"},
            {"id": "F05", "presented_as": "holds", "presented_posta": "medium"},
            {"id": "F03", "presented_as": "open", "presented_posta": "high"},
        ]
        self.assertEqual(check_referto_consistency(LEDGER, manifest), [])

    def test_holds_presented_as_defect_is_caught(self):
        # the exact CTU bug: F05 holds, but written up as a high-posta exposure
        bad = [{"id": "F05", "presented_as": "defect", "presented_posta": "high"}]
        v = check_referto_consistency(LEDGER, bad)
        self.assertTrue(any("F05" in x and "overstated" in x for x in v))

    def test_conteso_presented_as_defect_is_caught(self):
        bad = [{"id": "F03", "presented_as": "defect", "presented_posta": "high"}]
        v = check_referto_consistency(LEDGER, bad)
        self.assertTrue(any("F03" in x for x in v))

    def test_posta_inflation_is_caught(self):
        led = {"findings": [{"id": "X", "verdict": "da_leggere", "posta": "low"}]}
        bad = [{"id": "X", "presented_as": "defect", "presented_posta": "high"}]
        v = check_referto_consistency(led, bad)
        self.assertTrue(any("inflated" in x for x in v))

    def test_invented_finding_is_caught(self):
        v = check_referto_consistency(LEDGER, [{"id": "Z99", "presented_as": "defect"}])
        self.assertTrue(any("Z99" in x and "absent" in x for x in v))

    def test_accepts_ledger_object(self):
        from aae.pipeline import discipline
        r = discipline({"artifact_name": "t", "findings": [{
            "id": "A1", "element": "e", "taxonomy_cell": "outputs", "defect_class": "numeric",
            "posta": "low", "accusation": {"text": "t", "base": "execution", "evidence": "e",
                                           "sections": ["§1"]},
            "defense": {"attempted": True, "present": True, "fact": "f"},
            "attack": {"attempted": True, "vector": "v"}}]})
        # presenting a 'low holds' as 'holds/low' is fine
        self.assertEqual(check_referto_consistency(
            r.ledger, [{"id": "A1", "presented_as": "holds", "presented_posta": "low"}]), [])


if __name__ == "__main__":
    unittest.main()
