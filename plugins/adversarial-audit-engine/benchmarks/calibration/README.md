# Injected-defect calibration — reproducible benchmark

This directory turns the calibration result cited in `INVARIANTI_metodo.md` §4
from *documented* into *verifiable with one command*:

```bash
python3 reproduce.py          # recompute every headline number, check vs claims.json
```

No dependencies. Pure standard library. A test
(`tests/test_calibration_repro.py`) and the CI workflow run it on every push.

## The result being reproduced

24 synthetic defects were injected into real open-access papers, one operation
each (I1–I6). Six documents per block (clean + seeded) were audited **blind**,
with cross-domain **decoys** and clean **twins** as controls, then adjudicated
against a sealed key. The headline finding:

- **The lens detects in proportion to what it can reconstruct.** Defects that
  are **present and verifiable** (a wrong number I1, a wrong denominator I2, an
  inflated *n* I6, an unlicensed causal over-claim I4) are caught **14/16 = 88%**.
  Defects of **absence** (a deleted control sentence I3, a removed null I5) are
  caught **2/8 = 25%**. One-tailed Fisher exact **p = 0.0047**.
- **It does not hallucinate.** **1 false positive / 42 controls = 2.4%**
  (Wilson 95% 0.4%–12.3%).

The mechanistic boundary (present vs absent) separates the data more cleanly
than the design boundary (reconstructive vs judgment, 10/11 vs 6/13, p = 0.027),
because I4 is a *judgment* operation that behaves like *present* (the wrong claim
is there to reconstruct) and I5 is near-*reconstructive* but behaves like
*absence* (nothing left to reconstruct).

## Files

| file | content |
|---|---|
| `dataset_injections.csv` | 24 rows: `id, operation, mechanistic_class, design_class, detected` |
| `dataset_controls.csv`   | 42 rows: `id, kind, false_positive` |
| `claims.json`            | the published headline values; `reproduce.py` fails if the data stops matching them |
| `reproduce.py`           | recompute contingencies, Fisher exact (stdlib), per-operation rates, FP + Wilson CI |

## Anonymization (why no paper is named here)

**The injected defects are synthetic.** They were seeded by us into otherwise
sound papers to build ground truth; they are **not** real defects of those
papers. Naming the source papers next to a "defect" column would imply the
opposite and cross the project's red line (flag, never accuse; no defamation).

Every headline number depends only on `(operation, class, detected)` — never on
a paper's identity — so this public extract carries exactly that and nothing
more. Each row corresponds to one adjudicated injection; within an operation the
rows are exchangeable for every statistic computed here. The full provenance
(PMCIDs, DOIs, exact injection locations, RNG seeds, blind adjudications) lives
in the **private sealed registers** and is not part of the public method core.

## Honest limits

The injections are **realistic but not real**; 88% is an estimate **by excess**.
The number is significant *on synthetic defects*. Carrying it onto *real* errors
with independent ground truth is a change of axis, not one more block — and it is
the open frontier the method itself declares, not something this benchmark
closes.
