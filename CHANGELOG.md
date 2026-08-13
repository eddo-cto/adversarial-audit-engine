# Changelog

All notable changes to the Adversarial Audit Engine, newest first. The engine is a research
preview; every entry below is enforced in code and pinned by tests (CI on `main` and every PR,
Python 3.10–3.13). Version numbers are the plugin version (`aae.__version__`); repository/paper
releases are tagged separately (`v1.0.x`).

## 0.14.6 — Deep layers auto-deploy by stakes (standardization gradient G2)
Datapoint 1 (an OEPV tender annex at HIGH posta) ran with the attack roles only — triadic, construens
and deep-causal stayed off because the run script never set `enable_*`. That is the A1 gap: depth
depended on the operator remembering a flag. G2 makes the deep passes **auto-deploy when the run
warrants depth** — HIGH posta (the operator's declared stakes) or a conceptual-novel finding (exactly
what root-clustering is for) — via a deterministic policy `_deep_layers_warranted(config, ledger)`. The
explicit `enable_triadic` / `enable_construens` / new `enable_deep_causal` flags still force them on;
below the threshold (a low/medium run with no conceptual-novel signal) they stay off — the Freno against
over-engineering a small artifact. `deep_causal` is now wired into `Orchestrator.run()` (new
`AuditResult.deep_causal`, added to the summary) and, when it auto-runs, recorded **RAN** in the
manifest — honest measurement, not a silent extra. `construens` still needs its `construens_idea` and
abstains without one. Pinned by `tests/test_deep_layers_autodeploy.py`. Suite 192 green.

## 0.14.5 — Source-grade gate runs in the engine (standardization gradient G1)
Two real runs (LU-VE, and an OEPV tender annex) hand-wired the source-grade gate *after* the
orchestrator — and, worse, after completion and the manifest were already computed, so the "read the
primary first" downgrade did not always reach the verdict a client sees. G1 folds the gate into
`Orchestrator.run()`: it now runs **before** the defense/coverage gates, completion, and the manifest,
and the per-grade coverage is **always** reported (`ledger.source_grade_coverage`), on every entry
point — no external call. New `AuditConfig.primary_reachable` (default `True`) carries the operator's
one honest declaration: `False` means no primary exists for this artifact class, and the gate abstains
rather than punish. Pinned by `tests/test_source_grade_in_orchestrator.py` (coverage always reported;
worse-than-primary condemnation downgraded to `NEEDS_READING`; gate abstains when no primary). First of
the progressive standardization gradients: turning what a run had to assemble by hand into engine
behavior. Suite 188 green.

## 0.14.4 — One-command run + free level-3 eye wired from the environment (delivery gap #1)
The independent eye was documented but *narrated*, not wired — every real run stayed level 1. Added
`aae.external_eye_from_env()`: `AAE_EYE=groq|ollama|openrouter` (or an explicit `AAE_EYE_BASE_URL`) builds
a genuinely different-vendor adapter → independence **level 3**, at zero cost, via the existing
`OpenAICompatibleClient`. Not configured → `None`, and the run stays honestly level 1. The `/audit`
command gains a one-command quick-start and wires the eye in step 6 (credited only once the adapter is
actually called, never merely configured). Confidentiality is called out: `groq`/`openrouter` send the
artifact off-host (fine for demos, not for privileged material — use `ollama`). Pinned by
`tests/test_eye.py`. This is the first productization step: a professional reaches a level-3 report
without wrestling a bundle.

## 0.14.3 — Shared A+B refusal + `REDUCED` reintroduced as a derived verdict
Two changes prompted by a third-party run on a real artifact.
- **The non-bypassable A+B refusal is now shared, not tied to the CLI.** A real run via the *orchestrator*
  (not `run_core.py`) reported `run_manifest INCOMPLETE` yet a non-INVALID completion — the round-18
  refusal lived only in `run_core.py`, so the orchestrator entry point bypassed it. Extracted into
  `run_manifest.enforce_run_validity(...)` and applied on **both** entry points; the orchestrator now
  builds the manifest and forces `INVALID_RUN` on an under-run. Pinned by `tests/test_refusal_shared.py`.
- **`REDUCED` ("accusa_ridimensionata") is back — as a *derived* verdict, not dead code.** A real defect
  (would be `ARTIFACT_DEFECTIVE`) whose `cost_to_fix` is `TRIVIAL` is now "real but minor". It is computed
  one-way from `cost_to_fix`, so it cannot drift from it; it gives a client a verdict-level priority
  signal without cross-referencing the cost field. Trigger and reachability pinned by
  `tests/test_reduced_verdict.py`. (This supersedes the 0.14.1 removal, which was correct at the time: the
  old `REDUCED` had *no* trigger and never fired.)

## 0.14.2 — `run_core.py` runs standalone (sys.path off-by-one)
The CLI inserted `scripts/../..` (the `plugins/` dir) instead of `scripts/..` (the plugin dir where `aae`
lives), so `python3 scripts/run_core.py --version` raised `ModuleNotFoundError` unless `PYTHONPATH` was
set — which CI always did, hiding it. Found while packaging a self-verifying bundle. Fixed to
`scripts/..`; the CLI (and the `--version` check) now work from any working directory with no environment
setup.

## 0.14.1 — Remove the unreachable `REDUCED` verdict (dead-code fix)
A third-party audit (run on a stale 0.6.0 bundle) found, and re-derivation on 0.14.0 confirmed, that
`Verdict.REDUCED` ("accusa_ridimensionata", "real but minor") was **never producible** by the
adjudication state machine — `PATTERN` is caught by Rule 1 and the three remaining evidence bases by
Rule 5, leaving its fall-through with no entry. Removed from the enum and from the verdict-keyed tables in
`dedup`, `grounding`, `run_metrics`, and `usage_ledger`; the fall-through now defensively routes to the
human expert. Severity of a real-but-minor defect already lives in `cost_to_fix`, not in a distinct
verdict. Zero behaviour change (the verdict never fired); pinned by `tests/test_no_dead_verdict.py`.

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
