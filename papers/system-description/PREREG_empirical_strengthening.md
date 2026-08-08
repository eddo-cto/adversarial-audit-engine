# Pre-registration — strengthening §6: is the capability/independence dissociation two axes or one?

*Status: **pre-registration**. This document is written and committed **before** any new data is
collected. Its purpose is to bind us to a design and an analysis in advance, so that a confirming result
cannot be the product of post-hoc choices and a disconfirming result cannot be quietly discarded. It
inherits the project's invariants: nothing here can reach `VALIDATED` on internal grounds; whoever knows
the labels does not audit; targets are anonymized; the engine flags, it does not accuse. Companion to
`PAPER_system_description.md` §6 and to the falsification-lens protocol.*

**Registration commit:** this file's git commit hash and timestamp are the registration record. Any
change after data collection begins is logged in §9 (Deviations), not silently edited in.

---

## 1. Why this study exists (the criticism it must answer)

§6 currently reports, on **n = 7** sealed Matters-Arising targets audited under three model "natures"
(one run per nature), a **descriptive dissociation**: the *external-data* defect class is recovered more
as auditor nature-distance grows (A 0/3 ≤ B 2/3 ≤ C 3/3, monotone → ρ < 1), while the
*domain-re-derivation* class is recovered by **no** nature (0/3 across all), and the single
*general-reasoning* target is recovered by all. The different-vendor (level-3) review accepted the
description but rejected the causal reading: **"nature" confounds vendor, capability, tool access, and
run-to-run variance**, so n = 7 with one run per nature cannot separate a *capability* axis from an
*independence* axis. §6 was scoped down to "descriptive dissociation" accordingly.

This study is the design that would let the two axes be **separated or collapsed on the evidence**. It is
explicitly **not** a detection-accuracy claim and **not** a closure: it tests one structural question —
are capability and independence two separable axes of recovery, or one latent axis wearing two names?

## 2. Pre-registered hypotheses (directional)

Let recovery = the pre-registered *landing* of a produced finding on a sealed defect (§5 rule), per
mechanism class ∈ {general_reasoning (GR), external_data (ED), domain_rederivation (DR)}.

- **H1 (independence axis).** Holding **capability fixed**, raising auditor **independence** raises ED
  recovery monotonically, with **no** effect on GR (ceiling) or DR (floor).
- **H2 (capability axis).** Holding **independence fixed**, raising auditor **capability** raises DR
  recovery, with **little or no** effect on ED.
- **H0 (the falsifier — single latent axis).** Whatever raises ED recovery also raises DR recovery (and
  vice versa): the two classes move **together** regardless of which factor is varied. If the 2×2 shows
  the same class-recovery pattern whichever axis we move, the two-axis claim is **falsified** and we
  report a single-axis (or null) result.
- **S (specificity, must hold throughout).** Cross-domain **decoy** false-positive rate stays ≈ 0 in
  every cell, including the blind adjudicator. If decoys start firing, the whole recovery signal is
  contaminated and the study is inconclusive (reported as such).

We commit in advance to reporting H0/null outcomes with the same prominence as a confirmation; the target
venue (JUDGe) explicitly welcomes negative results.

## 3. Design — a 2×2 factorial that breaks the confound

Two crossed factors, each two levels; this is what n = 7 / one-run-per-nature could not do.

| | **IND− (low independence)** | **IND+ (high independence)** |
|---|---|---|
| **CAP− (low capability)** | same-vendor weak model, same-family instance | different-vendor model of *comparable* (low) capability |
| **CAP+ (high capability)** | same-vendor strong model, same-family instance | different-vendor model of *comparable* (high) capability |

- **Isolating independence:** compare **IND+ vs IND− at fixed CAP** (columns within a row). Capability
  and tools held ≈ constant, only the vendor/instance independence changes.
- **Isolating capability:** compare **CAP+ vs CAP− at fixed IND** (rows within a column). Independence
  held constant, only model capability changes.
- **k runs per cell** (pre-registered **k ≥ 3**) to estimate run-to-run variance; an axis effect counts
  only if it **exceeds** the within-cell run spread.

**Operator-supplied parameters (to be fixed in §8 *before* running, then frozen):** the concrete models
for CAP−/CAP+ and the vendor pairs for IND−/IND+. The design is vendor-agnostic; the identities plug in
here and are then sealed. *Capability-comparability* between the two IND levels is asserted by a
pre-registered proxy (public benchmark tier of the two models), declared, not assumed.

## 4. Targets and materials

- **Ground truth.** Published **Matters Arising / formal errata / retraction notices** whose defect is
  **reconstructible from the target text** and **third-party-adjudicated**. Each target sealed with its
  mechanism-class label held by a keeper.
- **Pre-registered target N.** Grow from 7 toward **N ≥ 18**, with **≥ 6 per mechanism class** (GR / ED /
  DR) so each class has minimal power. If sourcing cannot reach ≥ 6 in a class by the collection
  deadline, we **report the achieved N per class** and down-scope the corresponding hypothesis to
  descriptive — we do not pad with weaker targets.
- **Decoys.** Cross-domain artifacts with **no** known formal defect, **≥ 1 per target**, to measure
  false positives.
- **Class taxonomy is frozen here** (GR / ED / DR) with the assignment rule: GR = reconstructible from
  the text by general reasoning (arithmetic, internal contradiction, definitional entailment); ED =
  resolvable only against an outside source; DR = requires re-deriving a domain quantity. Ambiguous
  targets are adjudicated to a class **by the keeper before unblinding**, and dual-class targets are
  excluded.
