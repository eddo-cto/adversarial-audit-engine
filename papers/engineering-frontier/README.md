# The engineering frontier of verification

A short, self-contained methodological note on the adversarial-audit engine, with a runnable demonstration.

**One claim, made precise.** Machine verification reduces to engineering *exactly up to the independence
supply*, and **non-closure** — the engine's refusal to emit `VALIDATED` on internal grounds — is the
certificate that the supply has run out. The two facts usually stated as separate "humility lemmas" (a
vacuity floor; the impossibility of internal validation) are shown to be **one** quantity seen twice: the
error-correlation `ρ` between the evidence and the evaluator.

- `ρ = 0` — an independent channel: `n_eff = N`, vacuity `u → 0`. Verification *is* engineering; the external
  eye is a **speed-up**.
- `ρ → 1` — a same-nature repeat: `n_eff → 1`, `u` pinned at `u_∞(ρ) = W/(W + r̄/ρ) > 0`; and `ρ` itself is
  **unidentifiable** without an anchor. The external, different-nature eye is **necessary**.

The frontier is the locus where `n_eff` saturates. Non-closure names it.

## Files
- `THE_ENGINEERING_FRONTIER.md` — the note: setup, two propositions (with proofs), the corollary, honest limits.
- `frontier_demo.py` — the demonstration (Python standard library only).

## Run
```
python3 frontier_demo.py
```
**Exhibit A** simulates equicorrelated Bernoulli evidence and recovers the effective count `n_eff`
empirically (matches the Kish design-effect formula across `ρ`), then reads off the vacuity floor `u_∞(ρ)`.
**Exhibit B** shows internal agreement is symmetric under `p ↔ 1−p` — a confidently-*wrong* consensus agrees
exactly as much as a confidently-*right* one — so consensus cannot identify correctness, while a single
anchored draw separates them (`KL > 0`).

## Status
This note is a **survivor**, not a validated result: internal grounds cannot reach that verdict. Closure — of
this note too — is external.
