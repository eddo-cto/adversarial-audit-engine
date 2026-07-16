# The engineering frontier of verification

*A methodological note on the adversarial-audit engine. It makes one claim precise and gives it a runnable
demonstration: **machine verification reduces to engineering exactly up to the independence supply, and
non-closure is the certificate that the supply has run out.** The two facts usually stated as separate
"humility lemmas" are shown here to be **one** quantity — the error-correlation `ρ` between the evidence and
the evaluator — seen twice.*

Companion demonstration: `frontier_demo.py` (Python standard library only; prints every number quoted below).

---

## 0. The deflation to be bounded

A self-referential evaluator — a model judging a model, a procedure auditing itself — that *does* resolve
indeterminate cases invites the reading:

> "The machine verifies. So verification is **engineering**: build better probes, accumulate more evidence,
> reliability follows."

This is true up to a line and false past it. The engine's value is that the line is **locatable**, and the
note below gives its coordinate: the correlation `ρ` between a new probe's error and the evaluator's error.
`ρ = 0` is an independent channel; `ρ = 1` is a same-nature repeat. Everything follows from what `ρ` does to
two quantities — reducible uncertainty and identifiability.

## 1. Setup

Fix a claim and an evaluator `E`. Evidence arrives as items `e₁,…,e_N`, each a Beta pseudo-count of weight
`r̄` feeding a subjective-logic opinion whose **vacuity** `u ∈ [0,1]` is the mass of "not yet determined,"
`u = W / (W + n·r̄)` for prior weight `W` and `n` *independent* items.

Model the items as equicorrelated with common pairwise error-correlation `ρ` to `E`'s nature (they share, to
degree `ρ`, whatever `E` is made of). The **effective number of independent items** is the Kish design-effect
count

```
    n_eff(N, ρ) = N / (1 + (N − 1)·ρ).
```

`n_eff = N` at `ρ = 0`; `n_eff → 1/ρ` as `N → ∞` for `ρ > 0`; `n_eff = 1` for all `N` at `ρ = 1`.
This single object drives both results.

## 2. Proposition 1 — reducible vacuity is bounded by the independence supply

**Claim.** Fusing `N` equicorrelated items leaves

```
    u(N, ρ) = W / (W + n_eff(N, ρ)·r̄),     and therefore     inf_N u(N, ρ) = W / (W + r̄/ρ) =: u_∞(ρ).
```

Hence `u_∞(ρ) > 0` for every `ρ > 0`, `u_∞ → 0` iff `ρ → 0`, and at `ρ = 1` the floor
`u_min = W/(W + r̄)` is hit **at N = 1** and never improved.

**Proof.** Information from correlated observations scales with `n_eff`, not `N`: for equicorrelated units the
Fisher information of the mean is `N/(σ²(1+(N−1)ρ)) = n_eff/σ²`. Substituting the effective count into the
Beta→opinion map `u = W/(W + n·r̄)` gives the displayed `u(N,ρ)`. It is decreasing in `N` and its infimum is
the `N→∞` limit `n_eff → 1/ρ`, giving `u_∞(ρ)`. Monotonicity in `ρ` and the two endpoints are immediate. ∎

The content is not "there is a floor" but **the floor's coordinate**: it is `W/(W + r̄/ρ)`, a function of the
one parameter that measures nature-sharing. Independent evidence (`ρ=0`) closes the claim by engineering; each
increment of self-reference (`ρ↑`) raises the irreducible residue by a computable amount. Reducible uncertainty
*is* the independence supply.

## 3. Proposition 2 — without an anchor you cannot even measure ρ

Proposition 1 prices the residue in `ρ`. But `ρ` is an **error**-correlation, and error is defined against
truth. With no ground-truth **anchor**, `ρ` is not identifiable from internal agreement.

**Claim.** There exist two data-generating worlds — `W_ind` (N sources independently correct with prob `p`)
and `W_cor` (N sources copying a shared latent that is correct with prob `q`) — with `p ≠ q` yet **identical
distribution of the internal agreement statistic**. No function of internal agreement has different
expectation across them (internal likelihood ratio ≡ 1); a single query to an external anchor has strictly
positive discrimination (KL > 0).

