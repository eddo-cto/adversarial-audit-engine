# Meta sub-layer — usage ledger

`aae/usage_ledger.py` is the **persistence** layer for meta-analysis of engine runs:
one append-only JSON line per run, feeding the existing bias-resistant panel in
`aae/run_metrics.py`. It is **not** a merit score.

## Three purposes (same file, different reads)
1. **Improvement telemetry** — where the engine abstains or errs too much.
2. **Historical series** — runs over time, as a dataset in their own right.
3. **Reflexive meta-level** — the engine evaluating its own evaluations.

## Two non-negotiable invariants
- **Anti-Goodhart:** no field of the ledger may become a *target* of the engine's gate.
  If it did, the engine would learn to produce good metrics instead of good audits —
  the very failure the method warns against. Telemetry **describes**, it does not decide.
- **Reflexive / non-validating:** this sub-layer is itself a self-referential evaluator,
  so it does not self-validate. precision/recall/escape stay `n/d` without external human
  ground truth; closure belongs to the human eye.

## Use
```python
from aae.usage_ledger import UsageRecord, append, now_iso, summarize
append(UsageRecord(run_id="...", data=now_iso(), dominio="...",
                   artefatto="...", ruoli=[...], verdetti={"...": n},
                   n_astensioni=0, override_umani=0, note="..."))
print(summarize())   # descriptive summary + bias flags
```
