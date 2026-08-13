[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21288401.svg)](https://doi.org/10.5281/zenodo.21288401)
[![tests](https://github.com/eddo-cto/adversarial-audit-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/eddo-cto/adversarial-audit-engine/actions/workflows/tests.yml)

# Adversarial Audit Engine

> Audits a document or technical artifact by trying to **falsify** it: blind adversarial review across
> **different model vendors**, a deterministic grounding gate that blocks any finding not backed by a
> verbatim quote, explicit control of the falsifier's own **Type-I error**, and a code-enforced closure
> discipline. A hive of adversarial roles attacks the artifact; a dependency-free Python core enforces
> the rules. It never reports "validated" on internal grounds: **only a human validates.**

**[Read the story — how it was built and hardened across many adversarial rounds](STORY.md)**

**Status: research preview (v0.14.12).** A tool that *multiplies* a competent human reviewer — it does not
replace one, and it is not an oracle. Tested across many adversarial self-audit rounds and on real cases
(a consensus protocol, incident RCA, threat modeling, multi-regulation conflicts, scientific peer review).

## What is enforced in code (the trust protocol)

The value is not detection accuracy; it is that the discipline lives in **ordinary Python**, each rule
pinned by a test, so it behaves identically every run and cannot be talked out of by a prompt:

- **Non-closure is cryptographic.** `VALIDATED` requires a valid HMAC of the ledger digest under a key the
  operator holds outside the model's reach (`aae/attestation.py`); the model authors the payload but not
  the key, so it cannot sign its own validation.
- **Independence is attested, not claimed.** Cross-vendor review is credited only from the identity the
  calling adapter reports; a different-vendor label present only in the payload buys nothing.
- **A run is a run only under an A+B contract.** A *measured* minimum of required layers must actually have
  run **and** every other layer must carry an explicit `RAN`/`NOT_APPLICABLE`/`MISSING` verdict
  (`aae/run_manifest.py`); otherwise the run is `INVALID`, completion is forced to `INVALID_RUN` (which
  overrides even a human `VALIDATED`), and `run_core.py` exits non-zero. The minimum was **measured**, not
  assumed (`MEASUREMENT_layer_contribution.md`).
- **Grounding gate (anti-hallucination).** A finding may only condemn on a quote that exists *verbatim* in
  the source (`aae/grounding.py`); a fabricated or paraphrased quote is downgraded to "must be read by a
  human."
- **Defense-gate.** Every accusation must attempt the strongest defense first; condemnation without a
  recorded defense is structurally impossible — the rule most responsible for the near-zero false-positive
  rate.
- **Type-I control on the falsifier itself** (`aae/negation_spectrometry.py`): a bounded, measured
  false-demolition rate, so the auditor cannot quietly over-demolish valid artifacts.

Full version history: **[`CHANGELOG.md`](CHANGELOG.md)**.

## What it does (and does not)

Given an artifact — a spec, a paper, a model, an analysis, code — the engine deploys blind roles that
attack it from different angles and look for its defects, **attempting the strongest defense first** for
every accusation. A *pattern* may flag but never condemn: only reading or execution can condemn.

It does not promise truth. It promises **disciplined falsification**: it either finds a demonstrable
defect, or it honestly declares that it cannot decide internally and routes the case to a human expert.

## The core principle

Agents from the same model share the same blind spots. So the engine never self-certifies:

| Independence level | Who reviews | Best possible verdict |
|---|---|---|
| 1 — same instance, different roles | same model | self-falsification, *not* validated |
| 2 — different model, same vendor | — | reduced reservations |
| 3 — **different vendor** | e.g. another provider | `CROSS_MODEL_REVIEWED` (reliability ↑, **not** validated) |
| 4 — **human expert** | a competent person | `VALIDATED` |

The independent eye can run on a different vendor (adapters included), but it is still a machine: level 4
— the human — is the only instance that validates.

## The 5 layers

1. **Destruens** — point-by-point verification + propagation of *non-local* defects (a premise broken in
   one place invalidates a guarantee elsewhere).
2. **Construens** — cause-of-absence diagnosis with an inverted defense-gate.
3. **Generative** — deductive → inductive → **abductive** (rival hypotheses).
4. **Deep-causal** — root clustering, forward/backward chiasm, gated scenarios.
5. **Meta-epistemic governor** — validates the validator (bias, coverage, independence, "apparent
   coherence"). It does not self-certify: it terminates at the human.

> The method keeps its terms of art (the Latin layer names, coined terms like *negation spectrometry*).
> Every module and term is mapped to one plain-language line in
> **[`plugins/adversarial-audit-engine/GLOSSARY.md`](plugins/adversarial-audit-engine/GLOSSARY.md)** —
> readable without the papers.

## Hybrid architecture

Claude Code / Cowork orchestrates the roles (agents) and tools; the **deterministic core** (`aae/`,
bundled) enforces in *code* the verdict state machine, the defense-gate, per-dimension coverage, the A+B
run-validity manifest, dedup, metrics, and the governor. The LLM provides the semantics; the code enforces
the discipline.

## Installation (Claude Code)

```
/plugin marketplace add <this-repo-on-github>
/plugin install adversarial-audit-engine
```

Then, inside the project you want to audit:

```
/audit <path-or-description-of-the-artifact>
```

The Python core runs on the **standard library only** (no dependencies). The cross-vendor independent eye
requires the chosen provider's credentials, configured on *your* machine.

## Reproduce the claims

```
git clone https://github.com/eddo-cto/adversarial-audit-engine && cd adversarial-audit-engine
cd plugins/adversarial-audit-engine
python3 -m unittest discover -s tests        # the full invariant suite
for b in calibration real_errors inter_nature baselines; do
  python3 benchmarks/$b/reproduce.py --strict
done
```

## Declared limits (method honesty)

- It does not replace the expert: without level 4 the verdict stays "not validated".
- The "yardstick" (ground truth) can be wrong: the engine treats it as fallible.
- Coverage is *per defect class*, not global: some classes (e.g. genuinely novel non-local concepts) are
  routed to the human by construction.
- It is a research preview: use it as decision support, not as the final authority.

## Documents

- **[`GLOSSARY.md`](plugins/adversarial-audit-engine/GLOSSARY.md)** — every module and coined term in one
  plain-language line.
- **[`INVARIANTI_metodo.md`](plugins/adversarial-audit-engine/INVARIANTI_metodo.md)** — the
  non-negotiable method invariants.
- **[`MEASUREMENT_layer_contribution.md`](plugins/adversarial-audit-engine/MEASUREMENT_layer_contribution.md)**
  — how `REQUIRED_LAYERS` is measured, not assumed.
- **[`ARCHITETTURA_confini.md`](plugins/adversarial-audit-engine/ARCHITETTURA_confini.md)** — role
  boundaries and contract (in Italian).
- **[`USAGE_LEDGER.md`](plugins/adversarial-audit-engine/USAGE_LEDGER.md)** — the meta persistence layer.
- **[`INDEPENDENCE_free.md`](plugins/adversarial-audit-engine/INDEPENDENCE_free.md)** — how to get a
  **free level-3 independent eye** (local Ollama / free-tier APIs) without a paid API.

## Papers

This repository also hosts the papers that formalise what the engine produces and test whether mature
scientific communities do the same thing. All are archived on Zenodo with a permanent DOI (see
`CITATION.cff`).

- **`papers/system-description/`** — *The audit engine, described as it runs: a code-enforced trust
  protocol.* The empirical/architectural companion: the trust protocol above, the execution manifest, the
  10-run layer measurement, and the self-audit trail (`audits/`). Includes a short paper positioned for the
  **JUDGe @ NeurIPS 2026** workshop on evaluator reliability and validity.
- **`papers/managing-circularity/`** — *Managing epistemic circularity in self-referential evaluation: the
  survivor gate, and how three scientific ledgers resolve indeterminacy.* The main theory paper (Survivor
  Gate, declared non-closure, three real reliability ledgers: Kepler KOI, ClinVar/ACMG, NVD/CVE).
- **`papers/commensurability/`** — *Graded, asymmetric commensurability is not a quantale-enriched
  distributor.* The formal companion (C₃ quantale, two negative results, interleaving distance).
- **`papers/engineering-frontier/`** — *The engineering frontier of verification.* A short methodological
  note with a runnable demo (`frontier_demo.py`).

## License & disclaimer

MIT (see `LICENSE`). See `DISCLAIMER.md`: the software is provided "as is", without warranties; it is not
professional advice (legal, financial, medical). Its output must always be verified by a competent person.
