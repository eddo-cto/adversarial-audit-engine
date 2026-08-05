# Round-10 work order — corrections to `PAPER_system_description.md` and `governor_check.py`

**Target repo.** `github.com/eddo-cto/adversarial-audit-engine` at `079ae5d` (branch `main`).
**Paper source.** `papers/system-description/PAPER_system_description.md`.
**Origin.** Round-10 adversarial audit, ledger `audit_round10_paper_v2.ledger.json`
(10 findings, 8 `accusa_vince`, 2 `artefatto_regge`, completion `EXTERNAL_REVIEW_PENDING`,
governor `not_internally_verifiable`, independence level 1).

**Provenance warning — read before applying.** The audit that produced this work order was run by
an Anthropic model, i.e. the **same vendor** as the engine's own roles (`sonnet` for the hostile
roles, `opus` for the governor). By the engine's own definition (`aae/independence_ledger.py:23`)
that is independence level ≤ 2, **not** a different nature. Every item below is therefore a
*candidate*, not a verdict. Re-derive each one by execution before applying it; the evidence
command is given for every item. Do not accept an item because this file asserts it.

---

## Block A — paper corrections (mandatory before submission)

### A1. Repin the artifact commit — **blocking**

The paper pins `5f6e4d4`. Every round-9 fix lives in `079ae5d`. A referee who clones the pinned
commit gets a repo where §3's `F-SECTIONS` wiring is absent, §4's vendor-aware and out-of-band
closure do not exist, §5's 144 tests are 137, §8's guard-test file does not exist, and the whole of
§9 is unsupported. The paper's central move — clone and watch the gates fire — fails at the commit
the paper names.

*Evidence:* `git log --oneline 5f6e4d4..079ae5d` and, at `5f6e4d4`,
`git show 5f6e4d4:plugins/adversarial-audit-engine/aae/gates.py | grep -c vendor` → 0.

**Preferred fix:** cut an annotated tag on the commit that carries these corrections
(`git tag -a v1.0.2 -m "round-10 corrections"`) and pin the tag, so the pin cannot go stale again.
Line 13:

- old: ``at commit `5f6e4d4`. Four``
- new: ``at tag `v1.0.2`. Four``

If you prefer a bare commit, pin the correcting commit's SHA, not `079ae5d` — the paper must not
name a commit that predates its own text. **Add a standing check to §8:** the reproducibility block
should clone at the pinned ref, not at `HEAD`.

### A2. §9 — remove the unearned independence claim — **blocking**

`§9` calls the round-9 audit *"a genuinely different-nature check"*. It was not: same vendor,
independence level ≤ 2, and the ledger that audit emitted records `independence_level: 1` with the
governor's note *"agents share one instance/model family — NOT real independence"*. `§7` of the same
paper states the correct thing (*"two same-nature adjudicators … stay at independence level 1–2"*),
so `§9` contradicts `§7`. This is a self-assigned independence upgrade in the paper whose thesis is
that such upgrades are the failure mode — the apparent-consistency signature the governor exists to
detect. It is also the single easiest thing for a referee to catch: read §7, then §9.

The honest version is **stronger**: a same-nature auditor at the *minimum* independence level still
found four structural defects in the closure guarantees. That is a better advertisement for the
method than a borrowed level 3.

Replace lines 269–279 (the first paragraph of §9):

- old:
  ```
  The claims in §3–§4 above are stronger than they would have been a revision ago, and the reason is worth
  telling because it *is* the method. An independent instance of the engine — run on a separate account, a
  genuinely different-nature check — was pointed at this paper's own draft. It returned a disciplined
  ledger (with defense attempts, reduced findings, and every self-reported figure independently
  recomputed) and it **upheld four accusations against the engine's own closure guarantees**:
  ```
- new:
  ```
  The claims in §3–§4 above are stronger than they would have been a revision ago, and the reason is worth
  telling because it *is* the method. A separate instance of the engine — a distinct session on a separate
  account, but the **same vendor as the engine's own roles, so independence level 1–2 and explicitly not a
  different nature** — was pointed at this paper's own draft. It returned a disciplined ledger (defense
  attempted on every accusation, four accusations withdrawn against a verifiable fact, and every
  self-reported figure independently recomputed by execution rather than accepted) and it **upheld four
  accusations against the engine's own closure guarantees**:
  ```

Note the two secondary corrections folded in: *"reduced findings"* names the wrong verdict (that
ledger contained zero `REDUCED`; it had 7 `accusa_vince` and 4 `artefatto_regge`), and the
same-vendor status is now stated rather than elided.

*Evidence:* `python3 -c "import json,collections;d=json.load(open('<ledger>'));print(collections.Counter(f['verdict'] for f in d['findings']), d['independence_level'])"`
→ `Counter({'accusa_vince': 7, 'artefatto_regge': 4}) 1`.

Add one sentence at the end of the §9 first paragraph:

> That the finder sat at the *minimum* independence level is the point worth keeping: same-nature
> auditing is weak by construction, and it still located four defects the authors had not seen.

