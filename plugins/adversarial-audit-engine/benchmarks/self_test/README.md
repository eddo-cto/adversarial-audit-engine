# G self-test — the release gate for audit quality (product-health, 1.12)

The engine already measures its **Type-I** error (false demolition) via `benchmarks/type1_calibration`. This
is the missing other half: **G** — the real audit quality, i.e. how many labelled defects the engine actually
condemns (recall / Type-II) and how often it condemns a clean case (false-positive rate). The docs long said
"G is not measured"; this measures it, and turns it into a **CI gate that fails on regression**.

Not research, not a client feature: a product-health instrument. Core `aae/` is untouched; everything here is
stdlib and deterministic except the one live step — running the real engine to produce findings.

## Pieces
- `corpus_gen.py` — deterministic seeded corpus with injected defects at EXACT byte spans, in the engine's real
  domains (financial / auction / credential), plus ~20% no-defect cases. Synthetic/public text only — never client data.
- `match.py` — deterministic finding↔defect matching. A condemnation matches a defect iff its verbatim evidence
  quote (guaranteed by the grounding-gate) locates within the defect span (tolerance) and the class is
  compatible (frozen table). **No LLM-as-judge** — that would reintroduce the circularity.
- `metrics_g.py` — recall, **severity-weighted recall (primary)**, precision, F1, false-positive rate.
- `sealed_labels.py` — the only module that reads hold-out labels; refuses an optimizer (M/G separation, tested).
- `release_gate.py` — fails if severity-recall drops > δ or FP rises > δ vs the frozen baseline.
- `run_selftest.py` — orchestrator: generate → run the engine (injected auditor) → match → G → gate → exit code.

## Running it (release time, frontier model)
The auditor is the REAL engine run; local small models are not competent enough to be the auditor (measured),
so this runs where a capable model is available (Claude Code with a provider). Supply `auditor(case)->findings`:

```python
from benchmarks.self_test import run_selftest
rc = run_selftest.main(["--update-baseline"], auditor=my_engine_auditor)   # establish the frozen baseline once
rc = run_selftest.main([], auditor=my_engine_auditor)                      # later releases: gate, non-zero on regression
```

`baseline_g.json` is committed like a calibration record and never auto-overwritten (only with `--update-baseline`).

## Honesty
- A high recall with a high FP rate is **not** quality (escape alone is threshold-gameable — measured in the
  Goodhart pilot). Both are reported; the gate watches both.
- This measures the engine as a whole on a labelled corpus; it is not a per-client guarantee and never closes
  a run as VALIDATED. It catches quality regressions between releases — nothing more, nothing less.
