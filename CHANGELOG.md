# Changelog

All notable changes to the Adversarial Audit Engine, newest first. The engine is a research
preview; every entry below is enforced in code and pinned by tests (CI on `main` and every PR,
Python 3.10–3.13). Version numbers are the plugin version (`aae.__version__`); repository/paper
releases are tagged separately (`v1.0.x`).

## 0.14.11 — `/audit` stops improvising: a `--schema` contract for the core
The first real Claude Code `/audit` run exposed the orchestration gap the standardization gradients
target: with no explicit contract, the role agent **reverse-engineered the core live** — it imported
`aae.schema` by hand, guessed a non-existent `TaxonomyCell` (ImportError), and listed enums ad-hoc,
burning a turn and risking an invalid payload. Fix: `scripts/run_core.py --schema` emits, in one
deterministic call, the exact payload template + the LIVE enum vocabulary (taxonomy_cell, defect_class,
posta, evidence_base, cost_to_fix, action_state) + the rules — introspected from the real enums, so it
can never drift from what the code accepts. `commands/audit.md` step 5 now mandates the path: call
`--schema`, write `findings.json` to match (with `source_text` for the grounding gate), then
`run_core.py findings.json` — and explicitly forbids hand-introspecting `aae`. Pinned by
`tests/test_run_core_schema.py` (vocabulary == live enums; the finding template invites no verdict).
Suite 199 green.

## 0.14.10 — Plugin loads in Claude Code (duplicate-hooks packaging fix)
The very first install of the plugin *as a Claude Code plugin* (prior real runs used the bundled skill,
never the marketplace path) surfaced a packaging bug: `plugin.json` declared `"hooks":
"./hooks/hooks.json"`, but Claude Code auto-loads `hooks/hooks.json` by convention — so the manifest
reference was a duplicate and the loader refused the plugin ("Duplicate hooks file detected … the
standard hooks/hooks.json is loaded automatically, so manifest.hooks should only reference additional
hook files"). Removed the `hooks` field from the manifest; the hook still loads automatically. First
clean `/plugin install` path. No code/test change.

## 0.14.9 — Honest caveat: a sandbox reaches no free eye (docs)
`INDEPENDENCE_free.md` sold Groq/Ollama as easy free level-3 eyes without warning that, from a hosted/
remote sandbox, *both* are unreachable for opposite reasons: hosted endpoints are outside the egress
allowlist (`api.groq.com` fails DNS) and `localhost:11434` is the sandbox's localhost, not your laptop's
Ollama. A real run proved it. Added the caveat as the first item (and a model-churn note): reachable
level-3 eyes are only a **local** run (engine on your own machine, where `localhost` is your Ollama) or a
**self-exposed** endpoint via `AAE_EYE_BASE_URL` — always probe reachability from the run's own
environment first. Docs-only; suite unchanged.

## 0.14.8 — Live Groq default model (the shipped default had been deprecated)
The `groq` preset's default model (`llama-3.1-70b-versatile`) was retired by Groq in 2026, so a
`AAE_EYE=groq` run with no `AAE_EYE_MODEL` override would fail the call and degrade to level 1 — the
"configured but never reached" trap. Updated the default to a current model (`openai/gpt-oss-120b`) and
documented that hosted providers churn model IDs: the identity's VENDOR earns level 3, not the model
name, so any live model of the provider works — override with `AAE_EYE_MODEL` if a call 404s. (A
standalone `probe_groq.py` in the workspace confirms key + model reachability from the run's own sandbox
BEFORE the audit, since egress allowlists differ by host.) No test change: `test_eye.py` never pinned the
model string. Suite 196 green.

## 0.14.7 — Independent eye wired into the engine, vendor-agnostic (gradient G3) + lean escape hatch
Datapoint 1 stayed level 1: the run's "red team" was a same-vendor CLAIMED identity, never attested, so
independence was correctly not credited. G3 wires the eye into `Orchestrator.run()` itself. An eye —
injected, or resolved from the environment (`AAE_EYE=ollama|groq|openrouter|<base_url>`) — is **called**
over the strongest condemnations, and the identity its adapter reports becomes the **attested** reviewer
passed to `evaluate_completion` (so the orchestrator path can finally reach level 3, not only `run_core`).
- **Vendor-agnostic, local first-class.** A local **Ollama** eye is a different vendor → **level 3**,
  the same credit as a hosted one — a confidential run keeps full independence without the artifact
  leaving the host. Pinned by `test_local_ollama_attested_is_credited_level3`.
- **Never rigid.** No eye configured → honest level 1, no crash. An eye that is unreachable (e.g. Ollama
  not started) → a recorded flag and level 1, not a failure. `external_auditor` shows RAN in the manifest
  only when the eye actually answered. Pinned by `test_external_eye_wiring.py`.
- **Lean escape hatch (fixes a G2 rigidity).** New `AuditConfig.auto_deep_layers` (default `True`): set
  `False` for a lean run where only explicit `enable_*` flags deploy the deep layers — so a slow LOCAL
  eye or a quick pass is not forced through triadic/construens/deep-causal at HIGH posta.
Suite 196 green.

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
