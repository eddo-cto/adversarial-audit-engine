# Changelog

All notable changes to the Adversarial Audit Engine, newest first. The engine is a research
preview; every entry below is enforced in code and pinned by tests (CI on `main` and every PR,
Python 3.10–3.13). Version numbers are the plugin version (`aae.__version__`); repository/paper
releases are tagged separately (`v1.0.x`).

## 1.10.0 — Stable artifact_id: the diachronic signature can finally pair passes
The diachronic cross-vendor signature (1.7.0) could only pair runs by the free-text `artifact_name` —
which changes between an L1 and an L3 pass of the same case, so real pairs never matched and the signature
stayed uncomputable (1 pair, no shift) on the actual corpus. This release gives an artefact a **stable
identity across passes**:

- `Ledger.artifact_id` is a first-class, record-only field, emitted in the ledger JSON. `pipeline.discipline`
  sets it from the payload's `artifact_id` if given, else **derives it automatically** from `source_text`
  (`auto:` + content hash) — same document, same id, nothing to remember.
- `bundle_sources.py` stamps a stable `artifact_id` in the bundle manifest (`bundle:<id1>+<id2>`, hashed if
  long): the same set of documents always yields the same id, so an L1 and an L3 run of the same case pair.
- `signature()` already prefers `artifact_id` over the name; `commands/audit.md` and the `--schema` output
  now instruct the flow to copy the manifest's `artifact_id` into the payload (same id for L1 and L3).

Demonstrated: two runs with **different names but the same `artifact_id`** now pair, and the signature reads
the shift (condemn 1.00→0.00, cross-vendor eye present). Old ledgers predating this field still pair only by
name; the signal accrues from new runs forward. Two new tests (bundle id stability; signature pairing on
`artifact_id` despite different names); full suite 301 green.

This closes the instrumentation gap for the Goodhart-mitigation *signature*. It remains a signature, not a
proof: the closed adversarial loop (an optimiser pushing on the measure) is still the separate, later step.

## 1.9.0 — Multi-document bundling: many sources into one audit artifact
The box audits a single file, but real audits are multi-document — a balance sheet + a registry extract,
a purchase proposal + the notarial deed + the cadastral plan. Until now that meant hand-assembling the
sources, which is error-prone and loses provenance. `scripts/bundle_sources.py` makes it a first-class,
repeatable step:

- `bundle_sources.py -o audit_input.md <file1> <file2> …` (or `--id name=path` to fix ids) writes ONE
  self-contained markdown artifact: a **manifest** that assigns each document a stable id and a content
  hash, followed by each document in its own delimited section. Text files are read directly; PDFs use
  `pdftotext -layout` when available, with a clear message otherwise. stdlib only; record-only (bundling
  never adjudicates).
- The manifest's ids ARE the `evidence_base` the findings payload should declare, so the round-22
  evidence-sufficiency gate can tell what was actually supplied; keeping each document verbatim inside its
  section means a quote in `accusation.evidence` is still a verbatim substring of `source_text` (the
  grounding gate keeps working) with unambiguous provenance.
- `commands/audit.md` step 0 now instructs the flow: with multiple sources, bundle first, audit the bundle,
  set `evidence_base` to the manifest ids, and mark any absent document via `requires_docs`.

Seven new tests (`test_bundle_sources.py`); full suite 299 green.

## 1.8.0 — Evidence-sufficiency gate: you may not assert on a document you do not have
A real L3 client-review (a commercialista, on a company fascicolo) drew the line precisely. The engine's
*nose* was right — it flagged, from the visura activity codes, an **IVA-regime** question a numbers-only
reading of the balance sheet would miss, and a **patrimonial anomaly** from a 2024 *conferimento*. But the
reviewer's verdict was exact: *those it can neither verify nor even suppose without the FY2023 comparative
it does not have.* The 2024 operation's before/after straddles FY2023→FY2024; the fascicolo carried only the
FY2025 statement with its FY2024 comparative — both **post-operation** — so the effect was structurally
unobservable. The flag could be **raised**, never **asserted**.

