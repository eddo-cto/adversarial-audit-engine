# The audit engine, described as it runs: a code-enforced trust protocol for an adversarial LLM auditor, where the discipline is code, not prompts

*Systems-and-methods paper. Its contribution is a **trust protocol** — a small set of invariants an
adversarial LLM-audit pipeline is made to obey **in ordinary code**, not in prompts: (i) it may never
return `VALIDATED` on its own grounds, and human closure is a **cryptographic** attestation the model
cannot forge; (ii) cross-model independence is **attested by the calling adapter**, not read from a
self-report; (iii) a run counts as a run **only** if a measured minimum of layers actually executed
**and** every other layer was adjudicated applicable-or-not with a recorded verdict (an A+B contract),
otherwise the pipeline **refuses to close** and exits non-zero; (iv) the engine is turned on itself and
the audits are shipped. This matters because recent large-scale evidence is that LLM judges are reliable
without being valid — high test–retest consistency coexists with severe bias
([Reliability without Validity, arXiv:2606.19544](https://arxiv.org/abs/2606.19544)). A reliable-but-
invalid judge is dangerous precisely when it can certify itself; this paper's protocol is a mechanism
that structurally forbids that self-certification. The closest adversarial cousin,
[Refute-or-Promote (arXiv:2604.19049)](https://arxiv.org/abs/2604.19049), stage-gates candidate defects
with an adversarial kill-mandate and a cross-model critic to raise precision; it keeps a human
orchestrator and no enforced non-closure. Our distinctive is not detection accuracy — it is the
code-enforced closure discipline, the cryptographic independence, the non-bypassable run-validity
contract, and the self-audit trail. Positioned for the reliability-and-validity-of-evaluators agenda of
[JUDGe @ NeurIPS 2026](https://judge2026.github.io/), whose community deliverable is exactly a
judge-deployment disclosure standard.*

*Companion to two theory papers on the same engine
([Managing epistemic circularity](../managing-circularity/), [Graded commensurability is not a
quantale-enriched distributor](../commensurability/); Zenodo DOI 10.5281/zenodo.21288401), which build a
mathematics after the fact and hang the system underneath it (§11). This paper goes the other way: it
describes what the machine does and turns each methodological claim into a file you can read or a test
you can run — the one exception, the blind re-adjudication of §6, is attested rather than public and is
flagged as such in §8 — so it is falsifiable, from inside, without waiting for the external eye.*

**Artifact.** `github.com/eddo-cto/adversarial-audit-engine` (MIT), at tag `v1.0.5` (the round-18
trust-protocol commit; §9). Four reproducible benchmarks under
`plugins/adversarial-audit-engine/benchmarks/`, each with a `reproduce.py --strict` (pure standard
library), and 173 unit tests, checked in CI on `main` and every pull request across Python 3.10–3.13.
The protocol invariants above are themselves tests: the run-validity contract, the non-bypassable
refusal, the cryptographic-closure check, and a CI step that fails if the engine ever prints
`VALIDATED` end-to-end without a human.

---

## 1. Introduction — the problem is closure, and the fix is code

An LLM used to *evaluate* — a judge, a reviewer, an auditor — has a failure mode more dangerous than
being wrong: being **wrong while internally consistent**. The largest systematic study of
LLM-as-a-judge to date reports exactly this dissociation — reliability without validity: test–retest
consistency above 0.95 coexisting with severe position bias, and exact-match agreement inflating
discriminative ability once corrected for chance ([arXiv:2606.19544](https://arxiv.org/abs/2606.19544)).
A judge that is stable, confident, and biased is at its most harmful the moment it is allowed to
**certify itself** — to declare its own output validated, or to count its own agreement as
independence. Everything downstream (a training signal, a safety gate, a disclosure) then inherits an
error the system cannot see.

This paper's contribution is a **trust protocol** that makes that self-certification structurally
impossible, and makes the prohibition *checkable*. It is not a formalism and not an accuracy claim; it
is a set of invariants enforced in ordinary Python, each pinned by a test:

1. **Non-closure is cryptographic, not conventional.** The pipeline can reach `VALIDATED` only through a
   valid HMAC of the ledger digest under a key the operator holds outside the model's reach. The model
   authors the payload but not the key, so it *cannot* sign its own validation (§4).
2. **Independence is attested, not claimed.** Cross-model review is credited only from the identity the
   calling *adapter* reports; a different-vendor label present only in the payload buys nothing (§4).
3. **A run is a run only under an A+B contract.** A measured minimum of layers must actually have
   executed (A) **and** every remaining layer must carry an explicit applicable/not-applicable verdict
   (B); otherwise the run is `INVALID` and the pipeline **refuses to close**, overriding even a human
   attestation, and exits non-zero (§4, §9). The minimum itself was *measured*, not assumed (§9).
4. **The engine audits itself and ships the audits.** Its own adversarial rounds — including a
   different-vendor review that killed this paper's original headline claim — are committed under
   `audits/` and narrated in §9, because a system whose value is adversarial honesty must show the
   audits that caught it.

Two things follow. The method is **reproducible by a stranger** — clone, run, watch the gates fire and
the refusal trigger — and it **separates cleanly** the part that is a language model (fallible,
non-deterministic; where defects are found) from the part that is ordinary code (deterministic; where
verdicts and closure are decided). That separation is the whole design, and it is what distinguishes
this from adversarial defect-discovery pipelines such as
[Refute-or-Promote](https://arxiv.org/abs/2604.19049), which share the adversarial-kill and
cross-model-critic ideas but keep a human orchestrator and no enforced non-closure (§10).

The empirical section (§6) is deliberately secondary: a small-sample **descriptive dissociation**
between two candidate axes — capability and independence — offered as hypothesis-generating (n=7, one
run per nature), **not** as two identified orthogonal frontiers. It illustrates the protocol on real
errors; it is not the load-bearing claim, and the round-11 different-vendor review (§9) is why it is
scoped this modestly.

## 2. The graph, as it actually runs

The engine is a **Claude Code plugin**. One orchestrator command (`/audit`) spawns a small set of role
sub-agents, collects what they produce, and hands the collection to a deterministic Python core that
assigns the verdicts and decides completion. The orchestrator **coordinates but does not judge**; the
judging is code. This is the most important fact about the system and the one the algebra hides.

```mermaid
flowchart TD
    A[/audit orchestrator/\nLLM: coordinates, does NOT judge] --> T[Triage\nfixed taxonomy: premises·inputs·mechanisms·outputs·boundary·interface]
    T --> O[Oracle\nLLM+web: cited FACTS only, no verdicts]
    O --> H1[Verifier\nLLM: recompute every number; EXECUTE code where runnable]
    O --> H2[Propagator\nLLM: non-local — a choice here breaks a guarantee there]
    O --> H3["reasoner / domain specialists\n(activated by triage)"]
    H1 --> C[Deterministic core  aae/  — Python, standard library]
    H2 --> C
    H3 --> C
    C -->|defense-gate · coverage-gate\nverdict state machine · dedup · metrics| C2[Validated ledger + verdicts]
    C2 --> X[External-auditor\nDIFFERENT VENDOR via adapter — the only real independence lever]
    X --> G[Governor\nassesses the VALIDATOR, not the artifact:\ncoverage·independence·calibration·confounds·apparent-consistency]
    G --> S{{Stop hook → governor_check.py}}
    S -->|never VALIDATED on internal grounds| R[Residual → human external eye]
```

Read the graph as three bands. **Discovery** (orchestrator, oracle, hostile roles) is all language
model: where facts are fetched, code is executed, candidate defects found. **Discipline** (the `aae`
core) is all deterministic Python: where candidate defects become verdicts under fixed rules.
**Closure** (external-auditor, governor, Stop hook) is where the process refuses to certify itself and
routes the residue outward. The bands are not a metaphor — they are, respectively, the `agents/` +
`commands/` directories, the `aae/` package, and the `hooks/` + cross-vendor adapter.

**The roles, in one line each** (from the agent front-matter). *Oracle* (`sonnet`, no write): a cited
factual dossier — exact values, standards, formulas, known mechanisms — and **no verdicts**; it even
declares its own confound (surfacing mechanisms risks handing the answers to the attackers), which the
governor later assesses. *Verifier* (`sonnet`): recomputes every number, threshold, unit and
cross-reference and, **where code is executable, executes it** (bash/node) rather than reasoning about
it — the lesson that catches crashes read-only audits miss. *Propagator* (`sonnet`): the non-local
role; tabulates premises and guarantees, then builds the concrete step-by-step **sequence** that
violates each guarantee. *External-auditor* (`sonnet`): the independent eye, whose own file warns that
run by a same-family model it does **not** constitute independence — its value is realised only when
routed to a different vendor. *Governor* (`opus`): assesses the **validator**, not the artifact —
coverage, independence, calibration, confounds, and above all *apparent consistency* (100% / zero false
positives / no declared limit = the signature of a closed loop). Every hostile role carries the
**defense-gate** (defend before condemning) and is `disallowedTools: Write, Edit` — an auditor cannot
edit what it audits. These are declared in front-matter, not left to prompt goodwill.

## 3. The unit of work is a Finding, not a sentence

The atom the system manipulates is not free text. It is a `Finding` (`aae/schema.py`), and its shape is
the discipline made concrete:

- an **Accusation** with an `EvidenceBase` — one of `READING`, `EXECUTION`, `DOMAIN_KNOWLEDGE`,
  `PATTERN`. A `PATTERN`-only accusation (regex or string match) **may flag but never condemn**; the
  verdict state machine enforces it (`adjudicate`, Rule 1, forces `NEEDS_READING` for any pattern
  base). This is why the engine does not fire on surface cues.
- a **Defense** with an `attempted` flag — a first-class field, not an afterthought.
- a **DefectClass** from a fixed taxonomy:

```python
class DefectClass(str, Enum):
    LOOKUP = "lookup"                              # value/version/threshold vs a standard
    NUMERIC = "numeric"                            # a re-computable calculation error
    IDIOSYNCRATIC_LOCAL = "idiosyncratic_local"    # local reasoning/derivation error
    NON_LOCAL_MECHANICAL = "non_local_mechanical"  # two sections, incompatible values
    NON_LOCAL_CONCEPTUAL_DOCUMENTED = "non_local_conceptual_documented"
    NON_LOCAL_CONCEPTUAL_NOVEL = "non_local_conceptual_novel"  # residual limit → human
    EPISTEMIC = "epistemic"                        # validation / inference / construct validity
    ETHICAL = "ethical"                            # harm / autonomy / value trade-off
    PHENOMENOLOGICAL = "phenomenological"          # lived-experience / perception failure
```

This is the production classifier. Note (round-11 F-03): §6's *empirical* study uses a coarser,
experiment-specific grouping — general-reasoning / external-data / domain-re-derivation — **not** these
nine `DefectClass` values, and no crosswalk between the two is shipped. So §6 describes a boundary in its
own labels; it does not by itself show that this production enum carves that boundary. Connecting the two
(an explicit crosswalk, or re-running §6 over the production classes) is deferred work.

A non-local class with fewer than two cited sections is flagged by the integrity report,
which the documented `run_core` path runs (round-9 F-SECTIONS fix); a conceptual-novel defect is
marked the residual limit and routed to a human. The data structure already encodes what the engine
can and cannot close.

## 4. The verdict state machine — assigned by code, not by a prompt

This is the crux, and the reason the system is trustworthy in a way a prompt is not. **Verdicts are not
emitted by the language model.** The roles produce findings with evidence; the deterministic core
assigns the verdict. The `Verdict` enum is fixed (`ARTIFACT_DEFECTIVE`, `REDUCED`, `ARTIFACT_HOLDS`,
`NEEDS_READING`, `NEEDS_EXPERT`, `PENDING`), and three pure functions in `aae/gates.py` do the work:

1. **defense-gate** (`enforce_defense_gate`): any `ARTIFACT_DEFECTIVE` finding whose defense was never
   attempted is **automatically downgraded** to `NEEDS_EXPERT`. Condemnation without a recorded defense
   is structurally impossible — the one rule most responsible for the near-zero false-positive rate.
2. **coverage-gate** (`enforce_coverage_gate`): every taxonomy dimension must be touched by a finding
   or explicitly excluded-with-justification, else the ledger is stamped `COVERAGE INCOMPLETE`. You
   cannot pass by looking only where it is easy.
3. **independence-gate** (`evaluate_completion`): decides the final state. Its behaviour is the whole
   ethic in one table:

| condition (in the code) | completion state |
|---|---|
| open `NEEDS_READING` / `NEEDS_EXPERT` findings | `BLOCKED_OPEN_ITEMS` |
| **verified** human attestation: a valid HMAC of the ledger digest under the operator key | `VALIDATED` |
| **adapter-attested** different **vendor** (independence level 3) | `CROSS_MODEL_REVIEWED` — *"reliability improved — but NOT validated"* |
| different-vendor identity **claimed only in the payload** | `CROSS_MODEL_CLAIMED` — *"independence NOT credited (level 1)"* |
| same-vendor different model (level 2) | `INTRA_VENDOR_REVIEWED` — *"shared priors, not cross-vendor"* |
| no attested external identity | `EXTERNAL_REVIEW_PENDING` |

**Only a human returns `VALIDATED`, and closure is cryptographic (round 11).** The attestation is an
**HMAC of the ledger digest under a key the operator holds outside the model's reach** (`AAE_HUMAN_KEY`);
a bare token that does not verify closes nothing. Because the model authors the payload but not the key,
it *cannot* produce the signature — "the process cannot self-report validated" is now enforced by
cryptography, not by an honesty convention. Independence is **attested, not claimed**: level 3 is
credited only from the identity the calling adapter actually reports; a different-vendor identity present
only in the payload is `CROSS_MODEL_CLAIMED` and its independence is not credited. A `Stop` hook then
runs `governor_check.py` **in the operator's environment**, **re-verifies the HMAC**, and if a
`VALIDATED` does not verify it **downgrades the ledger on disk** and resets independence. Non-closure is
not a posture here: it is checked in code at write time and re-checked at Stop time, both against the
same operator secret — one mechanism at two moments, not two independent mechanisms.

**The run-validity contract (A+B) — what makes it a method, not a prototype (rounds 13–18).** A pipeline
that quietly *skips* half its layers can still print a confident verdict; the danger is a run that looks
complete because nobody counted what did not happen. So a run is admitted as a run only under two
conditions, computed in code (`aae/run_manifest.py`). **(A)** a measured minimum of required layers —
`triage, oracle, verifier, propagator, governor` — must have **actually executed**, measured from the
data each produced (findings by `source_role`, oracle from the distinct sources it cited, governor from
the meta verdict), not from self-report. **(B)** every *other* declared layer must carry an explicit
`RAN` / `NOT_APPLICABLE` / `MISSING` status with a justification, so the denominator of "what could have
run" is never unknown. The manifest then computes `run_validity ∈ {VALID, INVALID, INCOMPLETE,
RECORD_ONLY}`. If it is not `VALID`, the **refusal is non-bypassable**: completion is forced to
`INVALID_RUN` — which **overrides every other state, including a valid human `VALIDATED`** — and
`run_core` exits non-zero (round 18). A run cannot be closed by adding a signature to an incomplete
process; the process must first be *complete and adjudicated*. Crucially, `REQUIRED_LAYERS` was **not
asserted** — it was read off a 10-run, 8-class measurement of which layers actually carry load, which
corrected an earlier over-inclusion (`reasoner` was dropped from required to optional when two classes
recovered their defects without it; §9). Measuring the minimum before freezing it is the difference
between a contract and a guess.

## 5. The honest point about the technology

What this is: an orchestration of **language-model sub-agents** (Sonnet for the hostile roles, Opus for
the governor; each with an effort budget, a turn cap, and write tools removed) wrapped around a
**deterministic core of ordinary Python** — standard library, no machine learning, ≈4,200 lines across
30 small modules. Intelligence and fallibility live in the LLM band; discipline and trust live in the
Python band. Keeping them apart is the entire design.

Where it is solid: the gates, the verdict state machine, the run-validity manifest, the metrics, the
dedup, and the governor's deterministic check are pure functions with tests (173 passing); they behave
identically every run, and the four benchmarks reproduce to the digit in CI.

Where it is fragile, plainly: (i) the discovery band is a language model, so *which* candidate defects
surface varies run to run — the discipline bounds the false positives, not the recall variance; (ii)
real cross-vendor independence depends on an **adapter** (an MCP server or a script calling another
vendor's API) the operator must wire up — absent it the external-auditor is theatre, and the code says
so; (iii) the "5-layer" framing describes roles, not guarantees — the guarantees are the
three gates plus the A+B run-validity contract, fewer and humbler than any marketing.

## 6. What actually happens — a descriptive dissociation, and its limits

The theory papers name **one** frontier: independence (ρ). Running the engine on real errors surfaced a
candidate **second axis — capability**, and the two show *distinct landing patterns* in a small sample.
We report this as a **descriptive dissociation** and hypothesis-generating evidence, **not** a causal
decomposition: `n` is seven, there is one run per nature, and "nature" confounds vendor with model
capability, tool access, and run-to-run variance. What the data license is a suggestive separation of
*where the lens lands*, not two identified orthogonal frontiers. (This scoping is the result of the
round-11 different-vendor review; see §9.)

**Setup (benchmarks `real_errors`, `inter_nature`, `baselines`).** Seven real published papers that
later received a formal *Matters Arising* supply third-party ground truth: each has a known, formally
refuted defect. Seven cross-domain **decoys** test for false alarms. The same targets are run under
three different model "natures", and against the same strong model used *without* the engine's protocol.
Adjudication of whether a produced finding *lands* on the sealed target uses a strict rule — same
*locus* in the paper **and** same *mechanism* — and has been **re-adjudicated blind** by a fresh,
isolated instance (relabelled pairs, neutralised targets, no key, no class labels); it reproduced the
per-pair result **identically** to the coordinator on all 14 pairs (P landing 1/4, A landing 3/3, decoy
false-positives 0/7). This **reduces direct coordinator-label dependence** — it does not dissolve shared
same-vendor rubric, target-definition, or paper-selection bias; what remains un-blinded is closure, by
construction.

**The dissociation.** Group the real targets by defect mechanism and ask which model natures recover
them:

| defect class | example | primary nature | across three natures | reading |
|---|---|:---:|:---:|---|
| **general-reasoning** | internal contradiction, definitional entailment (ORIG_03) | caught | caught by all | inside both frontiers — always caught |
| **external-data** | a claim resolvable only against an outside source (ORIG_01/02/06) | **0/3** | **monotone: A 0/3 ≤ B 2/3 ≤ C 3/3** | **independence** frontier — recovery *rises with nature-distance* (ρ<1) |
| **domain-re-derivation** | re-integrate the equations, recompute a physical quantity (ORIG_04/05/07) | 0/3 | **0/3 for every nature** | **capability** frontier — *no* nature recovers it |

Two patterns stand out, and a permutation test over the class labels gives **p = 0.007** against
arbitrary assignment — so the segregation is not noise. The **capability-limited** pattern is the class
**no** nature recovers — and that a vanilla firehose of up to 155 findings *on that very target* also
misses — because it needs *executing* a domain re-derivation, which no text-only auditor does; this reads
as a property of the *task*. The **independence-sensitive** pattern is the class a *different* nature
does recover (monotone across natures), echoing `engineering-frontier`'s Proposition 2 — internal
agreement cannot separate genuine from coordinated consensus, an external draw can. But calling these
two *orthogonal frontiers* would require holding capability and tools fixed while varying independence,
which this design does not do. So the honest reading is: two mechanism classes landed differently across
three model runs — a descriptive dissociation, not an identified pair of causal axes.

**The honest sensitivity numbers.** On a single nature, real class-P recall is **1/4 (25%)** with
**0/7** decoy false-positives — the number the synthetic calibration (88% present-verifiable; see
`benchmarks/calibration`) overstated, and which we keep in view precisely because it is the honest one.
The 25% is not the product's accuracy; it is the calibration of a *general-reasoning* auditor on real
domain errors.

**What the discipline buys (baseline, `benchmarks/baselines`).** Against the same strong model run
*without* the protocol, discipline does **not** change *which* targets are caught (landing identical,
4/7, same targets) — it **emits ~5× fewer findings** (≈18 per paper vs ≈88, per-paper range 2.5×–8.4×)
and declares a boundary the vanilla judge does not. This is a false-alarm **proxy**, not a measured
false-positive rate: the non-target findings are not each adjudicated, so the honest claim is *lower
finding volume with the same landing*, and the ≈70 extra vanilla findings per paper are largely
speculative objections the defense-gate would downgrade. A deterministic OSS baseline (statcheck) lands
0/7: its class (APA-style NHST p-values) is disjoint from these defects. This grounds the literature's
"reliability without validity" on real errors: the value is calibration and a declared boundary, not a
recall crown.

Put it together as a **bounded, described footprint on seven targets**, not a theorem: the engine landed
on the general-reasoning-reconstructible defect; a *different* nature additionally recovered the
external-data class; the domain-re-derivation class was missed by every nature. It does **not** follow
that the engine routes "everything else" to a human — the code auto-routes only the conceptual-novel
class, and other classes receive internal verdicts. What the engine reliably reports is *which* class a
given defect fell in, and it declares the classes it did not reach.

## 7. Honest limits

`n` is small throughout (single-digit target and decoy counts): this **circumscribes** the claims, it
does not certify them, and nothing here reaches significance. Matters Arising are *conclaimed* errors,
not a representative sample. The over-flagging ratio is a **proxy** for false positives, not a measured
false-positive rate, and it varies with the paper (reported with its range). Two targets carry declared
wrinkles: one external-data target is adjudicator-dependent (which is the ρ<1 phenomenon itself, not a
judgment error), and one re-derivation target was confounded by text extraction dropping the governing
equation (irrelevant to recall, since that class is missed regardless). And the whole apparatus, this
paper included, is a **survivor**: two same-nature adjudicators reduce coordinator-label dependence but stay at
independence level 1–2; no number reaches `VALIDATED` without the different-nature axis and, ultimately,
the external human eye. That is the engine's own thesis applied to itself.

Two closure guarantees were, through round 10, conventions rather than proofs; **round 11 made them
enforced** (see §9). Human closure is now cryptographic: `VALIDATED` requires a valid HMAC of the ledger
digest under an operator key the model cannot reach, so a model that authors the payload can no longer
self-report validation. And independence level 3 is now **attested by the calling adapter**, not read
from a payload string: an unattested different-vendor identity is `CROSS_MODEL_CLAIMED`, its independence
uncredited. One honest caveat survives and is load-bearing precisely where the earlier draft said it was
not: the **§6 inter-nature data were collected before round 11**, so the vendor identities behind
`nature_A/B/C` rest on a private register's attestation, not on the new adapter check. The independence
*interpretation* of §6 is therefore still privately attested (see §6 and §8), even though the code that
would attest a future run is now in place.

## 8. Reproducibility statement

Everything quantitative above recomputes from versioned, anonymized data with the standard library and
no install:

```bash
git clone --branch v1.0.5 https://github.com/eddo-cto/adversarial-audit-engine && cd adversarial-audit-engine
for b in calibration real_errors inter_nature baselines; do
  python3 plugins/adversarial-audit-engine/benchmarks/$b/reproduce.py --strict || echo "DIVERGED: $b"
done
python3 -m unittest discover -s plugins/adversarial-audit-engine/tests   # 173 tests
```

The protocol invariants of §1 and §4 are themselves in that suite: `tests/test_run_manifest.py` pins the
A+B contract and the non-bypassable `INVALID_RUN` refusal, `tests/test_closure_hardening.py` the
cryptographic attestation, and the CI workflow runs the engine end-to-end and **fails if `VALIDATED`
is ever printed without a human**. Each `reproduce.py --strict` exits non-zero on any divergence from its
`claims.json`; each benchmark's guard is verified non-vacuous by an automated perturbation test
(`tests/test_benchmarks_guards.py` flips one datum in each benchmark and requires `--strict` to fail).
The one claim in this paper that is *not* clone-and-run is the §6 blind re-adjudication: its materials
are attested in a private sealed register
(a fresh instance reproduced the coordinator's result on all 14 pairs) rather than shipped, because
anonymization is deliberate — the public benchmarks carry only `(mechanism, class, landing, counts)`.
Paper identities (PMCIDs, DOIs, the sealed Matters-Arising targets) stay private; naming a paper beside
a "missed defect" adds nothing to any statistic and risks misreading. Red line: the engine flags, it
does not accuse.

## 9. The engine audited itself (rounds 9–18: hardening, a different-vendor review, and a measured contract)

The claims in §3–§4 above are stronger than they would have been a revision ago, and the reason is worth
telling because it *is* the method. A separate instance of the engine — a distinct session on a separate
account, but the **same vendor as the engine's own roles, so independence level 1–2 and explicitly not a
different nature** — was pointed at this paper's own draft. It returned a disciplined ledger (defense
attempted on every accusation, four accusations withdrawn against a verifiable fact, and every
self-reported figure independently recomputed by execution rather than accepted) and it **upheld four
accusations against the engine's own closure guarantees**: independence
was a string inequality, not vendor-aware (F-VENDOR); human validation was a `"human"` prefix the
orchestrating model could author (F-HUMAN); the `Stop` hook informed but never enforced (F-HOOK); and
the ≥2-sections rule was inert on the documented entry point (F-SECTIONS). Each is now fixed and pinned
by a regression test (`tests/test_gates_and_verdicts.py`, `tests/test_closure_hardening.py`):
vendor-aware completion states, an out-of-band human attestation, a hook that downgrades an unattested
`VALIDATED` on disk, and integrity checks wired into `run_core`. That the finder sat at the *minimum*
independence level is the point worth keeping: same-nature auditing is weak by construction, and it
still located four defects the authors had not seen.

Then the same engine, again at independence level 1, was pointed at *this hardened version* and returned
four more. One sat **inside the round-9 fix itself**: the hook downgraded a spoofed `VALIDATED`'s
completion state but left its independence level at `HUMAN_DOMAIN_EXPERT`, so the corrected ledger still
read as human-closed to every downstream reader — now reset to level 1, with a regression test that
asserts *both* fields, since asserting only the completion state is what had let the defect through. The
other three were the paper's own honesty debts, not the engine's: the artifact pinned a commit that
predated its own corrections (now pinned to an immutable tag); §4 called two checks "independent" when
both read the same operator secret, ρ = 1 (now "one mechanism at two moments"); and this very section had
called the round-9 audit "a genuinely different-nature check" — a self-assigned independence upgrade in
the paper whose thesis is that such upgrades are the failure mode. All corrected; two residues (an
unvalidated human token, a claimed rather than attested vendor level) are declared in §7 rather than left
for a reader to find.

This is the paper's thesis surviving its own instrument, twice. A level-1 engine found four closure
defects; the author closed them in code; the same engine returned and found four more, one *inside the
previous fix*; the author closed those too and declared the two he could not yet close. Before round 9,
"the discipline is code" held for the defense-gate and coverage-gate and quietly failed for closure —
string convention; closing it made the claim fully true for the sections-gate and for vendor-awareness,
and contracted human-closure forgery from a payload field to an operator secret whose strength is the
operator's own hygiene rather than eliminating it. Both audit trails — the round-9 ledger and the
round-10 work order — are committed under `papers/system-description/audits/`; they are self-audits at
independence level 1 and validate nothing, which is exactly why they are shown rather than summarized.

Then the paper went to a genuinely **different vendor** — the first review at independence **level 3**,
the axis §7 said the system could not supply for itself. It reproduced the four benchmark guards, then
attacked the central result and won. §6's *"two orthogonal frontiers, dissociated by the data,"* its
*"iff"* footprint, and §3's claim that the boundary runs *"exactly along"* the production `DefectClass`
taxonomy were over-claims: n=7 with one run per nature cannot separate capability from independence, and
the empirical labels are not the production classes. §6, §3 and the abstract are scoped to a *descriptive
dissociation* accordingly. And the different vendor confirmed that the two closure guarantees round 10
had only *declared* as residue (C1, C2) were still conventions — so this time we **built** them: human
closure is now a cryptographic HMAC the model cannot forge, and independence level 3 is credited only
from the adapter that made the call (round-11; §4, §7, `aae/attestation.py`). The level-3 work order is
committed under `audits/` beside the level-1 ledgers. The asymmetry is the point: a different-vendor eye
caught the headline over-claim two same-vendor rounds had missed — the independence scale doing its job.

**Rounds 12–18: from a hardened prototype to a contract (measure, then enforce).** The rounds above made
individual guarantees true; they did not yet answer *when is a run a run*. A pipeline could skip layers
and still print a verdict. So the engine was instrumented rather than argued with. Round 13 added an
**execution manifest** that records, per layer, `RAN` / `NOT_APPLICABLE` / `MISSING` — at first
record-only, deliberately not gating anything. Round 14 is the round worth keeping honest about: the
first measurement run, pointed at the round-12/13 code, **found three real instrumentation defects in
that very code** — `parse_finding` was silently dropping the fields that form the false-positive
denominator, the governor was counting all flags as coverage flags, and the source-grade coverage was
computed but never recorded — each now fixed and pinned by a regression test. Only *after* the
instrument was trustworthy was the minimum frozen: rounds 15–18 populated `REQUIRED_LAYERS` from a
growing measurement (5 classes, then a 10-run/8-class consolidation), and that consolidation **corrected
the engine against itself** — a 5-run sample had wrongly made `reasoner` required; two earlier runs
recovered their defects without it, so round 18 demoted it to optional. Round 17 caught a subtler
self-inflicted bug: the triage auto-adjudication was **overwriting an explicit `NOT_APPLICABLE`
justification** (external-auditor N/A *for independence*) with its own weaker "not selected by triage",
found by a 3-domain measurement run and fixed so a declaration always beats a deduction. With the minimum
measured and stable, round 18 finally switched on the **non-bypassable refusal**: an `INVALID` run is
forced to `INVALID_RUN`, overriding even a human `VALIDATED`, and the CLI exits non-zero. The order is
the ethic in miniature — *measure the minimum, correct yourself where the measurement contradicts you,
and only then let the gate bite* — because an unmeasured minimum would have made a valid run `INVALID`
(over-strict) or hidden a real gap. The consolidation table lives at
`MEASUREMENT_layer_contribution.md`; the contract and refusal are pinned in `tests/test_run_manifest.py`.

We report all of it here, rather than quietly patching, because a system whose entire value is
adversarial honesty must show the audits that caught it — including the one that caught the previous
audit's fix, the one that caught this section overclaiming, the different-vendor one that caught the
paper's headline over-claim and forced two closure guarantees from convention into code, and the
measurement runs that caught three defects in the very instrument built to measure the others.

## 10. Related work — where this sits among adversarial auditors and judge-reliability studies

Three lines of recent work bound this contribution, and the boundary is worth drawing precisely.

**The problem, measured (LLM-as-a-judge reliability vs. validity).** *Reliability without Validity*
([arXiv:2606.19544](https://arxiv.org/abs/2606.19544)) is the largest systematic evaluation of
LLM-as-a-judge to date — 21 judges, nine providers, ~541k judgments — and its central finding is the
one that motivates this whole paper: judges are **reliable without being valid**. Test–retest
consistency above 0.95 coexists with severe position bias; exact-match agreement, uncorrected for
chance, inflates apparent discrimination by 33–41 points of κ; rankings move by up to 14 positions
across benchmarks. That study *diagnoses* the disease empirically. This paper is a *mechanism* against
its most dangerous consequence — a judge that is stable and biased **certifying itself** — by making
self-certification cryptographically impossible and by forcing an explicit, measured account of what a
run actually did before it may close. Norman et al. do distill their findings into a *recommended*
"Minimum Viable Validation Protocol" (measure chance-corrected agreement, randomize position, and so on)
— but a recommendation is advisory; a judge can decline to follow it and certify itself anyway. Our
difference is in kind: we make the recommendation's *enforcement* structural — the pipeline refuses to
close when the account is incomplete. We cite them as the external empirical warrant for why non-closure
has to be enforced rather than assumed; we do not re-measure judge bias.

**The closest adversarial cousin (defect discovery).** *Refute-or-Promote*
([arXiv:2604.19049](https://arxiv.org/abs/2604.19049)) shares this system's core intuition — an
adversarial *kill-mandate* (defend/refute a candidate before promoting it) and a **Cross-Model Critic**
to catch correlated single-family blind spots — and demonstrates it at impressive scale (a 31-day
campaign, ~171 candidates, ~79% killed before disclosure, real CVEs and accepted ISO C++ defect
reports). The overlap is real and we claim no priority on the adversarial-kill or cross-model ideas.
The differences are the point of this paper. Refute-or-Promote optimizes **precision of discovery** with
a **human orchestrator** in the loop; its cross-model step *improves* reliability but nothing in the
pipeline *forbids* a confident close. This system optimizes **trustworthiness of closure**: the
orchestrator does not judge (code does), independence is credited only when an adapter attests a genuine
different vendor (not merely a second model prompted adversarially), closure requires a cryptographic
human signature, and a run that under-ran its measured minimum is **refused, non-bypassably**. Put
crudely: they build a better *finder*; we build a *finder that cannot lie about having finished*. The
two are complementary — a Refute-or-Promote front-end feeding an AAE-style closure contract is a natural
combination — but the guarantees are different in kind.

**The venue and the standard it wants.** [JUDGe @ NeurIPS 2026](https://judge2026.github.io/) frames
evaluator reliability and validity explicitly as a **systems** problem — "how does a judge's error
profile interact with what is upstream and downstream of it" — and its concrete community deliverable is
a **judge-deployment disclosure template** (provenance, deployment context, known failure modes, human
validation). This paper's execution manifest and A+B run-validity record are, in effect, a
*machine-checked instance* of exactly such a disclosure: for every run they emit which layers ran, which
were adjudicated inapplicable and why, what independence level was attested, and whether closure was
reached — and they refuse to close when that record is incomplete. We position the contribution there:
not a new judge, but a **protocol and a disclosure format that a judge cannot silently violate**.

Two clarifications of scope. We make **no detection-superiority claim** over any of the above; §6 is
explicitly a small-sample descriptive dissociation, not a recall result. And "adversarial" here is
narrower than adversarial-*robustness* work on prompt-injection attacks against judges — that literature
asks whether a judge can be *fooled from outside*; we ask whether a judge can be *stopped from certifying
itself from inside*.

## 11. Relation to the two theory papers

This is the **empirical/architectural companion** the theory papers lacked. *Managing epistemic
circularity* proves the survivor gate and non-closure in the C₃ quantale; here the same non-closure is a
`Stop` hook and a completion state machine you can run. *The engineering frontier* argues one
independence frontier (ρ); here a candidate second axis — **capability** — shows a *descriptive
dissociation* from it in a small sample (§6), and the first is instrumented rather than assumed. Nothing
in the published papers is retracted or corrected;
they are theoretically sound and honestly limited. A light Zenodo version-note on the engineering
frontier can point forward to the capability frontier developed here. The three papers together are one
object seen thrice: the algebra of the residue, the coordinate of the frontier, and the machine that
shows both are real because it runs.

---

*Revision v1.0.5 — post round-9…18 hardening. Rounds 9–11 enforced closure and made human-closure plus
vendor-independence cryptographic (`aae/attestation.py`); rounds 12–18 added the execution manifest,
measured `REQUIRED_LAYERS` over 10 runs / 8 classes, and switched on the non-bypassable A+B run-validity
refusal (§4, §9). Reframed around the trust protocol (§1); related work positions it against
Reliability-without-Validity, Refute-or-Promote, and the JUDGe @ NeurIPS 2026 agenda (§10). Companion
framing §11; self-audit trail §9, with its ledgers under `audits/`. Open items: cut a v1.0.5 tag at the
round-18 commit to match the artifact pin; the version-note on the engineering frontier.*
