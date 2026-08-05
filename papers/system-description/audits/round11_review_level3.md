# Round-11 — Level-3 adversarial review (first different-vendor audit)

*Verbatim review produced by a machine of a **different vendor** than the engine's roles. By the engine's
own scale this is independence **level 3** — it raises the axis but validates nothing; closure remains
human. It reproduced the four benchmark guards, then upheld findings against §6's central claims and the
two closure residues. Its disposition was **major revision, not rejection**. Every item was re-derived by
execution before being applied; §6/§3/§7 were scoped and the two closure guarantees (C1, C2) were built
in code (round 11). Kept in full, per the paper's own rule that a system built on adversarial honesty
must show the audits that caught it — including the different-vendor one that caught the headline
over-claim two same-vendor rounds had missed.*

---

## Standing

This is a different-vendor machine review. It raises the independence axis to level 3 under the paper's
terminology, but it does not validate the system. The final closure remains human. The review separates
**execution findings** (established by running or inspecting the supplied code and data) from **argument
findings** (conclusions about what the evidence permits the paper to claim).

## 1. Reproduction record

Verified by execution — all four quantitative benchmark guards reproduced and exited successfully
(`calibration`, `real_errors`, `inter_nature`, `baselines` each exit 0). The perturbation guard also
works (`test_benchmarks_guards` OK). **Did not reproduce:** the claimed unit-suite result `Ran 145 tests
… OK` — from the supplied *review bundle* only (the bundle shipped the core modules loose, not the `aae`
package, so `unittest discover` errored). Reproduces at the Git tag; the bundle was incomplete. (Bundle
packaging fixed for future reviews.)

## 2. Findings ledger (as delivered)

- **R-01** — the review *bundle* does not reproduce §8 in full. UPHELD against the bundle; unresolved
  against the Git tag. (Bundle issue, not a paper defect.)
- **F-01** — §8 reproduces the published *summaries* (CSV vs `claims.json`), not the §6 *experiment*
  (selection, defect classification, raw findings, vendor identity, blind adjudication). UPHELD — §8
  understates how much of §6 remains privately attested.
- **F-02** — the sample shows a descriptive dissociation, **not** identified orthogonal frontiers: one
  run per nature, n=7, "nature" confounds capability/tools; permutation p=0.007 shows the class
  segregation is non-arbitrary but does not establish causal orthogonality. UPHELD (the central point).
- **F-03** — §3's `DefectClass` taxonomy is not the taxonomy tested by §6 (general-reasoning /
  external-data / domain-re-derivation); no crosswalk shipped; P/A does not carve the boundary either.
  UPHELD — load-bearing category slippage.
- **F-04** — the "iff" footprint conflicts with the table (external-data recovered by B/C) and with the
  code (`adjudicate()` auto-routes only `NON_LOCAL_CONCEPTUAL_NOVEL`). UPHELD — wording/logic defect.
- **F-05** — the level-3 residue is more load-bearing for §6 than §7 admitted: the inter-nature argument
  depends on B/C being different vendors, and the public data carries only `nature_A/B/C` labels.
  PARTIALLY UPHELD.
- **F-06** — "does not hallucinate" is stronger than 0/7 supports (exact upper 95% bound ≈ 41%).
  FLAGGED, not condemned.
- **F-07** — the baseline establishes lower finding *volume*, not fewer *false alarms* (non-target
  findings are not adjudicated). PARTIALLY UPHELD; the "proxy" caveat is present.
- **F-08** — the runtime prints an absolute guarantee it does not enforce (a non-empty
  `AAE_HUMAN_ATTESTATION` preserves VALIDATED while governor_check prints the never-VALIDATED rule).
  Operational wording overclaims. (Closed in round 11: closure is now a verified HMAC.)
- **F-09** — "coordinator bias is dissolved" is too categorical (shared same-vendor rubric/selection
  bias remain). UPHELD — honesty-language defect.
- **F-10** — §9/§10 present the cleanest four-defect narrative rather than the full finding accounting.
  MOSTLY DEFENDED; flagged.

## 3. Overall assessment

**Survives:** the four benchmark summary scripts reproduce; their strict guards are non-vacuous; the
seven inter-nature rows contain a genuine descriptive pattern; the paper's disclosures (human token,
claimed vendor identity, small sample, false-alarm proxy, same-vendor self-audits) are materially more
candid than ordinary system papers; the audit history is not silently erased.

**Does not survive at the claimed strength:** the bundle's 145-test claim; a different-vendor replication
of §6 from shipped materials (only the final table recomputes); a causal dissociation of independence
from capability/tools; the match between the empirical mechanism labels and the production `DefectClass`
taxonomy; the universal `iff` / "exact footprint" / "orthogonal" / "coordinator bias dissolved" /
transferable "does not hallucinate" formulations; and the interpretation of §6 as an *independence*
result while vendor nature is claimed-but-unattested.

**Recommended disposition:** major revision, not rejection.

## 4. The one question for a human domain expert

After examining the sealed source papers, the Matters Arising, the extracted inputs and the raw model
findings: were the mechanism labels — especially the three `domain_rederivation` cases — assigned
independently of the observed model outcomes, and were those defects genuinely recoverable from the
material supplied to *every* nature rather than blocked by missing equations, domain-specific
interpretation, or unequal external-data/tool access? That determines whether the `000` re-derivation
pattern is a capability frontier or an artefact of target construction and input availability. Neither
this reviewer nor the system under review can close it from the public bundle.

---

*Applied in round 11 (tag `v1.0.4`): §6/§3/abstract scoped to a descriptive dissociation; §7 residues
C1 and C2 built in code (adapter-attested vendor level; cryptographic HMAC human closure); §9 discloses
this review. F-06/F-07/F-09 wording softened. Every applied item was re-derived by execution first.*
