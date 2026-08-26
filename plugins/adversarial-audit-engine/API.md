# Public API & stability contract (frozen for 1.x)

This is the **stable surface** of the Adversarial Audit Engine. Everything listed here is covered by
SemVer: within the `1.x` line it will not break. Anything **not** listed is internal and may change in a
minor release. Pinned by `tests/test_api_surface.py` and `tests/test_invariant_version.py`, so drift fails
CI rather than shipping silently.

## 1. The `--schema` payload contract (what an agent builds against)

`python3 scripts/run_core.py --schema` prints the exact contract: a `payload_template`, a
`finding_template`, the `vocabularies` (enum vocabularies), the `rules`, and a `run` hint. Build your
`findings.json` to match it, then feed it to the core. The stable keys:

**payload (top level):** `artifact_name`, `internal_identity`, `external_identity`, `max_posta`,
`source_primary_reachable`, `source_text`, `excluded_cells`, `triage` (`dimensions_present`,
`deploy_roles`), `findings[]`.

**finding:** `source_role`, `element`, `taxonomy_cell`, `defect_class`, `posta`,
`accusation` (`text`, `base`, `evidence`, `sections`), `defense` (`attempted`, `present`, `fact`),
`cost_to_fix`, `action`, `declared_limit`, `sources`, `severity`, `source_grade`, `action_state`.

**finding — optional temporal/epistemic axis (added 1.1.0, record-only).** These fields are **not
required** in `findings.json` and are **not** part of the enforced `--schema` template; they type a
finding's status across turns in longitudinal use and are ignored by the verdict state machine. They may
appear on the persisted ledger and round-trip if present: `temporal_status`
(`stable|provisional|transient|conflicted`), `likelihood` (float, only on `provisional`; a declared,
NON-calibrated estimate) + `likelihood_basis` (required when `likelihood` is set), `conflict_with`
(claim keys of opposing vectors), `perishable_pivot` (bool) + `pivot_valid_until`, `superseded_by`, and
`claim_key` — a deterministic cross-run identity of the claim, **auto-filled on serialize**, so every
persisted finding carries one. Consumers that do not know these fields may ignore them safely.

**vocabularies (enum members are additive in 1.x — new members may be appended, none removed/renamed):**
- `taxonomy_cell`: premises, inputs, mechanisms, outputs, boundary, interface
- `defect_class`: lookup, numeric, idiosyncratic_local, non_local_mechanical,
  non_local_conceptual_documented, non_local_conceptual_novel, epistemic, ethical, phenomenological
- `posta`: low, medium, high
- `evidence_base`: reading, execution, domain_knowledge, pattern
- `cost_to_fix`: trivial, low, medium, high
- `action_state`: open, done, deferred, deliberately_discarded
- `verdict` (**OUTPUT ONLY** — assigned by the code, never placed in a finding): accusa_vince,
  accusa_ridimensionata, artefatto_regge, da_leggere, conteso, pending

**rules (invariant in 1.x):** strongest-defense-first (no condemnation without a recorded defense);
`accusation.evidence` must be verbatim from `source_text` or an executed result (grounding gate);
non-local/conceptual findings need ≥2 cited sections; `source_grade` downgrades a condemnation resting on
grade>1 when a primary is reachable; a HIGH-posta run must record ≥1 `deliberately_discarded` hypothesis;
verdicts are output-only; the independent eye is credited only from the attested adapter identity.

## 2. CLI: `scripts/run_core.py` (the product entry point)

- `run_core.py --schema` — print the contract above.
- `run_core.py <findings.json>` (or payload on stdin) — run the deterministic discipline; write outputs.
- `run_core.py --metrics [dir]` — longitudinal, bias-resistant metrics panel.
- `run_core.py --version` — engine version. `run_core.py --help` — usage.

**Outputs** (in `AAE_OUT`, default `./aae_out`): `<stem>.ledger.json`, `<stem>.summary.txt`, and an
appended `_runs.jsonl` longitudinal record.

**Golden rule (invariant):** the core never reports `VALIDATED` on internal grounds. The best internal
completion is `EXTERNAL_REVIEW_PENDING`; closure to `VALIDATED` requires a human HMAC.

## 3. Programmatic core

```python
from aae.pipeline import discipline           # the single disciplined core
result = discipline(payload, *, attested_identity=None)   # -> AuditResult
```

`discipline(payload, *, attested_identity=None) -> AuditResult` is the one place the discipline lives;
`run_core.py` and `Orchestrator.run()` both delegate to it. `attested_identity` (keyword-only) is the
independent eye's identity **from the adapter**, never from the payload.

The package root (`aae`) re-exports the documented building blocks in `__all__` (schema types, orchestrator,
adapters, deterministic controls). Those names are stable; submodule internals are not.

## 4. Environment variables (stable names & meaning)

| Variable | Meaning | Default |
|---|---|---|
| `AAE_EYE` | independent eye: `ollama` \| `groq` \| `openrouter` \| a base URL | unset → honest level 1 |
| `AAE_EYE_KEY` | API key for the eye (not needed for `ollama`) | unset |
| `AAE_EYE_MODEL` | override the eye model | preset per vendor |
| `AAE_EYE_BASE_URL` | custom OpenAI-compatible endpoint | unset |
| `AAE_EYE_TIMEOUT` | eye call timeout (seconds) | 300 |
| `AAE_EXTERNAL_ATTESTED_IDENTITY` | identity the adapter attests after a real eye call → credits level 3 | unset |
| `AAE_CALIBRATION` | path to the Type-I calibration store (`_calibration.jsonl`) the run cites | unset → "NOT CALIBRATED" |
| `AAE_HUMAN_KEY` / `AAE_HUMAN_ATTESTATION` | HMAC key / attestation for human closure to `VALIDATED` | unset |
| `AAE_OUT` | output directory | `./aae_out` |
| `AAE_USAGE_LEDGER` | path for the usage ledger | unset |

## 5. SemVer policy for 1.x

**Will not break within 1.x:** the `--schema` payload/finding keys and rules; existing enum members
(§1); the `run_core.py` CLI flags and output filenames; `discipline()`’s signature and return type; the
`AAE_*` variable names and semantics; the golden rule and the grounding/defense/independence invariants.

**Allowed in a 1.x minor (additive, non-breaking):** new optional payload/finding fields; **appending**
new enum members; new `AAE_*` variables with safe defaults; new battery cards / calibration records
(these are data, versioned by `battery_id`, not API); new internal layers.

**Requires 2.0 (breaking):** removing/renaming a payload key, enum member, CLI flag, output filename, or
env var; changing `discipline()`’s signature incompatibly; weakening an invariant.

**Not part of the stable API:** internal module layout, `Orchestrator` internals, `MockLLMClient`
behavior specifics, the wording of summaries/flags, and the battery item contents.
