"""
test_metrics_and_oracles.py — the anti-Goodhart contract, and abstention as an
honest outcome.

A metric becomes a target. The project's defence is structural: no composite
score, abstention never counted as success, coverage claims impossible without
human ground truth, and a bias_audit that flags degenerate-but-good-looking
runs. If any of that erodes, the engine starts optimising its own numbers.
"""

import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aae import run_metrics as M  # noqa: E402
from aae.legal_oracle import Citation, LegalOracle, extract_citations  # noqa: E402
from aae.evidence_pairing import pair_claim_with_evidence  # noqa: E402
from aae.repr_validator import numeric_anomalies  # noqa: E402


def panel(**verdicts):
    return M.compute([M.RunRecord(verdicts=dict(verdicts))])


class NoCompositeScore(unittest.TestCase):
    def test_the_panel_exposes_no_single_quality_number(self):
        p = panel(accusa_vince=3, conteso=2, artefatto_regge=5)
        suspicious = [f for f in vars(p)
                      if "score" in f.lower() or "quality" in f.lower()
                      or f.lower() in ("grade", "rating", "index")]
        self.assertEqual([], suspicious,
                         f"a composite number appeared: {suspicious} — it will "
                         "become the target and replace the truth")

    def test_rates_are_orthogonal_and_separately_reported(self):
        p = panel(accusa_vince=1, conteso=1, artefatto_regge=1)
        for attr in ("condemnation_rate", "absolution_rate", "abstention_rate"):
            self.assertIsNotNone(getattr(p, attr))


class AbstentionIsNeverSuccess(unittest.TestCase):
    def test_abstention_has_its_own_bucket(self):
        p = panel(conteso=10)
        self.assertAlmostEqual(1.0, p.abstention_rate, places=6)

    def test_abstaining_on_everything_earns_no_credit(self):
        p = panel(conteso=10)
        self.assertNotEqual(1.0, p.condemnation_rate)
        self.assertNotEqual(1.0, p.absolution_rate)

    def test_abstention_is_not_folded_into_absolution(self):
        p = panel(conteso=5, artefatto_regge=5)
        self.assertAlmostEqual(0.5, p.abstention_rate, places=6)
        self.assertAlmostEqual(0.5, p.absolution_rate, places=6)


class UnknownIsNotZero(unittest.TestCase):
    """Without human ground truth, coverage metrics must be None — never an
    imputed, self-serving 0 that reads as 'no defects escaped'."""

    def test_escape_precision_recall_are_none_without_ground_truth(self):
        p = panel(accusa_vince=2, artefatto_regge=2)
        self.assertIsNone(p.escape_rate)
        self.assertIsNone(p.precision)
        self.assertIsNone(p.recall)

    def test_they_become_numbers_only_with_ground_truth(self):
        p = M.compute([M.RunRecord(verdicts={"accusa_vince": 2})],
                      ground_truth=M.GroundTruth(tp=8, fp=2, fn=4, tn=10))
        self.assertIsNotNone(p.precision)
        self.assertIsNotNone(p.recall)


class BiasAudit(unittest.TestCase):
    def test_rubber_stamp_signature_is_caught(self):
        warns = " ".join(M.bias_audit(panel(artefatto_regge=100)))
        self.assertIn("TIMBRO", warns.upper())

    def test_all_abstain_signature_is_caught(self):
        warns = " ".join(M.bias_audit(panel(conteso=100)))
        self.assertIn("ASTENUT", warns.upper())

    def test_over_condemnation_signature_is_caught(self):
        warns = " ".join(M.bias_audit(panel(accusa_vince=100)))
        self.assertIn("CONDANNA", warns.upper())

    def test_missing_ground_truth_is_always_declared(self):
        warns = " ".join(M.bias_audit(panel(accusa_vince=1, artefatto_regge=1,
                                            conteso=1)))
        self.assertIn("GROUND-TRUTH", warns.upper())

    def test_empty_panel_is_declared_uninterpretable(self):
        self.assertTrue(M.bias_audit(M.compute([])))


