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
import hashlib
import hmac
import json
import os
import sys


# Self-contained mirror of aae.attestation (the hook must run without imports).
# MUST stay byte-identical to aae.attestation.content_digest.
def _content_digest(led: dict) -> str:
    norm = [{"element": str(f.get("element", "")), "verdict": str(f.get("verdict", ""))}
            for f in led.get("findings", [])]
    blob = json.dumps({"artifact_name": str(led.get("artifact_name", "")),
                       "findings": norm}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _human_attestation_verifies(led: dict) -> bool:
    """True iff AAE_HUMAN_ATTESTATION is a valid HMAC of the ledger digest under
    AAE_HUMAN_KEY — the same test run_core applied. Missing key/token → False."""
    key = os.environ.get("AAE_HUMAN_KEY")
    token = os.environ.get("AAE_HUMAN_ATTESTATION")
    if not key or not token:
        return False
    expected = hmac.new(key.encode("utf-8"), _content_digest(led).encode("utf-8"),
                        hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, token.strip())


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


def _utf8_stdio() -> None:
    """Windows Stop hooks run under the console codepage (cp1252), which cannot encode
    an accented artifact name or a box/warn glyph — a real run crashed the hook with
    UnicodeEncodeError. Force UTF-8 with replacement; a no-op where unsupported."""
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main() -> int:
    _utf8_stdio()
    out_dir = os.environ.get("AAE_OUT", os.path.join(os.getcwd(), "aae_out"))
    ledgers = sorted(glob.glob(os.path.join(out_dir, "*.ledger.json")))
    pending = os.path.join(out_dir, ".audit_pending")
    print("== meta-epistemic governor (Stop hook) ==")
    if not ledgers:
        if os.path.exists(pending):
            # An audit started (the schema was fetched) but NO deterministic ledger
            # exists: the run derailed — an exception, a tool error, or the model
            # writing a prose summary instead of invoking the core. A prose 'referto'
            # is NOT an audit: verdicts must come from run_core.py, not from the model.
            # Fail LOUD and BLOCKING so the session cannot present as a completed audit.
            print("  !! AUDIT DERAILED — the audit started (schema fetched) but produced "
                  "NO deterministic ledger in", out_dir + ".")
            print("  A prose summary is NOT an audit: verdicts come from run_core.py, not "
                  "from the model. This session is INVALID and cannot close.")
            print("  RECOVER: gather your findings into findings.json and run "
                  "`run_core.py findings.json`. If a surprise interrupted you (e.g. the "
                  "independent eye erroring), that only lowers the independence level — it "
                  "must NEVER skip the core. Run the core, then stop.")
            return 2   # blocking: Claude Code surfaces this and the audit is not accepted
        print("  no ledger found in", out_dir, "— nothing to check.")
        return 0
    # A ledger exists: the core ran. Clear any stale marker so it can't misfire later.
    try:
        os.remove(pending)
    except OSError:
        pass
    led = json.load(open(ledgers[-1], encoding="utf-8"))

    # F-HOOK enforcement: a VALIDATED completion is only legitimate if a human
    # attested OUT OF BAND (operator environment). If not, correct the artifact.
    completion_state = led.get("completion_state", "")
    verified = _human_attestation_verifies(led)
    downgraded = False
    if completion_state == "VALIDATED" and not verified:
        led["completion_state"] = "EXTERNAL_REVIEW_PENDING"
        # The independence level must fall with the completion state: leaving it
        # at HUMAN_DOMAIN_EXPERT would keep the ledger presenting as human-closed
        # to every downstream reader, including this governor's own low_ind rule.
        if int(led.get("independence_level", 1)) >= 4:
            led["independence_level"] = 1
        led.setdefault("flags", []).append(
            "HOOK-DOWNGRADE: completion was VALIDATED without a verifiable human "
            "attestation (no valid HMAC under AAE_HUMAN_KEY at Stop time) — downgraded "
            "to EXTERNAL_REVIEW_PENDING and independence reset to 1. Internal grounds "
            "can never reach VALIDATED.")
        with open(ledgers[-1], "w", encoding="utf-8") as fh:
            json.dump(led, fh, ensure_ascii=False, indent=2)
        downgraded = True

    verdict, ac, notes = verdict_from_ledger(led)
    print(f"  artifact: {led.get('artifact_name','?')}")
    if completion_state:
        print(f"  completion state: {led.get('completion_state', completion_state)}")
    if downgraded:
        print("  !! HOOK ENFORCEMENT: downgraded an unverified VALIDATED "
              "-> EXTERNAL_REVIEW_PENDING (artifact corrected on disk).")
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