### A3. §4 — the two enforcement points are not independent — **blocking**

`§4` line 155 claims non-closure is *"enforced in code at two independent points — the completion
state machine and the hook."* Both read the same environment variable, `AAE_HUMAN_ATTESTATION`.
Their failure modes are perfectly correlated: if the variable is set, the state machine validates
**and** the hook confirms; the hook only fires when the variable is absent, which catches a stale or
hand-edited ledger, not the case the fix was written for. A paper whose central quantity is the
error-correlation ρ should not assert independence between two checks whose ρ is 1.

*Evidence:* with `AAE_HUMAN_ATTESTATION=whatever`, `run_core.py` returns `VALIDATED` and
`governor_check.py` in the same environment prints `completion state: VALIDATED` and does not
downgrade; with the variable unset, it downgrades.

Line 154–156:

- old: ``Non-closure is\nnot a posture here: it is enforced in code at two independent points — the completion state machine and\nthe hook.``
- new: ``Non-closure is\nnot a posture here: it is checked in code at write time and re-checked at Stop time, both against the\nsame operator secret — one mechanism at two moments, not two independent mechanisms.``

### A4. §4 — scope "outside the model's reach" to its threat model

Line 147–148 says the attestation is *"a secret the operator supplies from outside the model's
reach (an environment token)"*. The environment is not outside the model's reach in the documented
architecture: the `verifier` role's own mandate is *"where code is executable, it EXECUTES it
(bash/node)"*, so the orchestrating side has a shell. The token value is also unvalidated — any
non-empty string closes the loop.

*Evidence:* `AAE_HUMAN_ATTESTATION=whatever python3 scripts/run_core.py payload.json`
→ `completion: VALIDATED — Human external review attested out-of-band (operator token 'whatever')`.

This is still a real improvement over round 8 (forgery moved from a payload field the model writes
by design to an environment variable it must deliberately set), so state the improvement and its
boundary rather than overclaiming:

- old: ``The attestation is a secret the operator\nsupplies from outside the model's reach (an environment token)``
- new: ``The attestation is a secret the operator\nsupplies through a channel the payload does not touch (an environment token). The guarantee is\nrelative to a stated threat model: it holds for an operator who does not export the secret into the\nagent's shell, and it moves forgery from a field the model authors by design to a variable it must\ndeliberately set. It is not a cryptographic barrier — see §7``

### A5. §5 / §8 — the test count contradicts itself

`§5` line 167 says 144 passing; the `§8` block a reader will copy-paste (line 254) still says 137.
Measured at `079ae5d`: `Ran 144 tests … OK`.

- Line 254 old: ``# 137 tests``
- Line 254 new: ``# 144 tests``

### A6. §9 — scope the closing claim

Line 283 says closing the round-9 gap *"made the claim true across all three gate-families."* Two
closure guarantees still rest on unattested strings: human closure on an unvalidated environment
variable inside the agent's shell (A4), and level-3 vendor independence on a payload field the model
authors (C1 below). The categorical claim is not yet earned.

- old: ``The\nengine located that gap *in itself*, and closing it made the claim true across all three gate-families.``
- new: ``The\nengine located that gap *in itself*. Closing it made the claim fully true for the sections-gate and for\nvendor-awareness, and reduced human-closure forgery from a payload field to an operator secret whose\nstrength is the operator's own hygiene — a contraction of the attack surface, not its elimination. The\nresidue is stated in §7.``

---

## Block B — code correction (small, do it now)

### B1. The hook downgrade leaves `independence_level` at 4

After `governor_check.py` downgrades an unattested `VALIDATED`, the on-disk ledger reads
`completion_state: EXTERNAL_REVIEW_PENDING` while `independence_level` stays `4`
(`HUMAN_DOMAIN_EXPERT`). The artifact is left internally inconsistent, and the governor's own
suspicion rule keys on that field (`low_ind = independence <= 1`), so a downgraded ledger still
presents as human-closed to every downstream reader.

*Evidence:* after the downgrade, the ledger reads
`{'independence_level': 4, 'completion_state': 'EXTERNAL_REVIEW_PENDING', 'flags': ['HOOK-DOWNGRADE: …']}`.

In `plugins/adversarial-audit-engine/scripts/governor_check.py`, inside the
`if completion_state == "VALIDATED" and not attested:` block (around line 84), before the file is
rewritten:

```python
    if completion_state == "VALIDATED" and not attested:
        led["completion_state"] = "EXTERNAL_REVIEW_PENDING"
        # The independence level must fall with the completion state: leaving it
        # at HUMAN_DOMAIN_EXPERT would keep the ledger presenting as human-closed
        # to every downstream reader, including this governor's own low_ind rule.
        if int(led.get("independence_level", 1)) >= 4:
            led["independence_level"] = 1
        led.setdefault("flags", []).append(
            "HOOK-DOWNGRADE: completion was VALIDATED without an out-of-band human "
            "attestation (AAE_HUMAN_ATTESTATION unset at Stop time) — downgraded to "
            "EXTERNAL_REVIEW_PENDING and independence reset to 1. Internal grounds "
            "can never reach VALIDATED.")
```

