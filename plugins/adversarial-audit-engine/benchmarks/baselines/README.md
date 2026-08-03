# Baseline positioning — reproducible

```bash
python3 reproduce.py          # recompute every value, check vs claims.json
```

No dependencies. Pure standard library. A test and CI run it on every push.

## What this is — and is not

This is **positioning against open, same-task baselines**, not a leaderboard and
not a claim to beat anyone. It isolates what the engine's **discipline**
(defense-gate, admissibility, declared boundary) adds over an *undisciplined* use
of the same model, on the 7 real-error targets from `../real_errors`.

Two baselines, two questions:

- **A strong LLM judge, vanilla vs disciplined.** The *same strong model* is run
  twice on each paper: once with a naive prompt ("find all the flaws, be
  thorough") and once under the engine's protocol. Only the discipline differs.
- **statcheck** (deterministic, OSS, GPL-3.0). A stats-consistency checker that
  recomputes reported p-values. Narrow and format-fragile.

Anonymized: no vendor is named; the data is only finding counts, landing, and
mechanism class. Blind adjudication against the sealed targets; identities stay in
the private registers. Red line: flag, never accuse.

## What it shows (all reproduced by `reproduce.py`)

1. **Discipline does not change *which* targets are caught.** Landing is
   **identical** per-paper between the vanilla and disciplined runs (both 4/7,
   same targets). The engine's value is *not* higher recall.
2. **It cuts the noise ~5×.** The vanilla judge emits **~88 findings per paper**
   vs **~18** under discipline (overall 5.0×; per-paper mean 5.2×, range
   2.5×–8.4×). The real catches are buried among ~70 speculative "you didn't
   measure X" findings per paper — exactly what the defense-gate downgrades. This
   is the **false-alarm proxy**, and it is the differentiator.
3. **The boundary is the task's, not the discipline's.** The 3 targets missed by
   both arms are exactly the **domain-re-derivation** class (recompute a formula,
   re-integrate equations, recompute a physical quantity). They are missed even by
   a **155-finding firehose** — because they need *executing* the re-derivation,
   which no text-only auditor does.

`statcheck` lands **0/7**: its class (APA-style NHST p-values) is disjoint from
these real defects, and it is format-fragile on full text. It measures
class-breadth, not a head-to-head.

## Why this matters

It grounds, on real errors, what the 2026 LLM-as-judge literature calls
"reliability without validity": a strong judge is consistent and prolific but
**uncalibrated** — it over-flags and declares no boundary. The engine's discipline
does not catch more; it catches the same, with **~5× fewer false alarms and a
declared boundary**. That is the honest, defensible position — the value is the
*discipline*, not a recall crown.

## Files

| file | content |
|---|---|
| `dataset_llm_judge.csv` | 7 rows: `id, mechanism, n_vanilla, n_disciplined, landing_vanilla, landing_disciplined` |
| `dataset_statcheck.csv` | 7 rows: `id, mechanism, statcheck_landing` |
| `claims.json` | the values `reproduce.py` checks against |
| `reproduce.py` | recompute landing concordance, over-flagging (mean + range), the class boundary |

## Declared limits

`n = 7`; one vendor for the LLM baseline; the over-flagging count is a **proxy**
for false positives (the landing findings and the arithmetic structurals are real;
the proxy is the ~70 speculative findings per paper the defense-gate would
downgrade). The over-flagging ratio **varies with the paper** (lowest where the
honest answer is already cautious, or the paper is genuinely broken; highest on
complex-but-sound papers) — reported *with* its range. The landing calls have
been **re-adjudicated blind by a fresh, isolated instance** (relabelled pairs,
targets neutralised, no key, no class labels): it reproduced the per-paper
landing **identically** to the coordinator on all pairs, so the recall and the
0-false-positive figures do not rest on coordinator judgment. What remains
un-blinded is only **closure**: two same-nature adjudicators dissolve the
coordinator bias but stay at independence level 1–2 — no number reaches VALIDATED
without the different-nature axis and, ultimately, the external human eye.
