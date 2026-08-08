# `inter_nature_2x2` — the decoupled capability×independence study (§6 strengthening)

This benchmark holds the **analysis machinery** and **data schema** for the pre-registered 2×2
factorial that answers the one criticism §6 could not: is the capability/independence dissociation two
separable axes, or one latent axis? The full design, hypotheses, and frozen decision rule are in
`papers/system-description/PREREG_empirical_strengthening.md`. **This directory is written before the
data exist**; the analysis is validated on synthetic ground truth, so the pipeline is trustworthy
independently of any real result.

## Files

- `analyze_2x2.py` — pure-stdlib analysis: per-cell recovery, the two pre-registered contrasts
  (IND→ED at fixed CAP; CAP→DR at fixed IND) plus the two cross-effects, a two-sided permutation test,
  a target-resampling bootstrap CI, and the frozen verdict. `python3 analyze_2x2.py --selftest`
  reproduces a clean dissociation → `DISSOCIATION_CONFIRMED` and a single-axis confound → `SINGLE_AXIS`.
- `landings_TEMPLATE.csv`, `decoys_TEMPLATE.csv` — the input schema (delete the dummy rows).

## Run

```bash
python3 analyze_2x2.py landings.csv decoys.csv     # prints per-cell table, contrasts, VERDICT
python3 analyze_2x2.py --selftest                  # validates the machinery on synthetic truth
```

## Verdict semantics (frozen in the prereg)

- `DISSOCIATION_CONFIRMED` — IND lifts ED (CI excludes 0, effect > run spread) **and** CAP lifts DR,
  **and** both cross-effects are near-null, **and** decoy false-positive rate ≤ 2%.
- `SINGLE_AXIS` — one factor lifts **both** classes: the two-axis claim is falsified.
- `NULL` — neither factor separates the classes.
- `INCONCLUSIVE_SPECIFICITY` — decoys started firing; the recovery signal is contaminated.

We commit in advance to reporting whichever verdict the data give, at full prominence.

## Sourcing rubric — for the KEEPER, not the auditor (contamination invariant)

Growing the sealed target set is the **keeper's** job, because whoever reads a target's defect must not
also audit it — and the engine's own nature (nature A / Claude) is one of the auditors. An auditor
instance must never receive this rubric's *outputs*. A target qualifies iff **all** hold:

1. **Formal third-party ground truth.** A published *Matters Arising*, formal *erratum/corrigendum*, or
   retraction notice states a specific, adjudicated defect. Author self-corrections without third-party
   adjudication do **not** qualify.
2. **Text-reconstructible locus.** The defect sits at an identifiable locus in the *target text* (a
   number, a step, a claim), so a blind auditor could in principle reach it.
3. **Single, classifiable mechanism.** The defect maps to exactly one class:
   - **GR** — reconstructible from the text by general reasoning (arithmetic, internal contradiction,
     definitional entailment);
   - **ED** — resolvable only against an outside source;
   - **DR** — requires re-deriving a domain quantity.
   Dual-class or ambiguous targets are **excluded** (recorded, not forced).
4. **Sealable.** The keeper can store `(locus, mechanism, class, source)` privately; the public artifact
   carries only `(mechanism, class, per-cell landing, counts)` — never paper identities (PMCID/DOI).
5. **Decoy partner.** For every target, a cross-domain artifact with **no** known formal defect is added
   to the decoy pool.

Target counts (prereg): **N ≥ 18, with ≥ 6 per class**. If a class cannot reach 6 by the collection
window, report the achieved per-class N and down-scope that hypothesis to descriptive — do not pad.

## What this directory does NOT contain

No real landings yet, and — by construction — nothing that reaches `VALIDATED`. Even a clean
`DISSOCIATION_CONFIRMED` sits at independence level ≤ 3 in a single lab; the residue is external
replication by other hands. Red line: the engine flags, it does not accuse; targets stay anonymized.
