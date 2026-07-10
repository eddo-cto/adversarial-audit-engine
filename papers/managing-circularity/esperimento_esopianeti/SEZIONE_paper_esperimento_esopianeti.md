# Experiment: a high-N, open instantiation of survivor reliability on an independent scientific ledger

*Draft experimental section for the second paper (bridge / domain-independence). Measured tone,
anti-hype. All figures from real data; reproducibility artifacts (TAP queries) are listed in §E.7.*

## E.1 Why this testbed, and what we claim from it

The thesis of this paper is structural: circularity in AI-on-AI evaluation is not a bug to be
removed but a coordination problem to be made virtuous, and the device that makes it virtuous is
the *accumulation of independent domains* — a survivor earns reliability by surviving independent
attempts to falsify it, with an explicit indeterminate state where evidence has not yet closed.
To show that this structure is not an artifact of our own construction, we instantiate it on a
mature scientific reliability ledger built and maintained by a community with no connection to
this work: the Kepler Objects of Interest (KOI) catalogue of the NASA Exoplanet Archive.

We make a deliberately modest claim. We do **not** claim to discover anything about exoplanets.
We claim that an independently-maintained, high-volume reliability taxonomy, when read through the
lens of this paper, exhibits — quantitatively and on open data — the three features the theory
predicts: a graded verdict with a genuine indeterminate tier (C₃), a survivor gate in which a
single independent falsification is decisive (a floor), and a reliability *profile* that carries
information the final verdict conflates. A companion test on a physically independent measurement
channel supplies the non-circular corroboration that the internal analysis, by construction,
cannot.

This testbed was reached by a documented route. A preliminary pilot on medieval-name etymology
(n≈7, open corpora) did not yield clean data, but it earned the selection criteria we then used:
a domain contributes to accumulation only if it is (i) independent by provenance, (ii) high in
precision, and (iii) informative about the ground truth. The exoplanet ledger was chosen because
those three conditions are naturally and abundantly satisfied there, on open, deterministically
queryable data — not for novelty.

## E.2 Data and the mapping to C₃

The KOI cumulative table records, for each transiting-planet candidate, a disposition in three
classes that map exactly onto the truth quantale C₃ = {⊥ < k < ⊤} of this paper:

    FALSE POSITIVE (⊥)   <   CANDIDATE (k, indeterminate)   <   CONFIRMED (⊤)

with, in the retrieved snapshot, 4 839 / 1 978 / 2 746 objects respectively (N = 9 563 after
discarding one row with a corrupt flag value). The archive additionally records four *independent
false-positive diagnostics*, each a distinct physical cross-check that can falsify the planet
claim: not-transit-like (light-curve shape), stellar-eclipse (binary), centroid-offset
(astrometric contamination), and ephemeris-match (period–epoch contamination). A continuous
vetting score `koi_score` records positive confirmation. The four diagnostics are our independent
domains; passing all four is survival; `koi_score` is the positive-accumulation axis toward ⊤.
The diachronic axis of the theory is instantiated not as calendar time but, as the theory
requires, as the accumulation of independent lines.

## E.3 Run 1 — internal instantiation (with its caveat stated first)

Because the four diagnostics and the disposition are produced by the same vetting pipeline, this
first analysis is in part *definitional*: it shows that the field's own reliability taxonomy
realises the paper's structure, and quantifies the separation, but it is not by itself
non-circular evidence. We state this before the numbers, not after.

Accumulation tracks the verdict. The mean number of independent falsifications is 1.40 for
FALSE POSITIVE against 0.004 for the rest (permutation test, p < 0.001). The gate is sharp:

| independent falsifications | ⊥ FALSE POS | k CANDIDATE | ⊤ CONFIRMED |
|---|---|---|---|
| 0 | 95 | 1 975 | 2 729 |
| 1 | 3 210 | 3 | 17 |
| ≥2 | 1 534 | 0 | 0 |

A single independent falsification is decisive: P(⊥ | ≥1 falsification) = 99.6 %, and 99.4 % of
CONFIRMED objects pass all four checks. This is the survivor gate as a floor — the dual, on the
falsification side, of the join on the confirmation side. Among survivors (zero falsifications,
n = 4 799) the residual ⊤-versus-k split is not decided by the diagnostics (all zero) but by the
positive axis: mean `koi_score` is 0.04 / 0.80 / 0.96 across ⊥ / k / ⊤. The indeterminate tier k
(CANDIDATE) spans the entire score range, so the final verdict conflates trajectories that the
profile separates — the empirical shadow of the interleaving distance of the first paper.

## E.4 Run 2 — external, non-circular corroboration

The load-bearing test uses a channel physically independent of transit photometry: a mass
measured by radial velocity or dynamics (`pl_bmassprov = 'Mass'`), i.e. a Doppler/gravitational
observable produced by different instruments and pipelines than the transit vetting. Of the 290
Kepler planets carrying such an independent mass, 249 join by name to the KOI table. All 249 are
CONFIRMED in the transit taxonomy, and their transit-diagnostic profile is:

- 242 (97.2 %) pass all four independent transit falsifications;
- 6 carry the stellar-eclipse flag, 1 the not-transit-like flag.

The agreement of two physically distinct channels at 97 % is not definitional. More telling are
the seven discordant objects: real planets, confirmed by an independent channel, that the transit
domain alone would have down-graded. Physically these are unsurprising (genuine hot Jupiters can
show a detectable secondary eclipse, which the radial-velocity channel resolves). Structurally
they are the thesis in miniature, on real data: an independent domain correcting the error of a
single domain — accumulation buying reliability that no one line could supply.

## E.5 Independence diagnostic

Accumulation is only meaningful over lines that are actually independent. Across all KOIs the six
pairwise φ-coefficients among the four diagnostics are −0.23, +0.01, +0.06, +0.15, +0.10 and
+0.52. Five of six are near zero — the diagnostics fail for different reasons — while
centroid-offset and ephemeris-match are moderately correlated (+0.52), which we report rather than
smooth over: those two share contamination-detection logic and are, to that extent, not fully
independent. Independence here is a property established by construction (distinct physical tests)
and monitored, not assumed; the one correlated pair is a declared exception.

## E.6 Limitations

Three, stated plainly. First, Run 1 is partly definitional (shared pipeline); it is offered as
instantiation, not proof, and the non-circular weight rests on Run 2 and on the independence
diagnostic. Second, Run 2 is subject to follow-up selection: radial-velocity mass is measured
preferentially on promising targets, so the test establishes concordance on the positive class
and the rescue cases, not a full error-rate curve — false positives receive no radial-velocity
follow-up and are therefore untestable by this route. Third, the join covered 249 of 290
independent-mass planets; 41 were lost to name-format mismatch. None of these is hidden; each
bounds the claim.

## E.7 What the experiment establishes, and reproducibility

On open, high-volume data from an independent community, the paper's abstract structure —
graded C₃ verdict, survivor gate as a floor under independent falsification, reliability profile
beyond the final value — is realised, and a physically independent channel corroborates it
non-circularly, including cases where the independent line overrides a single domain. The result
is a feasibility demonstration of the mechanism on a real reliability ledger, not a claim about
exoplanet science. Every figure derives from ADQL queries against the NASA Exoplanet Archive TAP
service (endpoint `https://exoplanetarchive.ipac.caltech.edu/TAP/sync`, `format=csv`), which are
permanent, re-runnable artifacts; the queries and the deterministic analysis are archived with
this paper.