**Construction (binary case).** In `W_cor` sources copy a latent `L`, so agreement is total and correctness is
`q`. In `W_ind` agreement is `a(p) = p² + (1−p)²` and correctness is `p`. Choose `q` and `p` so the *observed*
agreement matches (e.g. both worlds conditioned to the same agreement level by mixing a tie-breaking source);
the internal agreement histograms coincide by construction, so consensus is **observationally identical**
while correctness differs by `|p − q|`. That gap is invisible internally and visible in one anchored draw.
This is the peer-prediction / Schelling-oracle wall (bribery, p+ε, 51%): a mechanism with no external
reference cannot separate genuine from coordinated consensus. ∎

Proposition 2 is the reason Proposition 1's `ρ` cannot be estimated away from inside: the very quantity that
prices the residue is unmeasurable without a channel of different nature.

## 4. Corollary — the frontier, and what non-closure certifies

Both propositions turn on independence. Put them together:

| | independent channel available (`ρ` can be lowered / anchored)? | verification is… | external eye is… |
|---|---|---|---|
| **Anchored stratum** | yes | **engineering** — add channels, `n_eff ↑`, `u → 0` | a **speed-up**, not a gate |
| **Self-referential stratum** | no (`ρ → 1`, no anchor) | **not reducible** — `u` pinned at `u_∞(ρ) > 0`, and `ρ` unidentifiable | **necessary** — it *is* the `ρ≈0` channel |

The boundary is a real locus: **where `n_eff` stops growing** because every remaining channel has `ρ → 1`.
**Non-closure** — the engine's refusal to emit `VALIDATED` on internal grounds, routing its residue to an
external eye — is exactly the **certificate that this locus has been reached**. It is not stylistic humility
and it does not support the deflation; it **fences the region where the reduction to engineering fails, at a
point the engine can name** (`u_∞(ρ) > 0` with `ρ` unidentifiable).

## 5. The claim, stated so it cannot be mistaken for its overreach

- **Overreach (false):** *the machine verifies, therefore verification is engineering, not epistemic.*
- **The under-stated true claim:** *the machine measures how far engineering reaches — it certifies its own
  frontier at the independence-supply coordinate. On the anchored stratum it resolves (the human eye is a
  speed-up); on the self-referential stratum `u` is pinned and `ρ` unmeasurable, and it says so.*

Equivalently: **you can engineer the plumbing (route the residue outward); you cannot engineer the warrant
(the external, different-nature judgment).** The reduction breaks at the warrant, not the pipe — and the engine
is the instrument that shows the break's coordinate.

## 6. The demonstration (`frontier_demo.py`)

Two exhibits, both printed numerically:

- **A — the floor as a function of `ρ`.** Fuse `N = 1…10⁴` equicorrelated items at each `ρ ∈ {0, .01, .1, .5,
  1}`. Output: `u(N)` collapses to `u_∞(ρ) = W/(W + r̄/ρ)`; `ρ=0 → u→0` (engineering closes the anchored
  stratum); `ρ=1 → u` pinned at `u_min` from the first item (no internal probe closes the self-referential
  stratum). The printed plateau matches the closed form to machine precision.
- **B — non-identifiability without an anchor.** Build `W_ind` and `W_cor` matched on internal agreement.
  Output: internal log-likelihood-ratio ≈ 0 (consensus cannot tell them apart) while a single anchored query
  yields KL > 0 (one external draw can). Correctness gap `|p − q|` is real and internally invisible.

```
python3 frontier_demo.py
```

## 7. Honest limits

`u_∞(ρ)` is exhibited under a standard equicorrelation + subjective-logic model; extending it to arbitrary
dependence structures (beyond one scalar `ρ`) is open. "Anchored vs self-referential" is itself a judgement
about a given claim — the engine helps *locate* the frontier, it does not remove the need to judge where a
specific claim sits. And this note is a **survivor**, not a validated result: internal grounds cannot reach
that verdict — closure, of this note too, is external.
