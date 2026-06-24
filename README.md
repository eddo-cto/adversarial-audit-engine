# Adversarial Audit Engine

> A hive of adversarial roles that **tries to falsify** a high-complexity
> artifact, with a deterministic Python core that enforces the discipline.
> It never reports "validated" on internal grounds: **only a human validates.**

**[Read the story — how it was built and hardened across seven adversarial rounds](STORY.md)**

**Status: research preview (v0.7.0).** Tested across seven adversarial rounds and
on real cases (a consensus protocol, incident RCA, threat modeling, multi-regulation
conflicts, scientific peer review). It is not an oracle: it is a tool that
*multiplies* a competent human reviewer — it does not replace one.

**v0.7.0** adds a deterministic **anti-hallucination grounding gate**
(`aae/grounding.py`): a finding may only condemn on a quote that exists *verbatim*
in the source; a fabricated or paraphrased quote is reliably downgraded to "must be
read by a human." It was itself broken and hardened across three dedicated
adversarial rounds, and what it does and does not guarantee is stated precisely:

- **Guaranteed (deterministic):** *existence* — no fabricated or altered quote can
  condemn; and *recall robustness* — PDF noise (hyphenation, zero-width chars,
  curly quotes) produced **0 false-negatives** on 1,407 real spans.
- **Best-effort, not guaranteed:** *out-of-context / quote-mining* — a real
  substring lifted out of a negated clause is flagged by a conservative
  sentence-scope check that catches most but not all such cases (≈3 in 4 in
  testing). The residual is the irreducible **semantic** limit, declared rather
  than faked; meaning is validated by the human. The check costs ≈6% over-flagging
  (legitimate findings routed to a human) — the safe direction.

A companion **legal oracle** (`aae/legal_oracle.py`) checks, on demand, that cited
norms *exist* and are faithfully represented — never their interpretation, never
from model memory.

---

## What it does (and does not)

Given an artifact — a spec, a paper, a model, an analysis, code — the engine
deploys blind roles that attack it from different angles and look for its defects,
**attempting the strongest defense first** for every accusation (the defense-gate),
which drives false positives to near zero. A *pattern* may flag but never condemn:
only reading or execution can condemn.

It does not promise truth. It promises **disciplined falsification**: it either
finds a demonstrable defect, or it honestly declares that it cannot decide
internally and routes the case to a human expert.

## The core principle

Agents from the same model share the same blind spots. So the engine never
self-certifies:

| Independence level | Who reviews | Best possible verdict |
|---|---|---|
| 1 — same instance, different roles | same model | self-falsification, *not* validated |
| 2 — different model, same vendor | — | reduced reservations |
| 3 — **different vendor** | e.g. another provider | `CROSS_MODEL_REVIEWED` (reliability ↑, **not** validated) |
| 4 — **human expert** | a competent person | `VALIDATED` |

The independent eye can run on a different vendor (adapters included), but it is
still a machine: level 4 — the human — is the only instance that validates.

## The 5 layers

1. **Destruens** — point-by-point verification + propagation of *non-local* defects
   (a premise broken in one place invalidates a guarantee elsewhere).
2. **Construens** — cause-of-absence diagnosis with an inverted defense-gate.
3. **Generative** — deductive → inductive → **abductive** (rival hypotheses).
4. **Deep-causal** — root clustering, forward/backward chiasm, gated scenarios.
5. **Meta-epistemic governor** — validates the validator (bias, coverage,
   independence, "apparent coherence"). It does not self-certify: it terminates
   at the human.

## Hybrid architecture

Claude Code / Cowork orchestrates the roles (agents) and tools; the
**deterministic core** (`aae/`, bundled) enforces in *code* the verdict state
machine, the defense-gate, per-dimension coverage, dedup, metrics, and the
governor. The LLM provides the semantics; the code enforces the discipline.

## Installation (Claude Code)

```
/plugin marketplace add <this-repo-on-github>
/plugin install adversarial-audit-engine
```

Then, inside the project you want to audit:

```
/audit <path-or-description-of-the-artifact>
```

The Python core runs on the **standard library only** (no dependencies). The
cross-vendor independent eye requires the chosen provider's credentials,
configured on *your* machine.

## Declared limits (method honesty)

- It does not replace the expert: without level 4 the verdict stays "not validated".
- The "yardstick" (ground truth) can be wrong: the engine treats it as fallible.
- Coverage is *per defect class*, not global: some classes (e.g. genuinely novel
  non-local concepts) are routed to the human by construction.
- It is a research preview: use it as decision support, not as the final authority.

## Documents

- `plugins/adversarial-audit-engine/ARCHITETTURA_confini.md` — role boundaries and
  contract (in Italian).
- See also the architecture documents and per-round verdicts in the project.

## License & disclaimer

MIT (see `LICENSE`). See `DISCLAIMER.md`: the software is provided "as is", without
warranties; it is not professional advice (legal, financial, medical). Its output
must always be verified by a competent pers