# Glossary — what each module and term means, in one line

Some names in `aae/` are terms of art from the method and its papers (Latin
labels like *destruens*/*construens*, coined terms like *negation spectrometry*).
They are precise and tied to the papers, so they are **not renamed**. This legend
maps every name to plain language, so the codebase is readable without the papers.

## The five layers (what a run does)

| layer name (in code/docs) | plain language |
|---|---|
| **destruens** (`triadic`) | the demolition pass: point-by-point verification + propagation of *non-local* defects (a flaw in one place that breaks a guarantee elsewhere). |
| **construens** (`construens`) | cause-of-absence diagnosis: when something expected is *missing*, work out why — with an inverted defense-gate. |
| **generative** (`discovery`) | the generative complement: find spaces where the *unvalidated* output already has standalone value. |
| **deep-causal** (`deep_causal`) | root-cause clustering, forward/backward *chiasm* prediction, and gated scenarios. |
| **meta-epistemic governor** (`meta_epistemic`) | validates the *validator*, not the artifact: coverage, independence, calibration, and apparent-consistency (self-confirmation). |

## Core modules (the deterministic discipline)

| module | plain language |
|---|---|
| `gates` | the deterministic gates and the verdict state machine (grounding · defense · independence). |
| `grounding` | anti-hallucination gate: a finding may only condemn on a quote that exists **verbatim** in the source. |
| `criterion` | the tunable decision criterion, incl. the OCR contract (a low-quality source can never reach "condemn"). |
| `independence_ledger` | emits a run's independence status: level, intra- vs inter-nature, verdict ceiling, ρ caveat. |
| `adjudication_guard` | bias-resistant adjudication as testable immunities: position, length, self-preference, cross-nature closure. |
| `negation_spectrometry` | the Type-I-error gate against **over-demolition**: measures how much the auditor demolishes on controls. |
| `support_geometry` | reads the "support geometry" of judged claims — flags the **fragile** ones (resting on a single source). |
| `evidence_pairing` | pairs a claim with the exact passage that contradicts or supports it. |
| `repr_validator` | representation validator: flags a gross numeric outlier as a data error *before* a substantive finding. |
| `run_metrics` | bias-resistant metrics panel: orthogonal rates, **no** composite score, abstention is never success. |
| `usage_ledger` | append-only run log for meta-analysis (anti-Goodhart; not a merit score). |
| `metrics` | shared metric primitives. |
| `dedup` | de-duplicates findings. |
| `schema` | core data structures (Ledger, Finding, Verdict, IndependenceLevel, …). |
| `config` | run configuration (stakes, identities, thresholds). |

## Roles, oracles and I/O

| module | plain language |
|---|---|
| `roles` | the adversarial role definitions (oracle, verifier, propagator, governor, external eye). |
| `oracle` | research-oracle machinery: a **factual** domain dossier with sources; finds no defects. |
| `orchestrator` | coordinates the roles and the deterministic core. |
| `legal_oracle` | checks, on demand, that cited legal norms **exist** and are faithfully represented — never their interpretation. |
| `normattiva_fetcher` | source connector for Italian law (Normattiva) used by the legal oracle. |
| `adapters` | cross-vendor LLM client adapters — the lever that lets the independent eye run on a **different vendor**. |
| `llm` | the LLM client interface/base. |
| `cli` | command-line entry point. |
| `triage` | quick screening pass. |

## Recurring terms

- **nature** — a model family / vendor. Same vendor, different model = still one nature (shared priors); a *different vendor* is a different nature.
- **hive** — the set of adversarial roles run together.
- **chiasm** — a forward↔backward cross-check in the deep-causal layer.
- **non-closure** — the refusal to report `VALIDATED` on internal grounds; closure belongs to a human external eye.
- **defense-gate** — before condemning, state the strongest defense the artifact could give; this drives false positives toward zero.
