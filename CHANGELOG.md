# Changelog

All notable changes to the Adversarial Audit Engine, newest first. The engine is a research
preview; every entry below is enforced in code and pinned by tests (CI on `main` and every PR,
Python 3.10–3.13). Version numbers are the plugin version (`aae.__version__`); repository/paper
releases are tagged separately (`v1.0.x`).

## 0.14.0 — Non-bypassable A+B run-validity refusal
The measured minimum of layers (`REQUIRED_LAYERS`) is consolidated over **10 runs across 8 artifact
classes**, correcting an earlier over-inclusion (`reasoner` returned to optional once two classes
recovered their defects without it). The A+B contract now **bites**: a run that is not `VALID` is forced
to `INVALID_RUN` — a state that **overrides every other, including a valid human `VALIDATED`** — and
`run_core.py` exits non-zero. Closure can no longer be bought by signing an incomplete process.

## 0.13.2 — Declaration beats the triage auto-N/A
An explicit `NOT_APPLICABLE` justification (e.g. external-auditor N/A *for independence*) is no longer
overwritten by the triage auto-adjudication ("not selected by triage"). Found by a 3-domain measurement
run.

## 0.13.1 — Measured scaffolding + triage optimization
The scaffolding layers are measured from their real outputs (governor from the meta verdict, oracle from
the distinct cited sources, triage from its decision record). Triage auto-adjudicates *unselected*
optional layers to `NOT_APPLICABLE` — never a required one.

## 0.13.0 — `REQUIRED_LAYERS` populated from measurement (A+B live)
The run-validity judgment goes live: a run is `VALID`/`INVALID`/`INCOMPLETE` from an execution manifest.
`REQUIRED_LAYERS` is read off a per-layer contribution measurement, not assumed; `deep_causal` and
`external_auditor` are optional.

## 0.12.1 — Instrumentation fixes found by a measurement run
Three real defects the measurement run found in the round-12/13 code: `parse_finding` now reads the
fields that form the false-positive denominator, the governor counts only coverage flags, and
source-grade coverage is recorded in the run log.

## 0.12.0 — Source-grade gate + self-instrumentation
A data-driven source-grade gate (§7.1) downgrades an `ARTIFACT_DEFECTIVE` resting on a non-primary source
when a primary is reachable. A self-instrumentation flag fires on a high-stakes run with zero recorded
discarded hypotheses (unknown false-positive denominator).

## 0.11.0 — Usage ledger (meta sub-layer)
`aae/usage_ledger.py` adds an append-only, one-JSON-line-per-run persistence layer feeding the
bias-resistant panel (`aae/run_metrics.py`), under two invariants: anti-Goodhart (no ledger field may
become a target of the gate) and reflexive/non-validating (it does not self-validate).

## 0.10.1 — Negation-spectrometry integrated into the governor
`MetaGovernor.falsification_type1(...)` exposes the Type-I gate directly on the meta-epistemic governor:
false-demolition rate (FDR), power, AUC, and the k-of-m persistence bound.

## 0.10.0 — Negation-spectrometry (Type-I gate against over-demolition)
`aae/negation_spectrometry.py` turns "the engine demolishes too much" into a measured, bounded number:
per-auditor false-demolition rate / power / AUC on a control battery; a negation is admitted only if it
persists across k-of-m independent (different-vendor) auditors; the assumption-free residual Type-I is
reported. Theorem verified numerically. Standard library only.

## 0.8.0 — Bias-resistant longitudinal metrics
`aae/run_metrics.py` (`run_core.py --metrics`): a panel of orthogonal rates with **no single composite
score** (anti-Goodhart), where abstention is never counted as success, and escape/precision/recall are
reported only with human ground truth. `bias_audit()` flags degenerate signatures (rubber-stamp,
all-abstain, over-condemn).

## 0.7.0 — Anti-hallucination grounding gate
`aae/grounding.py`: a finding may only condemn on a quote that exists *verbatim* in the source; a
fabricated or paraphrased quote is downgraded to "must be read by a human." Guaranteed (deterministic):
existence — no fabricated/altered quote can condemn; recall robustness — 0 false-negatives on 1,407 real
spans. Best-effort: out-of-context / quote-mining, caught by a conservative sentence-scope check (≈3 in 4
in testing), at ≈6% over-flagging (the safe direction). A companion `aae/legal_oracle.py` checks that
cited norms *exist* and are faithfully represented — never their interpretation.

## Earlier — rounds 9–11 (closure hardening)
Closure was moved from convention to code: vendor-aware completion states, an out-of-band **cryptographic
HMAC** human attestation the model cannot forge (`aae/attestation.py`), and a `Stop` hook that downgrades
an unattested `VALIDATED` on disk. See the self-audit trail under `papers/system-description/audits/`.
