# Inter-nature check — reproducible

```bash
python3 reproduce.py          # recompute every value, check vs claims.json
```

No dependencies. Pure standard library. A test and the CI workflow run it on
every push.

## The one test the engine cannot run on itself

Every auditor instance the engine can launch shares one **nature** (one model
family). Intra-nature agreement therefore tends to 1 and proves nothing about
independence — it could be a shared training prior rather than a property of the
task. The only way to find out is to hand the **same** artifacts, blind, to a
**different nature** (a different-vendor model) and see what survives.

That is this benchmark. The same 7 real-error targets from the real-error
validation (`../real_errors`, Matters Arising ground truth) were audited **blind**
by three natures — **A** = the engine's own nature, **B** and **C** = two
different-vendor models — with the identical protocol, then adjudicated by a
**fresh blind instance** (relabelled pairs + cross-domain decoys, no access to any
prior result). Anonymized: no vendor names, no paper identities; only
`(mechanism, per-nature landing)`.

## What it certifies — the three predictions, all confirmed

1. **The boundary is nature-independent.** On all 4 P targets the three natures
   give the *identical* landing pattern: they land only on the
   general-reasoning-reconstructible defect (1/1) and miss every one that needs
   domain re-derivation (0/3). The declarable boundary is a property of the
   **task**, not of one model family.
2. **A different nature adds real findings the engine's own missed** — on the
   A-class (external-data) targets the landings go 0 → 2 → 3 across natures, and
   the gain is not saturated (C catches one that B also missed). This is ρ<1:
   different natures are complementary, not redundant.
3. **The low-false-positive discipline survives independence.** 0 false positives
   on cross-domain decoys for *every* nature, including the fresh blind
   adjudicator. The engine's one strong virtue — it does not hallucinate — is not
   a shared prior of its own nature.

## Files

| file | content |
|---|---|
| `dataset_landings.csv` | 7 rows: `id, mechanism, nature_A, nature_B, nature_C` (blind landing 0/1) |
| `dataset_decoys.csv`   | per-nature cross-domain decoy false positives |
| `claims.json`          | the values `reproduce.py` checks the data against |
| `reproduce.py`         | recompute the boundary concordance, the A-class gain, the specificity |

## Why this matters for the whole method

This is the rung the engine's own independence scale points to and cannot reach
alone. It moves the real-error result from level 1–2 (single nature) toward level
3 (different vendor). It is **not** VALIDATED — closure still belongs to an
external human eye (level 4) — but it is the evidence the validity ceiling
required, and it is positive: the boundary and the no-hallucination discipline
that the engine's other domains inherit are task properties, not artifacts of one
model.

## Declared limits

`n = 7`, one run per nature, and the adjudication (though independently
re-confirmed blind) rests on a strict same-locus-same-mechanism rule that has
some judgment at the margin (two A-class targets). Matters Arising are conclamated
errors, not a representative sample. No number here reaches VALIDATED without the
external human eye.
