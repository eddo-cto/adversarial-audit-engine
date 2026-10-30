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

## Run contract, sources and closure

| module | plain language |
|---|---|
| `pipeline` | the one disciplined core: every entry point funnels through `discipline()`, which applies all gates to a findings payload. |
| `run_manifest` | the execution manifest: which layers ran; a run missing a required layer is `INVALID_RUN`. |
| `layer_policy` | decides deterministically when the deep-causal layer is warranted. |
| `run_registry` | the single longitudinal registry of runs (record-only). |
| `attestation` | makes closure real: `VALIDATED` needs an HMAC under an operator key the model cannot reach; independence is credited only from the adapter-attested identity. |
| `source_grade` | the source-grade gate: a condemnation on a worse-than-primary source, when a primary is reachable, must be read first. |
| `type1_calibration` | measures an auditor's false-demolition rate on a control battery and cites it with its confidence interval. |
| `attack_vectors` | the library of attack moves per defect class (the dual of the defense-gate). |

## Anti-Goodhart guards (1.16–1.20, record-only unless stated)

The verdict is a function of fields the auditor declares, so an auditor can optimise the verdict instead of the truth.
These modules expose that, without changing verdicts.

| module | plain language |
|---|---|
| `routing_sentinel` | lists condemnations avoided only by the auditor's own routing (missing documents, secondary source); also the high-stakes findings that hold only on the auditor's own defense (*defense lever*). |
| `referto_guard` | the ledger is the truth, the prose may not overstate it: a report may not present an open or defense-only finding as solid, nor an unsustained common cause as a conclusion. |
| `root_support` | a declared common cause is checked by a blind external judge with intruders and control groups: *sustained* or *hypothesis*. |
| `gauge` | a severity declaration (stakes, fix cost) may order a finding but never decide whether it is real: the core re-runs each finding with other severities and flags any change of truth class. |

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