- **Anonymization.** Public artifacts carry only `(mechanism, class, per-cell landing, counts)`; no paper
  identities, PMCIDs, or DOIs. Naming a paper beside a "missed defect" adds nothing to any statistic and
  risks defamation — excluded by red line.

## 5. Adjudication (blind)

- **Landing rule (frozen):** a finding lands iff it hits the **same locus** in the target **and** the
  **same mechanism** as the sealed defect. Locus-only or mechanism-only ⇒ no landing.
- **Blind adjudication:** a fresh, isolated instance with **relabeled pairs, neutralized targets, no key,
  no class labels** re-adjudicates every produced finding, as in the existing 14-pair check. Report
  **inter-adjudicator agreement (Cohen's κ)** against the coordinator; pre-registered acceptance κ ≥ 0.8.
- **Contamination invariant:** no instance that has seen the labels acts as an auditor or adjudicator on
  the same target.

## 6. Analysis plan (pre-registered, effect-size-first)

- **Primary model.** Mixed-effects logistic regression `land ~ CAP * IND * class + (1|target) + (1|run)`.
  Report **effect estimates with 95% CIs**, not p-values alone. Given small cell counts, the
  **confirmatory test** is a **pre-registered permutation test** on the two contrasts of interest:
  (i) the IND effect on ED at fixed CAP, (ii) the CAP effect on DR at fixed IND. 10,000 permutations of
  the factor labels within class; two-sided; α = 0.05.
- **Decision rule (frozen).** The **two-axis dissociation is confirmed** iff **all** hold: (a) IND+ raises
  ED recovery at fixed CAP with CI excluding 0; (b) CAP+ raises DR recovery at fixed IND with CI excluding
  0; (c) the **cross-effects** (IND on DR, CAP on ED) are near-null (CIs overlapping 0 and smaller in
  magnitude than the primary effects); (d) specificity S holds (decoy FP ≈ 0 every cell); (e) each effect
  **exceeds** the within-cell run-to-run spread.
- **Falsification (frozen).** If (a)&(b) fail while a *single* factor lifts **both** ED and DR ⇒ report a
  **single latent axis**. If neither factor separates the classes ⇒ **null**. Either way the result is
  reported at full prominence; §6 is rewritten to match, up or down.
- **No optional stopping.** N and k are fixed before collection; we do not peek-and-extend. Any change is
  a logged deviation (§9).

## 7. Power and honesty about limits

With N ≥ 18 (≥ 6/class) and k ≥ 3 runs across four cells this remains a **small** study; it can detect a
**large** axis-separation effect, not a subtle one. We pre-commit to reporting the achieved power and to
**not** upgrading "no detected cross-effect" into "proven orthogonality" — absence of a detected
interaction is bounded by n, and we will say so. This study raises the evidence from *descriptive on 7*
to *tested on a decoupled design*, which is a genuine step; it does not make the axes a theorem.

## 8. Operator parameters — FREEZE BEFORE RUNNING (fill, commit, then collect)

**Vendor assignment (fixed by operator access: Claude = engine nature; ChatGPT Pro = different vendor,
two capability tiers; Gemini free = a low-capability third-vendor point).**

| cell | vendor | capability tier | model string (pin current tier name before freezing) |
|---|---|---|---|
| (CAP−, IND−) | Claude (engine nature) | low | `__________` (e.g. the smaller role model) |
| (CAP+, IND−) | Claude (engine nature) | high | `__________` (e.g. the governor-tier model) |
| (CAP−, IND+) | ChatGPT (Pro) | low | `__________` |
| (CAP+, IND+) | ChatGPT (Pro) | high | `__________` |
| (CAP−, IND+′) robustness | Gemini (free) | low | `__________` |

- **Capability-comparability proxy (declare, do not assume):** the pairing of Claude-high ↔ GPT-high for
  the IND contrast at high capability, and Claude-low ↔ GPT-low (↔ Gemini-low) at low capability, is
  justified by `__________` (public benchmark tier of each model as of the freeze date). Gemini-free is
  used **only** as a low-capability IND+ point; it is **not** paired against a high-capability model,
  because free-tier capability is not comparable to the top tiers — noted so the comparison stays honest.
- **Independence semantics:** IND− = the engine's own nature (Claude-family); IND+ = a genuinely
  different vendor (GPT, or Gemini for the robustness point). Cross-vendor runs require the operator's
  own accounts/adapters; they cannot be produced from inside the engine.
- k (runs per cell, ≥ 3): `____`  · target N and per-class counts: `____ (GR __ / ED __ / DR __)`
- Keeper (holds labels, does not audit): `__________` · Adjudicator instance: `__________`
- Collection window: `__________`

*Model strings, k, N, keeper and window are still to pin. Once filled, commit this section in a second
registration commit. Data collection may begin only after that commit.*

## 9. Deviations log (append-only, post-registration)

*(empty at registration)*

---

*This is a pre-registration, not a result. It reaches no verdict and validates nothing: even a clean 2×2
sits at independence level ≤ 3 in a single lab, and the residue — external replication by other hands —
is the engine's own non-closure applied to its own empirical claim. Red line: flag, not accuse;
anonymized targets; no personalized financial or legal advice anywhere in the pipeline.*
