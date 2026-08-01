# Real-error validation — reproducible (Matters Arising ground truth)

```bash
python3 reproduce.py          # recompute every value, check vs claims.json
```

No dependencies. Pure standard library. A test and the CI workflow run it on
every push.

## Read this first: what this benchmark is, and is not

This is **method calibration**, not a product accuracy sheet. The lens was run,
blind, on real published papers that later received a **Matters Arising** — a
formal refutation written by an independent domain expert. The refutation's
central claim is the real defect; the lens never saw it. That gives a rare thing:
**external, third-party ground truth** for whether the discipline holds on *real*
errors, not just synthetic ones.

The value here is **not** "how many errors it catches." It is three
domain-independent facts about the *method*:

1. **It does not hallucinate.** 0 false positives on cross-domain decoys,
   confirmed across two blind adjudicators — the same virtue measured on the
   synthetic side (1/42). This is a property of the discipline (defense-gate +
   admissibility), so it transfers to any artifact, not just papers.
2. **Its boundary is declarable.** It lands on defects reconstructible from the
   text by **general reasoning** — arithmetic that will not reconcile, an
   internal contradiction (a figure that disagrees with a table), a definitional
   entailment. It **misses** defects that need **domain re-derivation**
   (re-integrating a model's equations, recomputing a physical quantity) or
   **external data**. That is the engine's declared out-of-scope class, now shown
   on real errors.
3. **The synthetic estimate is kept honest.** Real P-class recall is **1/4 (25%)**
   against the synthetic **88%** (`benchmarks/calibration`). The drop is signal:
   the synthetic "present" defects were simple; the real ones needed domain
   re-derivation. Publishing the drop is the point — it is why the 88% is not
   oversold.

The one clean positive was a paper that was **actually retracted**: blind, from
the text alone, the lens reconstructed the retraction's real reason (an internal
figure-vs-table contradiction inflating tiny effects). That is the boundary
working, not a detector scoring a hit.

## Why the honest number is a strength, not an own-goal

25% "recall on real errors" reads as weak only if you mistake this for a detector
scoreboard. It is not. A tool that **declares what it cannot do** — and backs the
declaration with external ground truth and near-zero false positives — is the
honest counterpart to LLM-as-judge products that overclaim. The engine's value is
the *declarable boundary + the low-false-positive discipline*, and both are
exactly what a downstream user (an integrity office, or any of the engine's other
domains) inherits.

## Files

| file | content |
|---|---|
| `dataset_targets.csv` | 7 rows: `id, block, target_class, mechanism, landed, adjudicator_dependent, extraction_confound` |
| `dataset_decoys.csv`  | 7 rows: `id, block, false_positive` |
| `claims.json`         | the values `reproduce.py` checks the data against |
| `reproduce.py`        | recompute specificity, the boundary, and the synthetic→real calibration |

## Anonymization

The papers are real and the defects are real (identified by third parties, not by
us). Naming a paper beside a "missed defect" adds nothing to any statistic and
risks misreading, so this public extract carries only `(class, mechanism,
landed)`. PMCIDs, DOIs, the sealed Matters-Arising targets, the blind audits and
both adjudications live in the **private sealed registers**.

## Declared limits

`n = 7` (4 of class P) — too small for significance; this **circumscribes** the
claim, it does not certify it. Matters Arising are *conclamated* errors (grave
enough to warrant a formal rebuttal), not a representative sample. One target
(T6, class A) is adjudicator-dependent; one (T7) was confounded by text
extraction dropping the governing equation. And it is a **single model nature**:
no number here reaches VALIDATED without the external **inter-nature** axis, the
one test the engine cannot run on itself.