This release makes that a deterministic rule, not a matter of the model remembering to hedge:

- Findings gain **`requires_docs`** (documents the finding needs to be closable). The run gains
  **`evidence_base`** (documents actually supplied). Both record-only.
- **`enforce_evidence_sufficiency_gate`** forces any finding whose `requires_docs` are absent from
  `evidence_base` out of a condemning verdict (ARTIFACT_DEFECTIVE / REDUCED / still-PENDING) into
  **NEEDS_EXPERT**, appending a declared limit that **names the missing documents**. An artefact that HOLDS
  is untouched — needing an absent document bars a condemnation, not an absolution. Wired into the shared
  `pipeline.discipline`, so every entry point (CLI, orchestrator) inherits it; nothing is left to judgement.

Verified on the case that motivated it: with `evidence_base = [bilancio_2025, visura_2026]`, the four heavy
findings (conferimento, parti correlate, IVA regime, rivalutazione perimeter) are all routed to the expert
with their specific missing documents named (the FY2024/2023 comparative, the notarial deed, the VAT returns).
Six new tests (`test_evidence_sufficiency.py`); full suite 292 green.

## 1.7.0 — Registry consolidation + the diachronic cross-vendor signature (record-only)
The single run registry (round 21) recorded each completed run in one place with independence and eye
vendor as first-class fields — but only from the moment it shipped, and only for runs that flowed through
the live core. Dozens of real audits already sat as `*.ledger.json` in scattered per-run folders, invisible
to any portfolio view; and the property the whole trust story turns on — *what happens to the verdicts when
the same artefact is re-audited at a higher, cross-vendor independence level* — was not computable at all.

This release closes both gaps, staying strictly record-only (no adjudication, no gate, no single score):

- **`consolidate(roots)`** (CLI `run_core.py --consolidate <root…>`) sweeps serialized ledgers and back-fills
  the single registry, **idempotently** (dedup by `run_id`) and best-effort. `record_from_ledger_dict`
  reconstructs a registry line from a `*.ledger.json` alone, so history predating the live registry becomes
  queryable. New first-class fields on every record: **`axes_covered`** (the orthogonal taxonomy cells the
  run touched) and **`artifact_id`** (a stable pass-to-pass identity, when stamped).
- **`signature()`** (CLI `run_core.py --signature`) is a **descriptive** panel of the diachronic
  cross-vendor shift: for every artefact seen at ≥2 independence levels, how the condemn / abstain / hold
  rates move from the lowest to the highest level, and whether a different-vendor eye entered. It aggregates
  the mean shift and prints, in the output itself, the discipline that keeps it honest: **this is a signature,
  not a proof of Goodhart mitigation** — it shows an orthogonal cross-vendor axis *deflating* single-vendor
  over-condemnation, but proves nothing about resistance-to-gaming, because no optimiser is pushing on the
  measure (the closed loop is absent). No single score; abstention is never counted as success.

Run against the real corpus (14 consolidated runs) the signature immediately disciplined an eyeballed claim:
the L1→L3 pairs we *thought* we had do not auto-pair, because the free-text artefact name changes between
passes — only a stable `artifact_id` makes the diachronic view computable. The instrument reported the gap
in its own data rather than letting the claim stand. That is the point of the engine turned on itself.

Six new tests (`test_run_registry.py`): axes derivation, idempotent consolidation with cross-vendor recording,
and the signature's deflation reporting + its refusal to overclaim. Full suite 286 green.

## 1.6.0 — Verified-at-source gate (the dual of the source-grade gate, record-only)
A reputation or credential claim — a "Premier Partner" badge, a star rating, a review count, an award —
is only as good as the source it was read on. Two real misattributions an L3 audit caught made this
concrete: a "Google Premier Partner" that was **absent from the official Partners directory**, and a
"Clutch 5.0" that belonged to a **different company** with a similar name. Both had been copied from the
subject's own page / a search snippet and presented as *verified*. The engine had no deterministic guard
against an unearned positive badge — only against an unearned condemnation (the round-12 source-grade gate).

