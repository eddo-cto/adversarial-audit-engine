"""
test_belnap_coverage.py — the 4-valued (Belnap) coverage recovery (round 19).

Pins that the ledger recovers the two coverage states a boolean view collapses:
F (excluded-with-justification) and B (a conflict is present), alongside T
(covered) and N (silent). Record-only: computed from fields the ledger already
carries, never feeding a verdict.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aae.schema import (Ledger, Finding, Accusation, Defense, DefectClass,  # noqa: E402
                        EvidenceBase, Posta, TemporalStatus)
from aae.source_grade import belnap_coverage  # noqa: E402


def _f(cell, fid="F", **kw) -> Finding:
    base = dict(
        id=fid, element=f"elem in {cell}", taxonomy_cell=cell,
        defect_class=DefectClass.IDIOSYNCRATIC_LOCAL, posta=Posta.MEDIUM,
        accusation=Accusation(text="x", base=EvidenceBase.READING),
        defense=Defense(attempted=True), action="fix",
    )
    base.update(kw)
    return Finding(**base)


class TestBelnapCoverage(unittest.TestCase):
    def test_four_states_present(self):
        led = Ledger(artifact_name="t")
        led.findings = [
            _f("mechanisms", "F1"),                       # T
            _f("premises", "F2", temporal_status=TemporalStatus.CONFLICTED,
               conflict_with=["ck_x"]),                   # B (precedence over T)
        ]
        led.excluded_cells = {"inputs": "not applicable to this artifact"}  # F
        # outputs, boundary, interface -> N
        bc = belnap_coverage(led)
        pc = bc["per_cell"]
        self.assertEqual(pc["mechanisms"], "T")
        self.assertEqual(pc["premises"], "B")
        self.assertEqual(pc["inputs"], "F")
        self.assertEqual(pc["outputs"], "N")
        self.assertEqual(pc["boundary"], "N")
        self.assertEqual(pc["interface"], "N")

    def test_counts_sum_to_six(self):
        led = Ledger(artifact_name="t")
        led.findings = [_f("mechanisms", "F1")]
        bc = belnap_coverage(led)
        self.assertEqual(sum(bc["counts"].values()), 6)
        self.assertEqual(bc["counts"]["T"], 1)
        self.assertEqual(bc["counts"]["N"], 5)

    def test_conflict_beats_covered(self):
        """B is more informative than T: a covered cell that also carries a
        conflict must read B, not T."""
        led = Ledger(artifact_name="t")
        led.findings = [
            _f("mechanisms", "F1"),                                   # plain covered
            _f("mechanisms", "F2", temporal_status=TemporalStatus.CONFLICTED,
               conflict_with=["ck_y"]),                               # conflict same cell
        ]
        self.assertEqual(belnap_coverage(led)["per_cell"]["mechanisms"], "B")

    def test_excluded_only_is_F_not_N(self):
        led = Ledger(artifact_name="t")
        led.excluded_cells = {"boundary": "no failure modes in scope"}
        self.assertEqual(belnap_coverage(led)["per_cell"]["boundary"], "F")

    def test_recovers_share_lost_by_boolean(self):
        """The whole point: F and B are NOT collapsed to the same bucket as N."""
        led = Ledger(artifact_name="t")
        led.findings = [_f("mechanisms", "F1")]
        led.excluded_cells = {"inputs": "j", "outputs": "j"}
        c = belnap_coverage(led)["counts"]
        self.assertEqual(c["F"], 2)          # excluded, not silent
        self.assertEqual(c["N"], 3)          # premises, boundary, interface
        self.assertEqual(c["T"], 1)


if __name__ == "__main__":
    unittest.main()
