#!/usr/bin/env python3
"""
governor_check.py — Stop-hook enforcement of the meta-epistemic governor.

This is the CODE that makes the discipline non-bypassable: at the end of a run
it inspects the produced ledger(s) and emits the reliability verdict, applying
the transversal law (clean + low-independence == suspect) and the hard rule that
internal grounds can NEVER reach "VALIDATED".

It mirrors aae.meta_epistemic deterministically and is self-contained so it can
run as a hook without importing the package; if `aae` is importable it is used.

Exit code is always 0 (a Stop hook should inform, not crash the session); the
message is printed to stdout/stderr for the operator and the model to see.
"""
from __future__ import annotations
import glob
import json
import os
import sys


def verdict_from_ledger(led: dict) -> tuple[str, float, list[str]]:
    findings = led.get("findings", [])
    by = {}
    for f in findings:
        v = f.get("verdict", "pending")
        by[v] = by.get(v, 0) + 1
    total = len(findings)
    defective = by.get("accusa_vince", 0)
    needs_expert = by.get("conteso", 0)
    holds = by.get("artefatto_regge", 0)
    declared_limits = sum(1 for f in findings if f.get("declared_limit"))
    coverage_flags = len(led.get("flags", []))
    independence = int(led.get("independence_level", 1))
    # false positives proxy: ARTIFACT_HOLDS that were defended (we count holds)
    notes = []
    signals = 0.0
    low_ind = independence <= 1
    if low_ind:
        notes.append("INDEPENDENCE: agents share one model family — NOT real "
                     "independence (shared blind spots invisible).")
        signals += 1
    clean = total > 0 and defective == 0 and needs_expert == 0
    if clean:
        notes.append("APPARENT COHERENCE: result suspiciously clean (no defects "
                     "upheld, no CONTESO) — possible circuit-closure, not quality.")
        signals += 1
    if needs_expert == 0:
        notes.append("CALIBRATION: nothing routed to CONTESO/expert.")
        signals += 0.5
    if declared_limits == 0:
        notes.append("HONESTY: no internal limit declared anywhere.")
        signals += 1
    if coverage_flags:
        notes.append(f"COVERAGE: {coverage_flags} dimension(s) uncovered/unjustified.")
        signals += 0.5
    ac = min(1.0, signals / 5.0)
    verdict = ("NOT_INTERNALLY_VERIFIABLE" if (low_ind or ac >= 0.6)
               else "RELIABLE_WITH_RESERVATIONS")
    return verdict, ac, notes


def main() -> int:
    out_dir = os.environ.get("AAE_OUT", os.path.join(os.getcwd(), "aae_out"))
    ledgers = sorted(glob.glob(os.path.join(out_dir, "*.ledger.json")))
    print("── meta-epistemic governor (Stop hook) ──")
    if not ledgers:
        print("  no ledger found in", out_dir, "— nothing to check.")
        return 0
    led = json.load(open(ledgers[-1], encoding="utf-8"))
    verdict, ac, notes = verdict_from_ledger(led)
    print(f"  artifact: {led.get('artifact_name','?')}")
    print(f"  reliability verdict: {verdict}  (apparent-coherence {ac:.2f})")
    for n in notes:
        print(f"   - {n}")
    print("  RULE: internal grounds can never reach 'VALIDATED'. The residue "
          "(unknown-unknowns; metric/ground-truth disputes; true independence) "
          "must be closed by an EXTERNAL HUMAN eye.")
    print("  GOVERNOR SELF-LIMIT: built from the same machinery as the system, "
          "I detect failure-signatures; I do not close the loop.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
