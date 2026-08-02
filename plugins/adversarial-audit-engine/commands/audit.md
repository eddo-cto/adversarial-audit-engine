---
name: audit
description: Runs a 5-layer adversarial audit on an artifact (code, spec, paper, model). Orchestrates the roles, runs the deterministic Python core for gates/verdicts/metrics, routes the independent eye to a different vendor, and never reports "validated" without external review.
---

# /audit — orchestrator of the adversarial hive

You are the ARBITER/SYNTHESIZER. You coordinate the roles but you do **not** enforce the discipline — the Python code (`aae`) does. Argument: the path/artifact to audit (and, if it is an idea/space, the construens/discovery mode).

## Non-negotiable boundary (why this plugin exists)
- **Orchestration + tools (here, Claude Code):** spawn the roles, real execution (bash/node), search (web), collection of findings.
- **Deterministic discipline (Python `aae`):** the ledger schema, the verdict state machine, the defense-gate, the coverage-gate, metrics, the **meta-governor**. Invoke it via `scripts/run_core.py` and `scripts/governor_check.py`. Do NOT reimplement the gates as prompts.
- **Independence (cross-vendor):** the `external-auditor` and/or the `governor` must run on a **different-vendor model** (see `agents/external-auditor.md`). Two Claude agents do NOT count as independent.

## Flow
1. **Triage** (fixed checklist of dimensions: premises, inputs, mechanisms, outputs, boundary conditions, interface). Decide which specialist roles to activate; justify the exclusions.
2. **Oracle** (`agents/oracle.md`): a dossier of domain facts/mechanisms (never verdicts). On regulated/quantitative domains, real search.
3. **Hostile roles in parallel**, blind to each other, each with the **defense-gate** (attempt the strongest defense before condemning): `verifier` (execute the code — bash/node — trust no ✓), `propagator` (non-local: a choice here breaks a guarantee there), + reasoner/specialists if triage activates them.
4. **Deep-causal** (optional, richly-structured artifacts): root-cause clustering, forward/backward chiasm, gated scenarios.
5. **Deterministic core**: pass the collected findings to `scripts/run_core.py` → validated ledger, verdicts via the state machine, dedup, metrics. No ARTIFACT_DEFECTIVE verdict without a recorded defense.
6. **Independence**: run the `external-auditor` on a different vendor (or record that it is unavailable).
7. **Meta-governor** (`agents/governor.md` + `scripts/governor_check.py`): validates the *validator* — coverage, independence, calibration, confounds, **apparent consistency**. The governor does NOT self-certify and routes the residual to the human.

## Golden rule
Completion can **not** be "VALIDATED" on internal grounds. The maximum internal state is `EXTERNAL_REVIEW_PENDING` / `RELIABLE_WITH_RESERVATIONS`. The `Stop` hook enforces this.

## Output
JSON ledger + summary (completion, metrics, bite-rate, independence level, apparent-consistency flags) + residual for the human expert.
