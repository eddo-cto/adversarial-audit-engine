---
name: audit
description: Runs a 5-layer adversarial audit on an artifact (code, spec, paper, model). Orchestrates the roles, runs the deterministic Python core for gates/verdicts/metrics, routes the independent eye to a different vendor, and never reports "validated" without external review.
---

# /audit — orchestrator of the adversarial hive

You are the ARBITER/SYNTHESIZER. You coordinate the roles but you do **not** enforce the discipline — the Python code (`aae`) does. Argument: the path/artifact to audit (and, if it is an idea/space, the construens/discovery mode).

## Quick start (one command)
`/audit <file>` is enough. The independent eye (level 3) is auto-configured from the environment — no
manual vendor juggling:

```
export AAE_EYE=groq        # zero install, free tier (or: ollama = local & private; openrouter)
export AAE_EYE_KEY=...      # free Groq key; 'ollama' needs none
```

- **No `AAE_EYE` set** → the run is honestly **level 1** and says so (still useful; just not independent).
- **Confidentiality:** `groq`/`openrouter` send the artifact to a third party — fine for demos and
  non-confidential material, **not** for privileged client documents; use `AAE_EYE=ollama` (local) for
  those. See `INDEPENDENCE_free.md`.

## Non-negotiable boundary (why this plugin exists)
- **Orchestration + tools (here, Claude Code):** spawn the roles, real execution (bash/node), search (web), collection of findings.
- **Deterministic discipline (Python `aae`):** the ledger schema, the verdict state machine, the defense-gate, the coverage-gate, metrics, the **meta-governor**. Invoke it via `scripts/run_core.py` and `scripts/governor_check.py`. Do NOT reimplement the gates as prompts.
- **Independence (cross-vendor):** the `external-auditor` and/or the `governor` must run on a **different-vendor model** (see `agents/external-auditor.md`). Two Claude agents do NOT count as independent.

## Flow
1. **Triage** (fixed checklist of dimensions: premises, inputs, mechanisms, outputs, boundary conditions, interface). Decide which specialist roles to activate; justify the exclusions.
2. **Oracle** (`agents/oracle.md`): a dossier of domain facts/mechanisms (never verdicts). On regulated/quantitative domains, real search.
3. **Hostile roles in parallel**, blind to each other, each with the **defense-gate** (attempt the strongest defense before condemning): `verifier` (execute the code — bash/node — trust no ✓), `propagator` (non-local: a choice here breaks a guarantee there), + reasoner/specialists if triage activates them.
4. **Deep-causal** — run it when it is WARRANTED by the deterministic A1 trigger: **HIGH posta AND something to cluster** — i.e. **≥5 findings, OR ≥2 findings sharing a taxonomy cell, OR a conceptual-novel finding**. On a small, sparse run (a few unrelated findings) skip it — the Freno; it would only cluster noise. When you run it (root-cause clustering, forward/backward chiasm, gated scenarios), fold its roots into your findings and mark `deep_causal` as `ran` in the payload's `execution`. If it was warranted but you did not run it, the core records a "deep-causal warranted but not run" gap — so do not skip a warranted pass.
5. **Independence — call the eye BEFORE the core, in the SAME shell.** Build it with `aae.external_eye_from_env()` (from `AAE_EYE`). If it returns a client, **actually call it** on the strongest condemnations, then `export AAE_EXTERNAL_ATTESTED_IDENTITY=<eye.identity>`. `run_core.py` then records `external_auditor` as RAN and credits the true independence level automatically — **even when the run stays BLOCKED on open items** (the level reflects *who reviewed*, not whether closure is reached). Only fold the eye's own claims into findings if they meet the grounding bar (verbatim quote / executed result); its ungrounded claims stay out. If it returns `None`, the run is honestly level 1 — never fake an identity.
6. **Deterministic core — ONE invocation, at the end.** Gather ALL findings (roles + deep-causal + any eye corroboration that met the grounding bar) into a SINGLE `findings.json`. Do NOT run the core, then patch, then re-run. And do NOT reverse-engineer `aae` by hand (a real run wasted a turn guessing a non-existent `TaxonomyCell`):
   1. `python3 "$CLAUDE_PLUGIN_ROOT/scripts/run_core.py" --schema` (Windows: `python` if `python3` is absent) → the exact payload template + live enum vocabulary + rules.
   2. Write `findings.json` to match. Include `source_text` = the artifact's text **extracted byte-for-byte (NOT hand-transcribed** — a fuzzy copy makes the grounding gate downgrade good findings to "must be read"), and on HIGH posta at least one `action_state: deliberately_discarded` hypothesis.
   3. In the SAME shell where you exported `AAE_EXTERNAL_ATTESTED_IDENTITY`, run `python3 "$CLAUDE_PLUGIN_ROOT/scripts/run_core.py" findings.json` → validated ledger, verdicts (assigned by the code, never by you), dedup, metrics, manifest. No ARTIFACT_DEFECTIVE without a recorded defense.
7. **Meta-governor** (`agents/governor.md` + `scripts/governor_check.py`, the Stop hook): validates the *validator* — coverage, independence, calibration, confounds, **apparent consistency**. Never self-certifies; routes the residual to the human.

## Golden rule
Completion can **not** be "VALIDATED" on internal grounds. The maximum internal state is `EXTERNAL_REVIEW_PENDING` / `RELIABLE_WITH_RESERVATIONS`. The `Stop` hook enforces this.

## Output
JSON ledger + summary (completion, metrics, bite-rate, independence level, apparent-consistency flags) + residual for the human expert.
