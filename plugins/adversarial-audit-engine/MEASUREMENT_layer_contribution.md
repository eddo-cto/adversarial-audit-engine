# Layer-contribution measurement — the basis for `REQUIRED_LAYERS`

`REQUIRED_LAYERS` (in `aae/run_manifest.py`) is **not assumed** — it is read from measured
per-layer contribution across real runs. This is that measurement, consolidated over **10 runs**
spanning **8 artifact classes**, each run through the deterministic core so the emitting layers'
contribution is taken from the data (`source_role`), not self-report.

## Findings per emitting layer, per run

| run (class) | verifier | reasoner | propagator | deep_causal |
|---|---:|---:|---:|---:|
| finance (fiere IEG/FM/GL) | 12 | 0 | 7 | 3 |
| finance (Sys-Dat) | 4 | 2 | 3 | 0 |
| paper (round-9 self-audit) | 8 | 0 | 3 | 0 |
| paper (arXiv) | 5 | 1 | 5 | 1 |
| code | 3 | 2 | 3 | 1 |
| spec | 3 | 2 | 2 | 1 |
| auction | 3 | 2 | 4 | 1 |
| geography | 4 | 3 | 2 | 1 |
| category_theory | 3 | 4 | 2 | 0 |
| family_law | 3 | 3 | 2 | 1 |
| **present in** | **10/10** | **8/10** | **10/10** | **7/10** |

(Scaffolding layers — triage, oracle, governor — emit no findings by design; they are measured
from their own outputs: triage from its decision record, oracle from the distinct cited sources,
governor from the meta verdict. They ran in 10/10.)

## What the data says

- **verifier** and **propagator** emit in **10/10** runs, across every class including the abstract
  one (category theory). Load-bearing everywhere → **REQUIRED**.
- **triage, oracle, governor** are the always-run scaffolding (10/10) → **REQUIRED** (by role, now
  measured).
- **reasoner** is **8/10** — it produced *nothing* in the two runs (fiere-finance, round-9-paper)
  whose defects `verifier`+`propagator` already covered. **Contextual, not irreducible → OPTIONAL.**
- **deep_causal** is **7/10** (skipped on thin/abstract artifacts) → **OPTIONAL**.
- **external_auditor** is **0/10** (never exercised under a single vendor) → independence-conditional,
  **OPTIONAL**.

## Correction the consolidation forced (why we measure before freezing)

The round-15 minimum, frozen on a smaller 5-run sample, wrongly included **reasoner** — because those
five runs all came from one measurement session where reasoner happened to fire. The two earlier runs
(built differently) show it is not irreducible. The ten-run consolidation **removed reasoner from
`REQUIRED`** (round 18). This is exactly why the hard, non-bypassable gate was not switched on until
the minimum was consolidated: an unmeasured minimum would have made a valid run INVALID (over-strict)
or hidden a real gap.

**`REQUIRED_LAYERS = (triage, oracle, verifier, propagator, governor)`.** Revisable as more runs
accumulate; still single-vendor and n=1 per class, but stable across 8 heteronormed domains.
