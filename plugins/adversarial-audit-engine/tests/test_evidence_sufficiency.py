"""
test_evidence_sufficiency.py — the evidence-sufficiency gate (round 22 / Villalta).

A finding may not be ASSERTED on a document it does not have. Pins:
  1. a CONDEMNING finding whose requires_docs are absent from evidence_base is forced
     to NEEDS_EXPERT, and its declared limit names the missing documents;
  2. the SAME finding, once the required document is in evidence_base, is left alone;
  3. an artefact that HOLDS is never touched (needing an absent doc bars condemnation,
     not absolution);
  4. it runs end-to-end through the shared pipeline from a JSON payload.
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

from aae.schema import (Ledger, Finding, Accusation, Defense, Verdict, Posta,
                        DefectClass, EvidenceBase)                     # noqa: E402
from aae.gates import enforce_evidence_sufficiency_gate                # noqa: E402
from aae import pipeline                                               # noqa: E402


def _finding(verdict, requires, fid="F-x"):
    f = Finding(
        id=fid, element="anomalia patrimoniale dal conferimento 2024",
        taxonomy_cell="mechanisms", defect_class=DefectClass.NON_LOCAL_MECHANICAL,
        posta=Posta.HIGH,
        accusation=Accusation(text="effetto patrimoniale dell'operazione",
                              base=EvidenceBase.DOMAIN_KNOWLEDGE, evidence="x",
                              sections=["visura", "bilancio"]),
        defense=Defense(attempted=True, present=False, fact=None),
    )
    f.verdict = verdict
    f.requires_docs = requires
    return f


class TestEvidenceSufficiencyGate(unittest.TestCase):
    def test_missing_doc_forces_condemnation_to_expert(self):
        led = Ledger(artifact_name="fascicolo")
        led.evidence_base = ["bilancio_2025", "visura_2026"]
        f = _finding(Verdict.ARTIFACT_DEFECTIVE, ["bilancio_2023_comparativo", "atto_conferimento"])
        led.add(f)
        notes = enforce_evidence_sufficiency_gate(led)
        self.assertEqual(f.verdict, Verdict.NEEDS_EXPERT)
        self.assertIn("bilancio_2023_comparativo", f.declared_limit)
        self.assertIn("atto_conferimento", f.declared_limit)
        self.assertTrue(notes)

    def test_reduced_verdict_also_forced(self):
        led = Ledger(artifact_name="f")
        led.evidence_base = ["bilancio_2025"]
        f = _finding(Verdict.REDUCED, ["dichiarazioni_IVA"])
        led.add(f)
        enforce_evidence_sufficiency_gate(led)
        self.assertEqual(f.verdict, Verdict.NEEDS_EXPERT)

    def test_present_doc_leaves_finding_untouched(self):
        led = Ledger(artifact_name="f")
        led.evidence_base = ["bilancio_2023_comparativo", "atto_conferimento"]
        f = _finding(Verdict.ARTIFACT_DEFECTIVE, ["bilancio_2023_comparativo", "atto_conferimento"])
        led.add(f)
        enforce_evidence_sufficiency_gate(led)
        self.assertEqual(f.verdict, Verdict.ARTIFACT_DEFECTIVE)
        self.assertIsNone(f.declared_limit)

    def test_holding_artifact_is_never_touched(self):
        led = Ledger(artifact_name="f")
        led.evidence_base = []
        f = _finding(Verdict.ARTIFACT_HOLDS, ["anything"])
        led.add(f)
        enforce_evidence_sufficiency_gate(led)
        self.assertEqual(f.verdict, Verdict.ARTIFACT_HOLDS)

    def test_case_insensitive_and_whitespace(self):
        led = Ledger(artifact_name="f")
        led.evidence_base = ["  Bilancio_2025 "]
        f = _finding(Verdict.ARTIFACT_DEFECTIVE, ["bilancio_2025"])
        led.add(f)
        enforce_evidence_sufficiency_gate(led)
        self.assertEqual(f.verdict, Verdict.ARTIFACT_DEFECTIVE)  # matched despite case/space

    def test_end_to_end_through_pipeline(self):
        payload = {
            "artifact_name": "fascicolo Villalta",
            "internal_identity": "anthropic:claude-x",
            "max_posta": "high",
            "evidence_base": ["bilancio_2025", "visura_2026"],
            "excluded_cells": {c: "n/a" for c in
                               ("premises", "inputs", "mechanisms", "outputs", "boundary", "interface")},
            "findings": [{
                "source_role": "reasoner", "element": "anomalia patrimoniale conferimento 2024",
                "taxonomy_cell": "mechanisms", "defect_class": "non_local_mechanical", "posta": "high",
                "accusation": {"text": "effetto patrimoniale", "base": "domain_knowledge",
                               "evidence": "conferimento in visura; nessuna partecipazione in bilancio",
                               "sections": ["visura", "bilancio"]},
                "defense": {"attempted": True, "present": False, "fact": None},
                "action": "ricostruire l'operazione",
                "requires_docs": ["bilancio_2023_comparativo", "atto_conferimento"],
            }],
        }
        result = pipeline.discipline(payload)
        f = result.ledger.findings[0]
        self.assertEqual(f.verdict, Verdict.NEEDS_EXPERT)
        self.assertIn("EVIDENCE-BASE", (f.declared_limit or ""))
        self.assertTrue(any("EVIDENCE-BASE" in fl for fl in result.ledger.flags))


if __name__ == "__main__":
    unittest.main()
