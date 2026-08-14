# Changelog

All notable changes to the Adversarial Audit Engine, newest first. The engine is a research
preview; every entry below is enforced in code and pinned by tests (CI on `main` and every PR,
Python 3.10–3.13). Version numbers are the plugin version (`aae.__version__`); repository/paper
releases are tagged separately (`v1.0.x`).

## 0.14.17 — Deep-causal on a deterministic structural trigger, enforced (A1)
Datapoint 3 (EDPS, HIGH posta, 3 sparse findings) left deep-causal off, and the scorecard called it a
gap. The data says otherwise: the 10-run measurement classified deep_causal as CONTEXTUAL (7/10). So the
honest policy is neither a blanket "always on HIGH posta" (contradicts the measurement) nor the agent's
whim (not measurable), but a deterministic STRUCTURAL trigger — new `aae/layer_policy.deep_causal_warranted`:
HIGH posta AND (>= 5 findings OR >= 2 findings sharing a taxonomy cell OR a conceptual-novel finding).
On a small/sparse run it stays off — so EDPS's 3 unrelated findings correctly do NOT warrant it (the
earlier "gap" was the scorecard, not the engine). Wired on both entry points: the orchestrator uses it to
auto-deploy, and `pipeline.discipline` ENFORCES it on the product path — a warranted-but-absent deep-causal
is flagged ("DEEP-CAUSAL WARRANTED BUT NOT RUN"), so it cannot be silently skipped. `commands/audit.md`
states the exact trigger. The threshold (5) is a named, tunable hypothesis; the mechanism is the principled
part. Pinned by `tests/test_deep_causal_policy.py`. Suite 227 green.

## 0.14.16 — Type-I calibration: the false-demolition rate becomes a cited, bounded number (G4)
Both real datapoints failed the control-battery / Type-I cell: the engine flagged the false-positive rate
as "unmeasured". G4 turns it into a measured, honest number. The math already existed
(`negation_spectrometry.calibrate` → FDR/TDR/AUC); added around it:
- **A control battery** (`benchmarks/type1_calibration/battery.json`, `general-v1`): 6 VALID items (must
  survive) + 6 INVALID (must die), balanced across defect classes — an unambiguous, versioned, fallible
  yardstick.
- **`aae/type1_calibration.py`**: FDR (Type-I) and TDR with **95% Wilson confidence intervals** (a rate
  is never a bare point — with a small battery it is intrinsically uncertain and that is shown), plus the
  calibration record store and `cite()`.
- **The run cites it (option B — calibrate once, cite):** `pipeline.discipline` reads the latest
  calibration for the auditor identity from `AAE_CALIBRATION` and reports
  `TYPE-I: ... = X% [95% CI …, n=… valid controls] …`, or honestly "NOT CALIBRATED" — never "low".
  Calibration is a **periodic safety re-calibration**, shippable to clients as an update patch (dated
  records, latest-wins; a bigger battery tightens the interval).
- **`calibrate.py`** turns an auditor's battery outcomes into a record.
Because this is an error theory, it is validated by **independent rounds** in
`tests/test_type1_calibration.py`: analytic cases (perfect/paranoid/blind/mixed), the AUC re-derived by a
second average-rank Mann-Whitney method, and a Monte-Carlo **coverage** test (the 95% interval covers the
true rate ~95% of the time) plus a convergence check. Suite 219 green.

## 0.14.15 — Generous, configurable eye timeout (a local Ollama eye was cut off at 60s)
The first successful level-3 product run (EDPS AI-risk guidance, local Ollama eye) surfaced it: the
adapter's HTTP timeout was **60s**, too short for a slow LOCAL model on a big audit payload, so the eye
timed out mid-review and had to be hand-patched to finish. Audits are not latency-sensitive: the default
is now **300s**, and `OpenAICompatibleClient` reads `AAE_EYE_TIMEOUT` (or a constructor arg) to override
— so the independent eye completes without a manual patch. Pinned by `tests/test_adapter_timeout.py`.
Suite 207 green.

