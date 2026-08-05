# The audit engine, described as it runs: a reproducible adversarial-audit architecture where the discipline is code, not prompts

*Systems-and-benchmarks paper. Companion to two theory papers on the same engine
([Managing epistemic circularity](../managing-circularity/), [Graded commensurability is not a
quantale-enriched distributor](../commensurability/); Zenodo DOI 10.5281/zenodo.21288401). Those
papers build a mathematics after the fact and hang the system underneath it. This one goes the other
way: it describes what the machine actually does, draws the real graph of roles and gates, and states
an honest point about the technology — what is a language model, what is deterministic code, what runs
in CI. Its single advantage over the theory papers: every claim below maps to a file you can read or a
test you can run (the one exception, the blind re-adjudication of §6, is attested rather than public and
is flagged as such in §8), so it is falsifiable, from inside, without waiting for the external eye.*

**Artifact.** `github.com/eddo-cto/adversarial-audit-engine` (MIT), at tag `v1.0.2`. Four
reproducible benchmarks under `plugins/adversarial-audit-engine/benchmarks/`, each with a
`reproduce.py --strict` (pure standard library) checked in CI on `main` and every pull request,
across Python 3.10–3.13.

---

## 1. Introduction — why bottom-up, and why it is worth more here

The two published papers about this engine are *a-posteriori mathematical constructions*. One reads
the finished behaviour and shows it lands in a graded quantale C₃ with a survivor gate; the other reads
the same behaviour and shows the two "humility lemmas" are one quantity — the error-correlation ρ —
seen twice. Both are true, and both descend from a formalism.

That framing carries a cost the papers cannot pay off: a reader cannot tell, from the algebra, *how
much of the system is the algebra*. Is the quantale enforced, or narrated? Does "non-closure" live in a
proof, or in a line of code that refuses to print `VALIDATED`? The honest answer — it lives in code — is
more convincing than the algebra, and the theory papers never show it.

This paper supplies the missing description. It is deliberately not a formalism; it is the operating
manual read out loud, with the numbers the manual actually produces. Its contribution is threefold and
concrete. (i) It makes the method **reproducible by a stranger**: clone, run, watch the gates fire.
(ii) It converts every methodological claim into a **passing test**, so the discipline is auditable
without trusting the authors. (iii) It separates cleanly the part that is a language model — fallible,
non-deterministic — from the part that is ordinary Python — deterministic, boring, trustworthy — a
distinction the theory papers blur and every prospective user needs.

The empirical payoff (§6) is a result the theory papers do not have: the engine's behaviour is governed
by **two orthogonal frontiers**, and — this is the new finding — the two are **dissociated by the data**,
not merely asserted. One class of real defect is recovered by *no* model nature (a capability frontier);
a different class is recovered precisely by a *different* nature (an independence frontier); a third sits
inside both and is always caught.

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

This taxonomy is not decoration: §6 shows the engine's empirical boundary is drawn exactly along these
class lines. A non-local class with fewer than two cited sections is flagged by the integrity report,
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
| out-of-band human attestation present (operator environment, *not* the payload) | `VALIDATED` |
| reviewer is a genuinely different **vendor** (independence level 3) | `CROSS_MODEL_REVIEWED` — *"reliability improved — but NOT validated"* |
| reviewer is a same-vendor different model (level 2) | `INTRA_VENDOR_REVIEWED` — *"shared priors, not cross-vendor, not validated"* |
| no valid external identity | `EXTERNAL_REVIEW_PENDING` |