class LegalOracleAbstains(unittest.TestCase):
    """Anti-hallucination by construction: no official source, no assertion."""

    def test_without_a_fetcher_it_asserts_nothing(self):
        r = LegalOracle().verify(Citation(raw="art. 36-bis DPR 380/2001",
                                          article="36-bis"), "afferma X")
        self.assertEqual("no_source", r.status)
        self.assertIsNone(r.exists)
        self.assertIsNone(r.faithful)

    def test_a_failing_fetcher_abstains_instead_of_guessing(self):
        def broken(_citation):
            raise RuntimeError("Normattiva ha bloccato l'accesso")

        r = LegalOracle(fetcher=broken).verify(
            Citation(raw="art. 1 L. 1/1990", article="1"), "afferma X")
        self.assertEqual("unverified", r.status)
        self.assertIsNone(r.faithful)

    def test_an_empty_fetch_abstains(self):
        r = LegalOracle(fetcher=lambda c: None).verify(
            Citation(raw="art. 1", article="1"), "afferma X")
        self.assertEqual("unverified", r.status)

    def test_fidelity_is_checked_verbatim_against_the_official_text(self):
        norm = ("Art. 1. Il termine per la presentazione e' di trenta giorni "
                "dalla notifica.")
        oracle = LegalOracle(fetcher=lambda c: norm)
        good = oracle.verify(Citation(raw="art. 1", article="1"),
                             "il termine per la presentazione e' di trenta giorni")
        bad = oracle.verify(Citation(raw="art. 1", article="1"),
                            "il termine per la presentazione e' di sessanta giorni")
        self.assertEqual("verified", good.status)
        self.assertTrue(good.faithful)
        self.assertFalse(bad.faithful, "a misquoted norm must not pass as faithful")

    def test_citations_are_extracted_from_free_text(self):
        found = extract_citations("Si richiama l'art. 36-bis del DPR 380/2001.")
        self.assertTrue(found)


class DeterministicAids(unittest.TestCase):
    def test_evidence_pairing_surfaces_the_contradicting_passage(self):
        """Cue-locality: the disconfirming fact must be brought NEXT TO the
        claim, because detection collapses when it is far away."""
        source = (
            "Il progetto adotta un sistema di raffreddamento passivo. " +
            "Testo irrilevante di riempimento. " * 40 +
            "Tuttavia il sistema di raffreddamento passivo non e' stato "
            "certificato per il carico dichiarato."
        )
        passages = pair_claim_with_evidence(
            "il sistema di raffreddamento passivo e' certificato", source, k=3)
        self.assertTrue(passages)
        self.assertTrue(any(p.contradiction_hint for p in passages),
                        "the contradicting passage must be retrieved")

    def test_repr_validator_flags_a_gross_outlier(self):
        anomalies = numeric_anomalies([10, 11, 12, 11, 10, 9999, 12])
        outlier = [a for a in anomalies if a.value == 9999]
        self.assertTrue(outlier)
        self.assertTrue(any("outlier" in k for k in outlier[0].kinds))
        self.assertGreater(outlier[0].score, 90)

    def test_repr_validator_emits_a_signal_not_a_verdict(self):
        for a in numeric_anomalies([1, 2, 3, 400]):
            self.assertGreaterEqual(a.score, 0.0)
            self.assertLessEqual(a.score, 100.0)
            self.assertFalse(hasattr(a, "verdict"),
                             "a detection aid must not emit verdicts")


class UsageLedgerPathIsRelocatable(unittest.TestCase):
    """The run-log must be able to live outside the package dir: a plugin
    install directory can be read-only, and data must not mix with code. The
    env var relocates it; absence falls back to the in-package path. Read at
    import, so a subprocess is the honest test (module env is read once)."""

    _PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _default_path(self, env):
        e = dict(os.environ)
        e.pop("AAE_USAGE_LEDGER", None)
        e.update(env)
        e["PYTHONPATH"] = self._PKG
        out = subprocess.run(
            [sys.executable, "-c",
             "import aae.usage_ledger as ul; print(ul.DEFAULT_PATH)"],
            capture_output=True, text=True, env=e,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout.strip()

    def test_env_var_relocates_the_ledger(self):
        self.assertEqual(
            self._default_path({"AAE_USAGE_LEDGER": "/tmp/aae_ledger_test.jsonl"}),
            "/tmp/aae_ledger_test.jsonl")

    def test_absent_env_var_falls_back_into_the_package(self):
        p = self._default_path({})
        self.assertTrue(p.endswith(os.path.join("aae", "usage_ledger.jsonl")))


if __name__ == "__main__":
    unittest.main()
