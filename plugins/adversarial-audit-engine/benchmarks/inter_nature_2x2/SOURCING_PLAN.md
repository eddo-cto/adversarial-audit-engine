# Sourcing plan — pre-specified sampling frame for the sealed target set

*Registered addendum to `PREREG_empirical_strengthening.md`. Fixed BEFORE the pull so target selection
cannot be cherry-picked to confirm the dissociation. The keeper (not an auditor instance) executes this;
the assistant surfaces candidate *pointers* only and never reads or classifies a target's defect.*

## What counts as a target (recap of the rubric)

Formal, third-party-adjudicated defect · text-reconstructible locus · single, classifiable mechanism
(GR / ED / DR) · not misconduct · sealable and anonymizable. Grow to **N ≥ 18, ≥ 6 per class**; if a
class cannot reach 6 by the collection window, report the achieved N and down-scope — **do not pad**.

## Honest finding on pool quality (measured 2026-08-08)

A mechanical pull of the Crossref `update-type:correction` feed (100 records sampled) is **low yield**
for our purpose: it is dominated by `Author Correction` / `Publisher Correction` and trivial errata
(affiliations, figures, typos), which are *not* substantive, text-reconstructible scientific defects.
So the naive "corrections" feed is **not** the frame. The two frames below are.

## Frame A (primary) — Nature-portfolio *Matters Arising*

Third-party, peer-reviewed scientific challenges to a specific claim in a paper < 18 months old,
published alongside the authors' Reply. Highest-quality ground truth for GR/ED defects.

- **Pull:** `python3 pull_candidates.py --frame matters --from <D0> --until <D1> --rows <R> --out A.csv`
  (bibliographic query; noisier — the keeper discards non-Nature "Review of:" hits).
  Also browsable per journal, e.g. the *Matters Arising* article list of Nature, Nature Communications,
  Nature Human Behaviour, Nature Methods, etc.
- **Order rule (frozen):** sort by publication date descending; screen in that order; take the first
  that pass the rubric until the per-class quota is met. No skipping to find "better" cases.

## Frame B (secondary) — Retraction Watch DB, reason = *Error*

The only source that carries the *reason*, which Crossref lacks. Use it to add substantive-error targets
while **excluding misconduct**.

- **Pull:** download the Retraction Watch database (open, hosted via Crossref, updated daily); filter
  `Reason` **contains** "Error" and **excludes** "Misconduct / Falsification / Fabrication / Plagiarism /
  Image". Then keep only text-reconstructible, single-mechanism cases.
- `pull_candidates.py --frame retraction` gives the retraction *pointers* from Crossref, but the reason
  screen must be done against the Retraction Watch CSV.

## Frozen parameters (fill before the pull, then commit)

- Collection window `<D0>`–`<D1>`: `__________`  · rows per frame `R`: `____`
- Quotas: GR `6+` / ED `6+` / DR `6+` (adjust only upward)
- Keeper (screens + seals; is NOT an auditor nature): `__________`
- Decoys: for every sealed target, one cross-domain artifact with no known formal defect.

## Contamination boundary (non-negotiable)

The assistant (same nature as auditor A) may surface candidate *pointers* (DOIs, titles, links) but does
**not** read or classify the defect. The keeper opens each correction/Matters-Arising, decides
eligibility, and seals `(locus, mechanism, class)` privately. Sealed labels never enter any auditor run.
The public artifact carries only `(mechanism, class, per-cell landing, counts)` — never paper identities.
Red line: flag, not accuse.