**Only a human returns `VALIDATED`, and only out of band.** The attestation is a secret the operator
supplies through a channel the payload does not touch (an environment token). The guarantee is relative
to a stated threat model: it holds for an operator who does not export the secret into the agent's
shell, and it moves forgery from a field the model authors by design to a variable it must deliberately
set. It is not a cryptographic barrier — see §7. Because the orchestrating model authors the payload, a
string beginning with `"human"` is explicitly *not* enough — this is the round-9 F-HUMAN fix. A
different-vendor reviewer raises independence to level 3 but still cannot validate ("a machine sharing
the ultimate limit"); a same-vendor model is level 2, not cross-vendor. A `Stop` hook then runs
`governor_check.py` **in the operator's environment** and, if it finds a `VALIDATED` lacking that
out-of-band attestation, **downgrades the ledger on disk** and records the correction. Non-closure is
not a posture here: it is checked in code at write time and re-checked at Stop time, both against the
same operator secret — one mechanism at two moments, not two independent mechanisms.

## 5. The honest point about the technology

What this is: an orchestration of **language-model sub-agents** (Sonnet for the hostile roles, Opus for
the governor; each with an effort budget, a turn cap, and write tools removed) wrapped around a
**deterministic core of ordinary Python** — standard library, no machine learning, ≈4,200 lines across
30 small modules. Intelligence and fallibility live in the LLM band; discipline and trust live in the
Python band. Keeping them apart is the entire design.

Where it is solid: the gates, the verdict state machine, the metrics, the dedup, and the governor's
deterministic check are pure functions with tests (145 passing); they behave identically every run, and
the four benchmarks reproduce to the digit in CI.

Where it is fragile, plainly: (i) the discovery band is a language model, so *which* candidate defects
surface varies run to run — the discipline bounds the false positives, not the recall variance; (ii)
real cross-vendor independence depends on an **adapter** (an MCP server or a script calling another
vendor's API) the operator must wire up — absent it the external-auditor is theatre, and the code says
so; (iii) the "5-layer" framing describes five roles, not five guarantees — the guarantees are the
three gates, fewer and humbler than any marketing.

## 6. What actually happens — two frontiers, dissociated by the data

The theory papers name **one** frontier: independence (ρ). Running the engine on real errors revealed a
**second, orthogonal** one, and the two turn out to be separable in the measurements — which is the
strongest evidence that they are genuinely two things and not one.

**Setup (benchmarks `real_errors`, `inter_nature`, `baselines`).** Seven real published papers that
later received a formal *Matters Arising* supply third-party ground truth: each has a known, formally
refuted defect. Seven cross-domain **decoys** test for false alarms. The same targets are run under
three different model "natures", and against the same strong model used *without* the engine's protocol.
Adjudication of whether a produced finding *lands* on the sealed target uses a strict rule — same
*locus* in the paper **and** same *mechanism* — and has been **re-adjudicated blind** by a fresh,
isolated instance (relabelled pairs, neutralised targets, no key, no class labels); it reproduced the
per-pair result **identically** to the coordinator on all 14 pairs (P landing 1/4, A landing 3/3, decoy
false-positives 0/7). The coordinator-bias confound is therefore dissolved; what remains un-blinded is
only closure, by construction.

**The dissociation.** Group the real targets by defect mechanism and ask which model natures recover
them:

| defect class | example | primary nature | across three natures | reading |
|---|---|:---:|:---:|---|
| **general-reasoning** | internal contradiction, definitional entailment (ORIG_03) | caught | caught by all | inside both frontiers — always caught |
| **external-data** | a claim resolvable only against an outside source (ORIG_01/02/06) | **0/3** | **monotone: A 0/3 ≤ B 2/3 ≤ C 3/3** | **independence** frontier — recovery *rises with nature-distance* (ρ<1) |
| **domain-re-derivation** | re-integrate the equations, recompute a physical quantity (ORIG_04/05/07) | 0/3 | **0/3 for every nature** | **capability** frontier — *no* nature recovers it |

The two frontiers fall out cleanly. The **capability** frontier is the class that **no** nature
recovers — and that a vanilla firehose of up to 155 findings *on that very target* also misses — because it requires *executing* a
domain re-derivation, which no text-only auditor does; it is a property of the *task*, orthogonal to how
many independent eyes you add. The **independence** frontier is the class that a **different** nature
*does* recover: this is `engineering-frontier`'s Proposition 2 turned from an argument into a
measurement — internal agreement cannot separate genuine from coordinated consensus, an external
(different-nature, ρ<1) draw can. That a single dataset separates "no nature helps" from "a different
nature helps" is exactly why the two frontiers are two.

**The honest sensitivity numbers.** On a single nature, real class-P recall is **1/4 (25%)** with
**0/7** decoy false-positives — the number the synthetic calibration (88% present-verifiable; see
`benchmarks/calibration`) overstated, and which we keep in view precisely because it is the honest one.
The 25% is not the product's accuracy; it is the calibration of a *general-reasoning* auditor on real
domain errors.

**What the discipline buys (baseline, `benchmarks/baselines`).** Against the same strong model run
*without* the protocol, discipline does **not** change *which* targets are caught (landing identical,
4/7, same targets) — it cuts the noise **~5×** (≈18 findings per paper vs ≈88, per-paper range
2.5×–8.4×) and declares a boundary the vanilla judge does not. A deterministic OSS baseline (statcheck)
lands 0/7: its class (APA-style NHST p-values) is disjoint from these defects. This is the literature's
"reliability without validity" grounded on real errors: the value is calibration — fewer false alarms
and a declared boundary — not a recall crown.

Put the frontiers together and the footprint is exact: the engine closes a defect **iff** it is
general-reasoning-reconstructible (inside the capability frontier) **and** you have supplied the right
independence (inside the independence frontier); everything else it routes to the human, by
construction, and it says which frontier it hit.

## 7. Honest limits

`n` is small throughout (single-digit target and decoy counts): this **circumscribes** the claims, it
does not certify them, and nothing here reaches significance. Matters Arising are *conclaimed* errors,
not a representative sample. The over-flagging ratio is a **proxy** for false positives, not a measured
false-positive rate, and it varies with the paper (reported with its range). Two targets carry declared
wrinkles: one external-data target is adjudicator-dependent (which is the ρ<1 phenomenon itself, not a
judgment error), and one re-derivation target was confounded by text extraction dropping the governing
equation (irrelevant to recall, since that class is missed regardless). And the whole apparatus, this
paper included, is a **survivor**: two same-nature adjudicators dissolve coordinator bias but stay at
independence level 1–2; no number reaches `VALIDATED` without the different-nature axis and, ultimately,
the external human eye. That is the engine's own thesis applied to itself.

Two closure guarantees are, as of this version, conventions rather than proofs, and we state them as
residue rather than let a reader discover them. Human closure requires a non-empty operator token whose
value is never verified: the guarantee holds against a model that authors the payload, not against one
that exports an environment variable into its own shell. And the reviewer's vendor is read from a
payload field rather than attested by the adapter that made the call, so independence level 3 is
*claimed*, not proven — a string of the form `vendor:model` with any unfamiliar vendor part is currently
sufficient. Both are one commit each and both are round-11 work; neither is load-bearing for the §6
measurements, which were produced under level 1–2 and are reported as such.

## 8. Reproducibility statement

Everything quantitative above recomputes from versioned, anonymized data with the standard library and
no install:

```bash
git clone --branch v1.0.2 https://github.com/eddo-cto/adversarial-audit-engine && cd adversarial-audit-engine
for b in calibration real_errors inter_nature baselines; do
  python3 plugins/adversarial-audit-engine/benchmarks/$b/reproduce.py --strict || echo "DIVERGED: $b"
done
python3 -m unittest discover -s plugins/adversarial-audit-engine/tests   # 145 tests
```

Each `reproduce.py --strict` exits non-zero on any divergence from its `claims.json`; each benchmark's
guard is verified non-vacuous by an automated perturbation test (`tests/test_benchmarks_guards.py` flips
one datum in each benchmark and requires `--strict` to fail). The one claim in this paper that is *not*
clone-and-run is the §6 blind re-adjudication: its materials are attested in a private sealed register
(a fresh instance reproduced the coordinator's result on all 14 pairs) rather than shipped, because
anonymization is deliberate — the public benchmarks carry only `(mechanism, class, landing, counts)`.
Paper identities (PMCIDs, DOIs, the sealed Matters-Arising targets) stay private; naming a paper beside
a "missed defect" adds nothing to any statistic and risks misreading. Red line: the engine flags, it
does not accuse.

## 9. The engine audited itself (round-9 hardening)

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

This is the paper's thesis surviving its own instrument. Before round 9, "the discipline is code" held
for the defense-gate and coverage-gate and quietly failed for closure — which was string convention. The
engine located that gap *in itself*. Closing it made the claim fully true for the sections-gate and for
vendor-awareness, and reduced human-closure forgery from a payload field to an operator secret whose
strength is the operator's own hygiene — a contraction of the attack surface, not its elimination. The
residue is stated in §7.
We report it here, rather than quietly patching, because a system whose entire value is adversarial
honesty must show the audit that caught it.

## 10. Relation to the two theory papers

This is the **empirical/architectural companion** the theory papers lacked. *Managing epistemic
circularity* proves the survivor gate and non-closure in the C₃ quantale; here the same non-closure is a
`Stop` hook and a completion state machine you can run. *The engineering frontier* argues one
independence frontier (ρ); here a second — **capability** — is dissociated from it by the data, and the
first is instrumented rather than assumed. Nothing in the published papers is retracted or corrected;
they are theoretically sound and honestly limited. A light Zenodo version-note on the engineering
frontier can point forward to the capability frontier developed here. The three papers together are one
object seen thrice: the algebra of the residue, the coordinate of the frontier, and the machine that
shows both are real because it runs.

---

*Draft v1 — for internal review before submission. Venue target: a systems / reproducibility track.
Author to confirm the code excerpts (§3–§4), the two-frontier table (§6), and the companion framing
(§9) before the version-note on the engineering frontier is filed.*
