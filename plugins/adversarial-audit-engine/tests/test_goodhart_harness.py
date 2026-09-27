"""
test_goodhart_harness.py — the adversarial-loop RUNNER, tested end-to-end with deterministic mocks.

Pins:
  1. the runner wires forger -> gold -> auditor -> tuples, and the tuples feed analysis.py to a decision;
  2. ANTI-LEAK invariant: the forger's feedback carries ONLY the auditor verdict, never the gold label;
  3. tuples are well-formed (keys, gold vocab, bool cleared);
  4. with mock defences that genuinely cut escape, the full pipeline yields H1_CONFIRMED and H2_CONFIRMED
     — proving the plumbing (runner + analysis) is correct in isolation from real LLM components.
"""
import os
import random
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "goodhart"))

import analysis as A          # noqa: E402
import harness as H           # noqa: E402


class MockGold:
    """Independent ground truth: an artefact is INVALID iff it was built invalid. Ignores evasion."""
    def label(self, art):
        return "INVALID" if art["truly_invalid"] else "VALID"


class MockForger:
    """Adaptive attacker (mock): higher pressure -> higher evasion. ~90% of artefacts are truly invalid
    (it is trying to sneak invalids through). Deterministic per seed."""
    def __init__(self, seed=0):
        self.rnd = random.Random(seed)

    def forge(self, pressure, feedback):
        return {"truly_invalid": self.rnd.random() < 0.9,
                "evasion": min(1.0, 0.1 + 0.10 * pressure)}


class MockAuditor:
    """Escape happens iff an INVALID artefact's evasion clears the auditor's catch-power. Stronger
    defences -> higher catch-power -> fewer escapes. Cross-seed is a weaker placebo (herding)."""
    def _catch_power(self, cell: "H.AblationCell") -> float:
        if not (cell.eye or cell.axes or cell.governor):
            return 0.15                      # defences off: easy to escape
        if cell.eye_mode == "cross_seed":
            return 0.55                      # placebo: helps some, but herding
        return 0.95                          # defences on / cross-vendor: hard to escape

    def audit(self, art, cell) -> bool:
        if not art["truly_invalid"]:
            return True                      # a valid artefact is correctly cleared
        return art["evasion"] >= self._catch_power(cell)   # cleared == escaped


class SpyForger(MockForger):
    def __init__(self, seed=0):
        super().__init__(seed)
        self.seen_feedback = []

    def forge(self, pressure, feedback):
        self.seen_feedback.append([dict(f) for f in feedback])
        return super().forge(pressure, feedback)


class TestRunnerPipeline(unittest.TestCase):
    def test_full_pipeline_confirms_h1_and_h2(self):
        recs = H.run_experiment(lambda s: MockForger(s), MockGold(), MockAuditor())
        # tuples well-formed
        self.assertTrue(recs)
        for r in recs[:50]:
            self.assertEqual(set(r) >= {"cell", "pressure", "gold", "cleared"}, True)
            self.assertIn(r["gold"], ("VALID", "INVALID"))
            self.assertIsInstance(r["cleared"], bool)
        # the plumbing yields the pre-registered decisions
        self.assertEqual(A.h1_decision(recs)["verdict"], "H1_CONFIRMED")
        self.assertEqual(A.h2_decision(recs)["verdict"], "H2_CONFIRMED")

    def test_curve_rises_off_stays_low_on(self):
        recs = H.run_cell(MockForger(1), MockGold(), MockAuditor(),
                          H.AblationCell("defenses_off", eye=False, axes=False, governor=False))
        recs += H.run_cell(MockForger(1), MockGold(), MockAuditor(),
                           H.AblationCell("defenses_on"))
        off = A.curve(recs, "defenses_off"); on = A.curve(recs, "defenses_on")
        self.assertGreater(off[max(off)]["rate"], on[max(on)]["rate"] + 0.3)  # off escapes far more at max P


class TestAntiLeakInvariant(unittest.TestCase):
    def test_forger_feedback_never_contains_gold(self):
        spy = SpyForger(0)
        H.run_cell(spy, MockGold(), MockAuditor(), H.AblationCell("defenses_on"),
                   pressure_levels=[0, 1], k=3)
        # every feedback entry the forger ever saw carries only the verdict, never the gold
        for snapshot in spy.seen_feedback:
            for entry in snapshot:
                self.assertNotIn("gold", entry)
                self.assertEqual(set(entry.keys()), {"cleared"})


if __name__ == "__main__":
    unittest.main()