## 0.14.14 — One contract, one discipline: the two entry points unified
The two entry points ran the SAME ~8 discipline steps in two files, and had already **drifted on 4 rules**
(grounding, integrity-as-flags, self-instrumentation, human-HMAC were enforced on only one path) — so the
core claim "the discipline lives in one audited place" was, in fact, false. Extracted the whole
discipline into **`aae/pipeline.py::discipline(payload, *, attested_identity=None)`** — the single audited
core, driven by the `--schema` findings contract. Now:
- **`scripts/run_core.py`** is a thin product-path wrapper: `discipline()` + write ledger/summary/run-log.
- **`Orchestrator.run()`** is purely the findings PRODUCER (drives the LLM: oracle, triage, roles, deep
  layers, the eye), then serializes to the same payload and **delegates all discipline** to
  `pipeline.discipline`. It no longer enforces anything itself.
Effect: one place to audit, one place to fix, no drift; and the previously orchestrator-only path now
gets grounding, self-instrumentation and human-HMAC for free (the 4 divergences are closed). The eye is
called before the core and its identity passed through; the deterministic governor is the enforceable
core (the LLM-narrative governor, if any, rides on top as presentation). Suite 203 green; both entry
points verified. This makes the trust-protocol claim literally true.

## 0.14.13 — The product path exercises the full method (bug 1: `/audit` → `run_core.py`)
Datapoint 2 exposed that `/audit` drives `run_core.py`, which does **not** invoke `Orchestrator.run()` —
so the G1–G3 gradients built into the orchestrator did not reach the product path. Diagnosed precisely:
G1 (source-grade gate) and G3 (env-attested eye) were **already** implemented independently in
`run_core.py`; the real gaps were the deep layers and the eye/record handshake. Fixed:
- **Code:** when `AAE_EXTERNAL_ATTESTED_IDENTITY` is set (the eye actually ran), `run_core.py` now records
  `external_auditor` = RAN in the manifest **deterministically**, overriding an under-declaring payload —
  a real run left it NOT_APPLICABLE despite a genuine cross-vendor corroboration, understating the
  independence. Pinned by `tests/test_external_auditor_recorded.py`.
- **`commands/audit.md` flow rewrite:** deep-causal is **run on any HIGH-posta / richly-structured**
  artifact (Freno only for trivial ones), not "optional"; the eye is called **before** the core and its
  identity exported in the **same shell**; the core is **one invocation at the end** (no run→patch→re-run
  churn); and `source_text` must be **byte-for-byte extracted, not hand-transcribed** (a fuzzy copy makes
  the grounding gate downgrade good findings — exactly what cost datapoint 2 three findings).
Suite 203 green. Deferred by design: full unification of the two entry points (orchestrator vs run_core).

## 0.14.12 — Two fixes a real Claude Code run exposed (attested independence; Windows hook encoding)
The first end-to-end `/audit` on a user's machine (an EIA study, local Ollama eye) surfaced two bugs:
- **An attested cross-vendor eye was lost from the record when the run was BLOCKED.** The eye
  (`ollama-local:llama3.1:8b`) genuinely ran and corroborated a defect, yet the ledger read
  `independence_level: 1` — `evaluate_completion` returned `BLOCKED_OPEN_ITEMS` before crediting the
  attested reviewer. Completion STATE and independence LEVEL are separate facts; the level now reflects
  who reviewed regardless of open items. Fixed in `gates.py` (credit the attested level up front),
  pinned by `tests/test_independence_when_blocked.py`.
- **The Stop hook crashed on the Windows console codepage.** `governor_check.py` printed box/warn
  glyphs (and could print accented artifact names) under cp1252 → `UnicodeEncodeError`. Both
  `governor_check.py` and `run_core.py` now force UTF-8 stdout/stderr (no-op where unsupported) and the
  hook's decorative glyphs are ASCII — so the discipline no longer depends on the operator exporting
  `PYTHONIOENCODING` by hand. Suite 201 green.

Known, deferred (next phase, by design — not a rushed patch): the product path `/audit` → `run_core.py`
does **not** invoke `Orchestrator.run()`, so the G1–G3 gradients (which live in the orchestrator) do not
apply to it. Standardization work moves onto the `run_core.py` / `audit.md` path, or the two paths get
unified.

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
