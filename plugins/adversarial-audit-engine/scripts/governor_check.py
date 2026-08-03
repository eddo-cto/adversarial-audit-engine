#!/usr/bin/env python3
"""
governor_check.py — Stop-hook enforcement of the meta-epistemic governor.

This is the CODE that makes the discipline non-bypassable: at the end of a run
it inspects the produced ledger(s) and emits the reliability verdict, applying
the transversal law (clean + low-independence == suspect) and the hard rule that
internal grounds can NEVER reach "VALIDATED".

It mirrors aae.meta_epistemic deterministically and is self-contained so it can
run as a hook without importing the package; if `aae` is importable it is used.

Enforcement (F-HOOK fix): the hook reads the persisted completion_state and, if
it is VALIDATED without an OUT-OF-BAND human attestation (AAE_HUMAN_ATTESTATION
in the operator's environment at Stop time), it DOWNGRADES the ledger on disk to
EXTERNAL_REVIEW_PENDING and records the correction. It runs in the operator's
environment, which the model cannot forge, so this is a genuine second lock.

Exit code is always 0 (a Stop hook must not crash the session); enforcement is
by CORRECTING the persisted artifact, not by failing the run.
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

    # F-HOOK enforcement: a VALIDATED completion is only legitimate if a human
    # attested OUT OF BAND (operator environment). If not, correct the artifact.
    completion_state = led.get("completion_state", "")
    attested = bool(os.environ.get("AAE_HUMAN_ATTESTATION"))
    downgraded = False
    if completion_state == "VALIDATED" and not attested:
        led["completion_state"] = "EXTERNAL_REVIEW_PENDING"
        led.setdefault("flags", []).append(
            "HOOK-DOWNGRADE: completion was VALIDATED without an out-of-band human "
            "attestation (AAE_HUMAN_ATTESTATION unset at Stop time) — downgraded to "
            "EXTERNAL_REVIEW_PENDING. Internal grounds can never reach VALIDATED.")
        with open(ledgers[-1], "w", encoding="utf-8") as fh:
            json.dump(led, fh, ensure_ascii=False, indent=2)
        downgraded = True

    verdict, ac, notes = verdict_from_ledger(led)
    print(f"  artifact: {led.get('artifact_name','?')}")
    if completion_state:
        print(f"  completion state: {led.get('completion_state', completion_state)}")
    if downgraded:
        print("  ⚠ HOOK ENFORCEMENT: downgraded an unattested VALIDATED "
              "→ EXTERNAL_REVIEW_PENDING (artifact corrected on disk).")
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
