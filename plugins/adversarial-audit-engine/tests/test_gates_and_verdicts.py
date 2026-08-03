"""
test_gates_and_verdicts.py — the discipline that lives in CODE, not in prompts.

These are the invariants the project says it enforces in software precisely so
an agent cannot talk its way around them. If any of these assertions can be
made to fail, the engine's central claim fails with it.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aae.schema import (Accusation, Defense, DefectClass, EvidenceBase,  # noqa: E402
                        Finding, Ledger, Posta, Verdict, IndependenceLevel)
from aae.gates import (enforce_coverage_gate, enforce_defense_gate,  # noqa: E402
                       evaluate_completion)
from aae.triage import TAXONOMY  # noqa: E402
from aae.adapters import independence_level_between  # noqa: E402


def make_finding(fid="F-1", base=EvidenceBase.READING,
                 defect_class=DefectClass.NUMERIC, cell="outputs",
                 attempted=True, present=False, fact=None,
                 posta=Posta.HIGH):
    return Finding(
        id=fid, element="totale", taxonomy_cell=cell,
        defect_class=defect_class, posta=posta,
        accusation=Accusation(text="il totale non riconcilia", base=base,
                              evidence="121000+4500+52000 != 175000",
                              sections=["§3", "§5"]),
        defense=Defense(attempted=attempted, present=present, fact=fact),
    )


class VerdictStateMachine(unittest.TestCase):
    """A verdict is a state machine, not a free label."""

    def test_pattern_evidence_can_flag_but_never_condemn(self):
        f = make_finding(base=EvidenceBase.PATTERN)
        self.assertEqual(Verdict.NEEDS_READING, f.adjudicate())

    def test_pattern_cannot_condemn_even_with_defense_attempted(self):
        f = make_finding(base=EvidenceBase.PATTERN, attempted=True)
        self.assertNotEqual(Verdict.ARTIFACT_DEFECTIVE, f.adjudicate())

    def test_conceptual_novel_is_routed_to_a_human(self):
        f = make_finding(defect_class=DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL)
        self.assertEqual(Verdict.NEEDS_EXPERT, f.adjudicate())

    def test_a_verifiable_defending_fact_makes_the_artifact_hold(self):
        f = make_finding(present=True, fact="la §5 usa un altro denominatore, dichiarato")
        self.assertEqual(Verdict.ARTIFACT_HOLDS, f.adjudicate())

    def test_condemnation_requires_an_attempted_defense(self):
        """The defense-gate: the single mechanism credited with ~0 false
        positives across four rounds."""
        f = make_finding(attempted=False)
        self.assertEqual(Verdict.NEEDS_EXPERT, f.adjudicate())

    def test_solid_base_plus_failed_defense_condemns(self):
        for base in (EvidenceBase.READING, EvidenceBase.EXECUTION,
                     EvidenceBase.DOMAIN_KNOWLEDGE):
            with self.subTest(base=base):
                f = make_finding(base=base, attempted=True, present=False)
                self.assertEqual(Verdict.ARTIFACT_DEFECTIVE, f.adjudicate())

    def test_adjudicate_is_pure(self):
        """Same fields in, same verdict out, every time."""
        f = make_finding()
        self.assertEqual(f.adjudicate(), f.adjudicate())


class DefenseGate(unittest.TestCase):
    def test_condemnation_without_defense_is_downgraded_at_ledger_level(self):
        led = Ledger(artifact_name="x")
        f = make_finding(attempted=False)
        f.verdict = Verdict.ARTIFACT_DEFECTIVE  # smuggled in past adjudication
        led.add(f)
        notes = enforce_defense_gate(led)
        self.assertEqual(Verdict.NEEDS_EXPERT, led.findings[0].verdict,
                         "a condemnation with no recorded defense must not survive")
        self.assertTrue(notes)


class CoverageGate(unittest.TestCase):
    def test_uncovered_dimension_raises_a_flag(self):
        led = Ledger(artifact_name="x")
        led.add(make_finding(cell="outputs"))
        enforce_coverage_gate(led)
        uncovered = [d for d in TAXONOMY if d != "outputs"]
        for dim in uncovered:
            self.assertTrue(any(dim in fl for fl in led.flags),
                            f"dimension '{dim}' was neither covered nor flagged")

    def test_explicit_exclusion_silences_the_flag(self):
        led = Ledger(artifact_name="x", excluded_cells={d: "fuori perimetro"
                                                        for d in TAXONOMY
                                                        if d != "outputs"})
        led.add(make_finding(cell="outputs"))
        enforce_coverage_gate(led)
        self.assertEqual([], led.flags,
                         "exclusion WITH justification is a legitimate answer")


class NeverValidatedInternally(unittest.TestCase):
    """The red line of the whole project."""

    def _clean_ledger(self):
        led = Ledger(artifact_name="x",
                     excluded_cells={d: "fuori perimetro" for d in TAXONOMY})
        f = make_finding()
        f.adjudicate()
        led.add(f)
        return led

    def test_no_external_eye_never_yields_validated(self):
        st = evaluate_completion(self._clean_ledger(), max_posta=Posta.HIGH,
                                 external_identity=None,
                                 internal_identity="anthropic:claude")
        self.assertNotEqual("VALIDATED", st.state)
        self.assertEqual("EXTERNAL_REVIEW_PENDING", st.state)

    def test_low_stakes_still_never_yields_validated_internally(self):
        st = evaluate_completion(self._clean_ledger(), max_posta=Posta.LOW,
                                 external_identity=None,
                                 internal_identity="anthropic:claude")
        self.assertNotEqual("VALIDATED", st.state)

    def test_same_identity_does_not_count_as_external(self):
        st = evaluate_completion(self._clean_ledger(), max_posta=Posta.HIGH,
                                 external_identity="anthropic:claude",
                                 internal_identity="anthropic:claude")
        self.assertNotEqual("VALIDATED", st.state)

    def test_different_vendor_raises_independence_but_not_to_validated(self):
        st = evaluate_completion(self._clean_ledger(), max_posta=Posta.HIGH,
                                 external_identity="google:gemini-1.5-flash",
                                 internal_identity="anthropic:claude")
        self.assertEqual("CROSS_MODEL_REVIEWED", st.state)
        self.assertNotEqual("VALIDATED", st.state)

    def test_only_a_human_validates_via_out_of_band_attestation(self):
        led = self._clean_ledger()
        st = evaluate_completion(led, max_posta=Posta.HIGH,
                                 external_identity=None,
                                 internal_identity="anthropic:claude",
                                 human_attestation="perito estimatore")
        self.assertEqual("VALIDATED", st.state)
        self.assertEqual(IndependenceLevel.HUMAN_DOMAIN_EXPERT,
                         led.independence_level)

    def test_human_string_in_payload_does_NOT_validate(self):
        # F-HUMAN regression: the model authors external_identity, so a string
        # beginning with 'human' must never be enough for VALIDATED.
        for spoof in ("human:perito", "human", "humanoid-model-v2", "HUMAN reviewer"):
            led = self._clean_ledger()
            st = evaluate_completion(led, max_posta=Posta.HIGH,
                                     external_identity=spoof,
                                     internal_identity="anthropic:claude")
            self.assertNotEqual("VALIDATED", st.state,
                                f"{spoof!r} must not reach VALIDATED")

    def test_same_vendor_is_intra_vendor_not_cross_model(self):
        # F-VENDOR regression: a same-vendor different model is level 2, not the
        # cross-vendor claim, and never VALIDATED.
        led = self._clean_ledger()
        st = evaluate_completion(led, max_posta=Posta.HIGH,
                                 external_identity="anthropic:claude-sonnet-4",
                                 internal_identity="anthropic:claude-opus-4")
        self.assertEqual("INTRA_VENDOR_REVIEWED", st.state)
        self.assertNotEqual("CROSS_MODEL_REVIEWED", st.state)
        self.assertNotEqual("VALIDATED", st.state)
        self.assertEqual(IndependenceLevel.DIFFERENT_MODEL_SAME_VENDOR,
                         led.independence_level)

    def test_bare_token_is_not_counted_as_a_cross_model_reviewer(self):
        # F-VENDOR regression: 'x' is not a well-formed vendor:model identity.
        led = self._clean_ledger()
        st = evaluate_completion(led, max_posta=Posta.HIGH,
                                 external_identity="x",
                                 internal_identity="anthropic:claude")
        self.assertEqual("EXTERNAL_REVIEW_PENDING", st.state)
        self.assertEqual(IndependenceLevel.SAME_INSTANCE_ROLES,
                         led.independence_level)

    def test_open_blockers_beat_everything_including_a_human(self):
        led = Ledger(artifact_name="x",
                     excluded_cells={d: "fuori perimetro" for d in TAXONOMY})
        f = make_finding(defect_class=DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL)
        f.adjudicate()
        led.add(f)
        st = evaluate_completion(led, max_posta=Posta.HIGH,
                                 external_identity="human:esperto",
                                 internal_identity="anthropic:claude")
        self.assertEqual("BLOCKED_OPEN_ITEMS", st.state)


class IndependenceScale(unittest.TestCase):
    def test_same_identity_is_level_1(self):
        self.assertEqual(IndependenceLevel.SAME_INSTANCE_ROLES,
                         independence_level_between("anthropic:opus", "anthropic:opus"))

    def test_same_vendor_different_model_is_level_2(self):
        self.assertEqual(IndependenceLevel.DIFFERENT_MODEL_SAME_VENDOR,
                         independence_level_between("anthropic:opus", "anthropic:haiku"))

    def test_different_vendor_is_level_3(self):
        self.assertEqual(IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR,
                         independence_level_between("anthropic:opus", "openai:gpt-5"))

    def test_missing_counterpart_is_level_1_not_an_error(self):
        self.assertEqual(IndependenceLevel.SAME_INSTANCE_ROLES,
                         independence_level_between("anthropic:opus", None))

    def test_level_4_is_never_reachable_from_two_machine_identities(self):
        for a, b in [("anthropic:opus", "openai:gpt-5"),
                     ("google:gemini", "groq:llama")]:
            self.assertLess(int(independence_level_between(a, b)),
                            int(IndependenceLevel.HUMAN_DOMAIN_EXPERT))


if __name__ == "__main__":
    unittest.main()
