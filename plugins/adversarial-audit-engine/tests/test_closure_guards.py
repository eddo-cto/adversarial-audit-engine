"""Closure guards (1.17) — the "defend everything" escape.

Real A/B runs (RN95): two of four runs held 17-18/18 findings with defenses of the form "the expert declares the
limit"; one was promoted to CROSS_MODEL_REVIEWED with nothing left for the human. Pins: a hold that admits a
missing document does not count as closed; an all-held HIGH-stakes run is blocked; small/low-stakes runs are not;
verdicts never change; the defense lever lists HIGH-posta holds that rest only on the auditor's own defense.
"""
import os
import unittest

from aae.pipeline import discipline

SRC = "Il terrazzo non e' stato ispezionato in quanto la scala era pericolante."
QUOTE = "Il terrazzo non e' stato ispezionato"


def _f(fid, **over):
    f = {
        "id": fid, "element": "E-" + fid, "taxonomy_cell": "inputs",
        "defect_class": "non_local_mechanical", "posta": "high",
        "accusation": {"text": "stato non verificato", "base": "reading",
                       "evidence": QUOTE, "sections": ["§1", "§2"]},
        "defense": {"attempted": True, "present": True, "fact": "il perito dichiara il limite"},
        "attack": {"attempted": True, "vector": "check"},
        "cost_to_fix": "medium", "severity": "alta", "source_grade": 1, "declared_limit": "limite",
    }
    f.update(over)
    return f


def _disc(fid):
    return _f(fid, action_state="deliberately_discarded", posta="low",
              discard_justification="irrilevante")


def _run(findings, **over):
    p = {"artifact_name": "t", "source_text": SRC, "evidence_base": ["perizia"], "max_posta": "high",
         "findings": findings}
    p.update(over)
    os.environ.pop("AAE_EXTERNAL_ATTESTED_IDENTITY", None)
    return discipline(p)


class TestClosureGuards(unittest.TestCase):

    def test_hold_with_missing_document_blocks_closure(self):
        fs = [_f("U1", requires_docs=["foto"]), _f("C1", defense={"attempted": True, "present": False}), _disc("X1")]
        r = _run(fs)
        self.assertEqual(r.completion.state, "BLOCKED_OPEN_ITEMS")
        self.assertIn("UNSETTLED", r.completion.reason)
        self.assertEqual({f.id: f.verdict.value for f in r.ledger.findings}["U1"], "artefatto_regge")

    def test_hold_with_satisfied_document_does_not_block(self):
        fs = [_f("U2", requires_docs=["perizia"]), _f("C2", defense={"attempted": True, "present": False}), _disc("X2")]
        r = _run(fs)
        self.assertNotIn("UNSETTLED", r.completion.reason)

    def test_all_held_high_stakes_blocks(self):
        fs = [_f(f"H{i}") for i in range(5)] + [_disc("X3")]
        r = _run(fs)
        self.assertEqual(r.completion.state, "BLOCKED_OPEN_ITEMS")
        self.assertIn("ALL-HELD", r.completion.reason)
        self.assertTrue(all(f.verdict.value == "artefatto_regge" for f in r.ledger.findings))

    def test_all_held_below_threshold_or_low_stakes_not_blocked_by_guard(self):
        r = _run([_f(f"S{i}") for i in range(4)] + [_disc("X4")])
        self.assertNotIn("ALL-HELD", r.completion.reason)
        r2 = _run([_f(f"L{i}", posta="low") for i in range(6)] + [_disc("X5")], max_posta="low")
        self.assertNotIn("ALL-HELD", r2.completion.reason)

    def test_one_condemnation_lifts_all_held_guard(self):
        fs = [_f(f"H{i}") for i in range(5)] + [_f("C3", defense={"attempted": True, "present": False}), _disc("X6")]
        r = _run(fs)
        self.assertNotIn("ALL-HELD", r.completion.reason)

    def test_defense_lever_lists_high_posta_holds(self):
        r = _run([_f("D1"), _f("D2", posta="low"), _disc("X7")])
        self.assertEqual(r.ledger.defense_holds, ["D1"])
        self.assertTrue(any(x.startswith("DEFENSE LEVER") for x in r.ledger.flags))

    def test_defense_lever_respects_grounding(self):
        bad = _f("D3")
        bad["accusation"] = dict(bad["accusation"], evidence="frase assente dalla fonte")
        r = _run([bad, _disc("X8")])
        self.assertEqual(r.ledger.defense_holds, [])


if __name__ == "__main__":
    unittest.main()