This release adds the **dual**. Findings gain two record-only fields: `credential_claim` (this finding
carries a reputation/credential claim) and `verified_at_source` (the operator's assertion that it was read
on the **primary authoritative source** — the official directory or the review portal itself). The new
`enforce_verified_at_source_gate` downgrades any claim asserted `verified_at_source=true` whose load-bearing
`source_grade` is worse than primary (an aggregator, a snippet, the subject's own page) to self-declared,
and records a `VERIFIED-AT-SOURCE:` flag telling the reader to re-read it on the primary source. It **never
touches the verdict** — an unearned badge is a badge defect, not a conviction. `Ledger.verified_at_source_coverage`
tallies credential claims by badge state (verified / declared / unearned) so "how many claims actually earned
the verified badge" is a measured fact. Wired into the ONE `pipeline.discipline` core, so both the `/audit`
product path and the orchestrator enforce it; the `--schema` contract documents the fields and the rule.
`test_verified_at_source.py` pins the gate, the coverage, and the discipline wiring. The client-facing
`due-diligence-fornitore` skill carries the same node as a mandatory "reputation read at the source" step.

## 1.5.0 — Spec pickup via `_spec.md` (launcher → command contract)
The dashboard offers a free-text "spec" box (nature of the document, domain, what to check, focus) and
appended it to the launch command as `/audit "file" -- <spec>`. But `/audit` (`commands/audit.md`) never
parsed anything after the filename — no `$ARGUMENTS`, no `--` handling — so the operator's spec was
**silently dropped** and had to be re-pasted by hand into the session. A launcher and a command that
disagree about where the input lives is exactly the two-sections/incompatible-values class the engine
claims high recall on; it should not live in our own product.

This release closes the gap with a **file-based contract** instead of fragile command-line parsing:
- **`dashboard.ps1`** (all three copies: `_common`, `claude-plus-local`, `full-local`) now writes the
  operator's spec verbatim to `<run-folder>/_spec.md` before opening Claude Code. The original multi-line
  text is preserved (not collapsed to one line). The clipboard `-- <spec>` is kept only as a
  human-visible hint.
- **`commands/audit.md`** gains **step 0 — pick up the run spec**: before triage, read `_spec.md` from the
  run folder if present and fold it into triage as *operator-supplied context* (nature/domain/focus, role
  selection). It is **data, not an override** — the gates, verdicts, independence and red-line still bind,
  and it can never instruct the run to skip a layer or pre-decide a verdict. Absent `_spec.md`, the run
  proceeds with no prior and auto-detects the artifact's nature.

No change to the deterministic core, schema, or verdict machine. Record/UX contract only; version-coherence
across the four release surfaces (`aae.__version__`, `plugin.json`, `marketplace.json`, README) preserved.

## 1.4.0 — Single longitudinal run registry (record-only)
Each run already accrued a self-describing record (`_runs.jsonl`, round 13), but it was written **inside
that run's own `out_dir`** and never aggregated: answering "how many runs, with what verdicts, at what
independence, over time" meant a `find(1)` sweep across scattered folders — and the property that matters
most, the **independence actually achieved and the vendor of the independent eye**, was not recorded at all
(it had to be reconstructed by hand from the ledger plus who ran the eye). This release closes both gaps.
The **eye is now a recorded ledger property**: `Ledger.internal_identity` and
`Ledger.external_attested_identity` persist the identities the completion was computed from — the attested
one, adapter-supplied, never the model-authored payload (the C1 invariant). And a new module
(`aae/run_registry.py`) writes **one append-only line per completed run to ONE known location**
(`AAE_REGISTRY`, else `AAE_HOME/RUN_REGISTRY.jsonl`, else `~/.aae/RUN_REGISTRY.jsonl`), capturing `run_id`,
timestamp, box, artifact, `run_validity`, verdicts, **`independence_level`**, **`eye_vendor`**, the
**governor completion** verdict, calibration state, content digest and the ledger path. `run_core.py
--registry [path]` renders a descriptive portfolio panel (independence distribution, cross-vendor count,
Type-I calibration) — no single score, abstention never dressed up as success. The registry is strictly
**record-only and non-authoritative**: it indexes what the deterministic core already decided, never
adjudicates and never gates, and every write is **best-effort** — a read-only mount or disk error returns
`None` and can never break an audit. Pinned by `tests/test_run_registry.py` (10 tests). Suite 273 green.
Backward-compatible: two new optional ledger fields (default `""`); existing runs and consumers are
unaffected.

## 1.3.0 — The deterministic core is non-bypassable (robustness under surprises)
A real `claude-plus-local` run derailed: an unexpected `TypeError` on the independent-eye call threw, and
the hive ended the session with a **prose summary** instead of invoking `run_core.py`. **No ledger was
produced, yet nothing failed** — the Stop hook found no ledger and printed "nothing to check". The trust
protocol had been silently bypassed: with no core run, verdicts would come from the model, not the code —
exactly what the engine exists to prevent. This release engineers that shut, in code, not prompt: fetching
the schema (`run_core.py --schema`, the mandatory first step of every audit) drops an `.audit_pending`
marker that **only a completed core run clears**; the Stop hook (`governor_check.py`) now, on finding the
marker but **no ledger**, prints `AUDIT DERAILED` and **exits 2 (blocking)** — the session cannot present as
a completed audit. Any surprise that derails the run (an exception, a tool error, an eye failure, or the
model deciding to write prose) leaves the marker and is caught; a genuine non-audit session (no marker)
passes quietly, and a completed run clears the marker (an `INVALID_RUN` counts — the core still adjudicated
it). Supporting hardening in `commands/audit.md`: the eye is called with an explicit signature
(`eye.complete(system=…, user=…)`), an eye that errors **never aborts** the audit (it lowers the
independence level and the core still runs), and step 6 states the core is non-bypassable. The guarantee no
longer depends on the model remembering to run the core. Pinned by `tests/test_stop_hook_enforcement.py`
(6 tests). Suite 263 green. Backward-compatible: valid runs are unaffected; only derailed sessions newly fail.

## 1.2.0 — Belnap (4-valued) coverage recovery on the ledger (record-only)
A boolean covered/not-covered view of the six taxonomy cells collapses two states the engine already
produces but then discards: **F** — a cell explicitly *excluded-with-justification* (`excluded_cells`) — and
**B** — a cell carrying a *conflict* (a finding typed `conflicted` on the 1.1.0 temporal axis, two vectors
kept instead of collapsed). Both were squashed into the same "0" as **N** (a genuinely silent, unexamined
cell). This release adds `Ledger.belnap_coverage` (record-only): a 4-valued state per cell —
`T` covered, `F` excluded, `N` silent, `B` conflict — with precedence `B > T > F > N`. Computed in the
pipeline next to `source_grade_coverage` from fields already on the ledger; it never feeds a verdict. On the
real audit corpus this recovers a measurable signal: **12.8%** of cells are `F`, previously invisible next
to the 3.8% that are truly silent. This is the one piece of the derived-taxonomy exploration (VAL-PROP-01/02)
that survived: that feature was **killed at F0** — its "seams" between cells proved *below* a permutation
null on real ledgers (z=−2.83), so it never entered the engine — but the Belnap distinction it rested on is a
real, standalone improvement that does not depend on the (rejected) ternary graph. Backward-compatible,
additive; the `--schema` contract and `content_digest` are unchanged. Pinned by `tests/test_belnap_coverage.py`
(5 tests). Suite 257 green.

## 1.1.0 — Temporal/epistemic axis on findings (longitudinal, record-only)
Longitudinal use (auditing a living artifact across turns as new primary documents arrive) exposed
statuses the ledger could not name: a finding can be **provisional** (suspected, not yet realized),
**transient** (true this turn, resolved later), or **conflicted** (two vectors in genuine disagreement —
the Belnap "both" state the ledger previously collapsed on overwrite). These are a **third axis**,
orthogonal to the taxonomy (WHERE a defect is) and to the verdict (this turn's adjudicated truth). This
release adds that axis to `Finding`, **record-only**: `adjudicate()` never reads it and the verdict state
machine is untouched. New optional fields: `temporal_status` (`stable|provisional|transient|conflicted`),
`likelihood` + `likelihood_basis` (a **declared, non-calibrated** estimate on a provisional finding —
basis required, so a bare number can never masquerade as a measured rate), `conflict_with` (claim keys of
the opposing vectors), `perishable_pivot` + `pivot_valid_until` (a load-bearing datum that must be
re-verified each turn), and — the primitive the rest depends on — `claim_key`, a deterministic cross-run
identity of the *claim* (stable under changes of per-run id, verdict, and connective prose) plus
`superseded_by`, so a longitudinal tracker can draw a claim's status line across turns. `claim_key` is
auto-filled on serialize, so **every** ledger now carries it. All fields default unset (like
`source_grade=9`): a one-shot run asserts no temporal judgment. Backward-compatible and additive — the
`--schema` agent contract is unchanged, `content_digest` (element+verdict) is unchanged, so existing
consumers and human attestations are unaffected. Also: `commands/audit.md` now requires `accusation.evidence`
to be ONE verbatim quote (no editorial gloss), reducing upstream the mixed-evidence downgrades the 1.0.1
grounding gate handles. Pinned by `tests/test_temporal_axis.py` (13 tests). Suite 252 green.

## 1.0.1 — Footnote-tolerant, fragment-aware grounding (real-document hardening)
A real-use run on the footnoted EDPB Opinion 28/2024 (AI models & GDPR) exposed a recall gap: legitimate
verbatim quotes were flagged "absent" only because the source carried inline **footnote markers**
("legitimate interest **53**, an interest") or because the auditor joined two real passages with "...".
The grounding gate now, when a whole-string match fails, extracts the explicitly-quoted spans (between
`"` `"` or `«` `»`), splits each on an internal ellipsis, drops standalone 1–3-digit footnote/paragraph
markers **symmetrically** from quote and source, and requires **every** resulting fragment to be present
verbatim. This recovers genuinely-grounded findings on footnoted legal/regulatory documents (the target
domain) while preserving the guarantee: one absent fragment still fails the whole (no fabrication
condemns), and editorial glue outside quotation marks is ignored. Verified by re-adjudicating the real
EDPB findings (grounding flags 7→4, no verdict regressions) and pinned by `tests/test_grounding_fragments.py`.
Suite 239 green. No API/contract change (patch).

## 1.0.0 — First stable release: API frozen, trust protocol standardized
The engine reaches 1.0. This is not "audits are now validated" (only a human validates) — it is that the
**tool is mature and standardized**: one audited discipline (`aae.pipeline.discipline`), one contract
(`--schema`), a calibrated Type-I number the run cites, and a public surface that will not break within the
1.x line. What 1.0 declares:

- **Public API frozen for 1.x** — new `API.md` fixes the `--schema` payload/finding keys, the enum
  vocabularies (additive-only), the `run_core.py` CLI, `discipline()`'s signature, the 11 `AAE_*`
  variables, and a SemVer policy (what won't break, what may be added, what triggers 2.0). Pinned by
  `tests/test_api_surface.py` so drift fails CI.
- **Trust protocol standardized** — cryptographic human closure (HMAC), attested cross-vendor independence,
  the A+B run-validity manifest, grounding gate, defense-gate, source-grade gate, deterministic
  meta-governor; all on one code path since the 0.14.14 unification.
- **Type-I calibrated** — auditor `anthropic:claude-sonnet-5` at 0% [95% CI 0–14%, n=24] on the near-miss
  `general-v2` battery; swappable **block structure** for domain cards.
- **A1 deep-causal** on a deterministic structural trigger.
- Validated on 3 real public-document datapoints (DP3 EDPS at attested level 3).

Honest boundaries carried into 1.0: it multiplies a competent reviewer, it is not an oracle; internal
completion never exceeds `EXTERNAL_REVIEW_PENDING`; calibration certainty scales with battery size; no
external/paid pilot yet. Suite 233 green.

## 0.14.20 — general-v2 calibrated: Type-I 0% [95% CI 0-14%, n=24]
A fresh, blind Sonnet 5 auditor scored the general-v2 base card (24 valid near-miss + 12 invalid): all
24 valid items survived (0 false demolitions) and all 12 invalid were demolished → **Type-I = 0%, 95% CI
[0%, 14%], power TDR = 100%, AUC = 1.0** (`_calibration.jsonl`, auditor `anthropic:claude-sonnet-5`,
battery `general-v2`, 2026-08-15). This tightens the standing bound from [0%, 39%] (n=6) to [0%, 14%]
(n=24) and — the point of the near-miss design — the 0% now holds against valid items engineered to look
wrong (many summands, pp-vs-relative, valid-but-unusual logic, correct-but-tricky citations). Appended
latest-wins, so runs for this auditor now cite the general-v2 number instead of general-v1. Honest note:
this is still the auditor's condemn/hold decision on a generic battery; domain cards remain the path to
domain transfer. No engine-code change.

## 0.14.19 — Block structure for control batteries (swappable base + domain cards)
The Type-I battery becomes modular. `benchmarks/type1_calibration/batteries/` now holds one CARD per
`battery_id`, with a manifest (`index.json`) that names the single ACTIVE base card; domain cards are added
as separate files over time and can replace the active base per client/domain. Calibration records are
already keyed by `(auditor_identity, battery_id)` (latest-wins by date), so every card carries its own
honest number. The base card is upgraded to **`general-v2`: 24 valid + 12 invalid, VALID-HEAVY and
NEAR-MISS by design** — the valid items look superficially wrong (many summands, percentage-point-vs-
relative distinctions, valid-but-unusual logic, correct-but-tricky citations) yet survive the strongest
defence. That matters because the Type-I rate is bounded by the VALID controls: a trivially-correct valid
item never tempts a false demolition, so it measures nothing; a near-miss does. Every numeric/date label
is verified in code at build time. New reusable tool `make_blind.py` turns any card into a blind audit file
(neutral, shuffled ids) plus a private answer key kept out of the repo (`.gitignore`), enforcing the
anti-contamination invariant when adding a card. `general-v1` (6+6) is retained as history, marked
superseded. No engine-code change; the discipline is unchanged. The v2 calibration NUMBER is produced by a
fresh blind auditor next; until then runs still cite the standing record.

## 0.14.18 — First real Type-I calibration shipped (blind, Sonnet 5)
The G4 mechanism (0.14.16) was measured but uncalibrated — runs said "NOT CALIBRATED". This ships the
first real number. The 12-item control battery (`general-v1`, 6 valid + 6 invalid) was audited BLIND by a
fresh Sonnet 5 auditor: items were re-identified with neutral, shuffled ids and the label key was withheld
from the auditor (the project's anti-contamination invariant — whoever knows the labels cannot audit). The
auditor scored 6/6 true demolitions and 0/6 false demolitions → **Type-I (false-demolition) = 0%, 95% CI
[0%, 39%], power TDR = 100%, AUC = 1.0** (`benchmarks/type1_calibration/_calibration.jsonl`, auditor
`anthropic:claude-sonnet-5`, battery `general-v1`, 2026-08-14). Point `AAE_CALIBRATION` at that file and
runs cite the real number instead of "NOT CALIBRATED". The CI is deliberately wide (n=6 valid controls);
tightening it is the job of a larger battery, shipped as a periodic recalibration. Honest note: this
calibrates the auditor's condemn/hold decision on the battery, not a full per-item engine run. No code
change — the discipline and gates are unchanged from 0.14.17.

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