**Pin it with a regression test** in `tests/test_closure_hardening.py`: write a ledger with
`completion_state: "VALIDATED"` and `independence_level: 4`, run the hook with
`AAE_HUMAN_ATTESTATION` unset, and assert **both** that `completion_state` became
`EXTERNAL_REVIEW_PENDING` **and** that `independence_level` is no longer ≥ 4. Asserting only the
first is what let this through.

---

## Block C — declared limits for §7 (do **not** fix now; ship as stated residue)

These two are real and belong in the paper as declared limits, not as silent gaps. Fixing them is
round 11; declaring them now is what lets the paper go out honestly.

### C1. Level 3 is asserted, not attested

The reviewer's vendor is read from `external_identity`, which the orchestrating model authors — the
exact channel the F-HUMAN fix declared untrustworthy. The fix was not propagated one rung down the
ladder. Executed at `079ae5d`: `external_identity="zzz:qqq"` and `"notanthropic:whatever"` both
return `CROSS_MODEL_REVIEWED` at independence level 3 against an `anthropic:` internal identity.
Nothing cross-checks the claimed reviewer against the adapter that made the call — even though
`aae/adapters.py` already builds that identity from the base URL (`self.identity = f"{vendor}:{model}"`).

**Round-11 fix (record it, don't build it now):** have the adapter emit the identity it actually
called, accept level 3 only from that record, and mark any payload-supplied level as `CLAIMED` in
the ledger.

### C2. The human token is unvalidated

Any non-empty `AAE_HUMAN_ATTESTATION` closes the loop; the value is never checked. **Round-11 fix:**
HMAC over the ledger hash with a key the operator holds outside the session, or a signed file with a
public key pinned in the repo.

**Text to add at the end of §7**, after *"That is the engine's own thesis applied to itself."*:

> Two closure guarantees are, as of this version, conventions rather than proofs, and we state them
> as residue rather than let a reader discover them. Human closure requires a non-empty operator
> token whose value is never verified: the guarantee holds against a model that authors the payload,
> not against one that exports an environment variable into its own shell. And the reviewer's vendor
> is read from a payload field rather than attested by the adapter that made the call, so
> independence level 3 is *claimed*, not proven — a string of the form `vendor:model` with any
> unfamiliar vendor part is currently sufficient. Both are one commit each and both are round-11
> work; neither is load-bearing for the §6 measurements, which were produced under level 1–2 and are
> reported as such.

---

## Block D — acceptance checklist

Apply nothing that does not pass its own evidence command first. When done, all of the following
must hold:

```bash
cd plugins/adversarial-audit-engine
export PYTHONPATH="$PWD"

# 1. suite still green, count matches the paper in BOTH places
python3 -m unittest discover -s tests            # expect: Ran 145 tests ... OK  (144 + B1)
grep -c "144 tests\|145 tests" ../../papers/system-description/PAPER_system_description.md

# 2. benchmarks unchanged
for b in calibration real_errors inter_nature baselines; do
  python3 benchmarks/$b/reproduce.py --strict >/dev/null || echo "DIVERGED: $b"
done

# 3. B1 actually landed
unset AAE_HUMAN_ATTESTATION
# ...write a VALIDATED/level-4 ledger into $AAE_OUT, then:
python3 scripts/governor_check.py
# assert on disk: completion_state == EXTERNAL_REVIEW_PENDING AND independence_level < 4

# 4. the paper no longer names a stale ref
grep -n "5f6e4d4" ../../papers/system-description/PAPER_system_description.md   # expect: no hits
grep -n "137 tests" ../../papers/system-description/PAPER_system_description.md # expect: no hits

# 5. the two overclaims are gone
grep -n "genuinely different-nature" ../../papers/system-description/PAPER_system_description.md  # expect: no hits
grep -n "two independent points"     ../../papers/system-description/PAPER_system_description.md  # expect: no hits
```

Then verify the pin resolves: `git tag -a v1.0.2 && git push --tags`, and confirm that a fresh
clone at that tag reproduces §5, §6 and §8 without any local state.

---

## What this work order does not close

This file was produced at independence level 1, single-vendor, single run. It cannot validate
anything and does not attempt to. Items A1, A5, B1 and the two `grep` checks in D are mechanically
verifiable and need no judgement. Items A2, A3, A4, A6 and Block C are **arguments about what the
paper should claim**, and an author is entitled to disagree with them — if you do, record the
disagreement rather than silently keeping the current wording, because the next auditor will raise
the same points and the record of why you rejected them is worth more than the wording itself.

The residue that neither this file nor the engine can close: whether the two-frontier result of §6
survives a genuinely different-vendor replication, and whether the defect taxonomy carves the space
the way the paper says it does. Both need an external human eye.

---

*Applied in commit `d22d475` (round 10) and, together with the §9/§10 disclosure and this trail,
tag `v1.0.3` (round 10 disclosure). Every item was re-derived by execution before application; see
the session record. Two residues (C1, C2) are declared in §7 and deferred to round 11.*
