"""
test_goodhart_forger.py — the adaptive forger (#118) and the harvested attack seed.

Pins:
  1. every forged artefact is well-formed AND gold-INVALID (the forger's intent: sneak false claims);
  2. ANTI-LEAK: forge reads ONLY feedback[-1]['cleared'] — touching any other key raises (tripwire);
  3. determinism: same seed + same feedback sequence -> identical artefacts;
  4. adaptation: under pressure the forger reaches sneakier tactics (not stuck on the blatant one);
  5. attack_seed exposes generic moves and leaks no case identifiers/outcomes (firewall by construction).
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "benchmarks", "goodhart"))

import forger as F              # noqa: E402
import gold_mechanical as G     # noqa: E402
import attack_seed as S         # noqa: E402


class LeakTrap(dict):
    """A feedback dict that allows reading only 'cleared'; any other access raises (anti-leak tripwire)."""
    def __getitem__(self, k):
        if k != "cleared":
            raise AssertionError(f"forger read forbidden feedback key: {k!r}")
        return super().__getitem__(k)

    def get(self, k, default=None):
        if k != "cleared":
            raise AssertionError(f"forger read forbidden feedback key via get(): {k!r}")
        return super().get(k, default)


class TestForgerProducesInvalid(unittest.TestCase):
    def test_all_forged_artifacts_are_gold_invalid(self):
        gold = G.MechanicalGold()
        for seed in range(6):
            fg = F.MechanicalArithForger(seed=seed)
            fb = []
            for p in (0, 1, 2, 4, 8):
                for _ in range(20):
                    art = fg.forge(p, fb)
                    self.assertEqual(art.get("kind"), "arith")
                    self.assertEqual(gold.label(art), "INVALID")   # the forger only submits false claims
                    fb.append({"cleared": True})


class TestAntiLeak(unittest.TestCase):
    def test_forger_reads_only_cleared(self):
        fg = F.MechanicalArithForger(seed=1)
        # feedback carries a gold label the forger must NEVER read; the trap raises if it does
        fb = [LeakTrap(cleared=True, gold="INVALID", auditor_internal="secret")]
        art = fg.forge(2, fb)               # must not raise
        self.assertEqual(art.get("kind"), "arith")


class TestDeterminismAndAdaptation(unittest.TestCase):
    def test_same_seed_same_feedback_identical(self):
        a = F.MechanicalArithForger(seed=42)
        b = F.MechanicalArithForger(seed=42)
        fb_a, fb_b, outa, outb = [], [], [], []
        for _ in range(15):
            xa = a.forge(1, fb_a); outa.append(xa["expr"]); fb_a.append({"cleared": True})
            xb = b.forge(1, fb_b); outb.append(xb["expr"]); fb_b.append({"cleared": True})
        self.assertEqual(outa, outb)

    def test_pressure_unlocks_sneakier_tactics(self):
        # at pressure 0 only the blatant product tactic appears; higher pressure reaches percentage/rounding
        fg0 = F.MechanicalArithForger(seed=3)
        blatant = all(("*" in fg0.forge(0, [])["expr"] and "/" not in fg0.forge(0, [])["expr"])
                      for _ in range(1))  # smoke: pressure 0 stays on products
        fg = F.MechanicalArithForger(seed=3)
        exprs = [fg.forge(4, [])["expr"] for _ in range(30)]
        self.assertTrue(any("/" in e or "and" in e for e in exprs))  # sneakier tactics reached


class TestAttackSeed(unittest.TestCase):
    def test_moves_present_and_generic(self):
        self.assertTrue(S.moves_for("numeric"))
        self.assertTrue(S.moves_for("non_local_conceptual_documented"))
        self.assertEqual(S.moves_for("does_not_exist"), [])
        self.assertGreaterEqual(len(S.all_moves()), 10)

    def test_no_case_identifiers_leaked(self):
        blob = " ".join(S.all_moves()).lower()
        for forbidden in ("rimini", "108", "lotto", "sub ", "perizia", "euro", "€", "44,9", "46.418"):
            self.assertNotIn(forbidden, blob)   # firewall: only generic move shapes, no case data/outcomes


if __name__ == "__main__":
    unittest.main()
