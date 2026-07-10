# Managing epistemic circularity in self-referential evaluation
## The survivor gate, and how three scientific ledgers resolve indeterminacy

**Author:** Edoardo Gazzoni · independent researcher · GitHub: [eddo-cto](https://github.com/eddo-cto)
· ORCID: 0009-0004-2525-256X

*Working paper · unified draft (Parts I–IV) · July 2026*

**Companion paper.** Gazzoni, E. (2026). *Graded, asymmetric commensurability is not a quantale-enriched distributor: a transitivity obstruction, and a persistence-module alternative* — develops the C₃ quantale, the two negative results, and the interleaving distance this paper applies.

**Abstract.** When an evaluator shares the nature of what it evaluates and no external ground truth
is available — a model judging a model, as in *LLM-as-a-judge* evaluation; a verification procedure
auditing itself — evaluation is *self-referential*, and its circularity cannot be eliminated (Chang; the coordination problem;
data-technique circles). It can be *managed*. We propose (i) a procedure — the **Survivor Gate** — a
stratified adversarial architecture with hygienic meta-levels that guards both under- and
over-demolition, arrests its own meta-level regress by **declared non-closure**, and outputs a
*survivor* (a maximally-guarded residue) rather than a certification; and (ii) a **diachronic
account of reliability** for such survivors, built on **commensurability** and **plausibility** and
formalized inside **partial structures / partial truth** (da Costa, French, Bueno). The two parts
lock together: the survivor gate produces outputs honest about their limits, and only such outputs
can have their overlap with an independent line measured without that measurement being contaminated
by self-confirmation. We fix the theory's central term — *morphism* — as a **partial homomorphism**
whose variant (isomorphism / adjunction / lax) is an empirical question, and we specify the
experiment that discriminates it. On three independently-maintained reliability ledgers (Kepler KOI;
ClinVar/ACMG; NVD/CVE) we then test the account empirically, and report that **each measurement we specified overturned a
reading it was meant to support — including our own**: a proposed order-of-magnitude spread in
cross-domain contestedness dissolves once calibration is separated from judgement (≈23 % vs 19.8 %,
the same order); and the resolution of the indeterminate tier, which a within-gene facet control had
attributed to external adjudication alone, is corrected by a longitudinal test on the whole population
(169,218 variants born indeterminate): accumulated peer agreement **does** resolve k along a clean
dose–response (14 % → 49 % as independent submitters grow), while an external authority resolves it
faster still (53 %) — an empirical echo of the procedural arrest the theory argues for, now in its
truer form (the external eye is the most efficient resolver, not the only one). Throughout, the theory is applied to itself: this
paper is, by its own commitments, a **survivor**, not a validated result.

> **On method.** This draft is written from an *independent context* and adopts partial structures
> as a *proposed* foundation — offered by an external eye, to be checked against the engine and a
> human reader, not certified. That is the theory's own discipline: independence is imported, not
> manufactured from inside.

---

# Part I — The problem

An evaluation is **self-referential** when the evaluator shares the nature of the evaluated and there
is no independent external criterion to appeal to. Classical construct validity (Cronbach–Meehl)
validates a construct by correlating it with **other measures assumed independent** — the nomological
network. In the self-referential case this collapses: when evaluator and evaluated share a nature,
their measures share the same bias, and the correlation confirms nothing. The circularity is not a
bug to be fixed; it is a **proven, unavoidable feature** of measurement without an independent
criterion. An active recent literature imports construct-validity and measurement theory into AI
evaluation (Jacobs & Wallach 2021; Raji et al. 2021; *The Benchmarking Epistemology* 2025;
*Quantifying construct validity in LLM evaluations* 2026; *Measuring what Matters* 2025;
*Measurement to Meaning* 2025) and documents the circularity empirically — LLM-as-judge shows
*reliability without validity* (2026). But that work applies validity to **benchmarks** and validates
judges by **agreement metrics**; it names the circularity without giving a **structural, internal
account** of how the *architecture* of an evaluation could reduce it in the specific case where **no
independent criterion exists** and where reliability, if any, must **accrue over time**. That
specific case — self-referential, criterion-free, structural-and-diachronic — is the gap this paper
addresses. The engineering question is therefore not how to break
the circle but **how to manage it so that what the procedure certifies is as little contaminated by
self-confirmation as possible** — and, over time, how much standing a managed output can earn.

---

# Part II — The procedure: the Survivor Gate

## II.1 Three commitments

**A falsificationist, adversarial base.** The procedure never tries to confirm a claim. Every claim
is submitted to its own strongest attack and earns standing only by surviving attacks designed to
destroy it. Confirmation is unavailable in the self-referential case (it is exactly what circularity
forbids), so the procedure trades it for **survival under adversarial pressure**: the burden is on
the attack to fail, not on the claim to please.

**Stratified adversariality.** A single adversary has a single blind spot. The procedure stratifies
attack into layers, each covering a different angle — internal consistency; conformity to known
results; downstream propagation of consequences; deep/non-local causal structure; and a governing
layer that audits the audit. No layer is trusted alone; a claim must survive the conjunction.
Crucially — and this is a limit, not a boast — the layers **cannot cover every angle**. Angles
outside the shared vocabulary of all layers (cross-domain unknown-unknowns) escape any number of
layers that share the blind spot. **Coverage is asymptotic and never complete**; §II.3 turns this
limit into the reason the survivor gate, not certification, is the output.

**Hygienic meta-levels guarding both failure directions.** An adversarial procedure has two opposite
pathologies. *Under-demolition* — attacks too weak or too few, a claim that should fall let through;
guarded by stratification plus independence of attackers. *Over-demolition* — attacks too zealous, a
claim that should stand destroyed by an argument that proves too much or by the attacker's own bias;
unchecked adversariality collapses everything, as useless as confirming everything. The subtle
commitment: **the control that guards against over-demolition must itself be adversarial** — it
attacks the demolition, asking whether a destroying attack is sound or over-reaches, with the same
rigor. Over-demolition is caught not by mercy but by **attacking the attack**. (A lenient "defense
advocate" would reintroduce confirmation by the back door.)

![**Figure 1.** The survivor gate. A graded verdict in the quantale C₃ (⊥ < k < ⊤): a floor where one independent falsification suffices, an explicit abstention tier, and a survivor that is a maximally-guarded residue rather than a certification. The governor detects failure signatures but does not certify itself; the meta-level regress is arrested by *declared non-closure* — the residue passes to an external eye whose independence the architecture cannot manufacture from inside.](figure_paper/fig1_survivor_gate.png)


## II.2 The regress, and how it is arrested

If every control is adversarial, and the anti-over-demolition control is itself adversarial, then
that control needs a control to check *its* over-reach, and so on: the meta-levels regress without
end. We do **not** answer this with a final, self-certifying control — there is none, and claiming
one would be the exact self-confirmation the architecture exists to avoid. We arrest the regress by
**declared non-closure**: the top meta-level is built to *not* certify itself. It reports its
residual uncertainty, names what it could not rule out, and hands that residue to an **external eye**
— a different-nature auditor (a human, or an independent-domain search) whose independence the
architecture cannot manufacture from inside. The tower stops not because a final control closes it,
but because the top level admits it cannot close itself and says so. The arrest is **honest, not
arbitrary**: it converts an infinite regress into a single declared boundary — where internal
machinery ends and an external eye must begin. This is the load-bearing move: a procedure that
claimed to close its own regress would be certifying itself, worthless in the self-referential case;
a procedure that declares where it stops converts its central weakness into its one honest guarantee.

## II.3 The survivor gate

Because coverage is never complete and the regress is arrested by admission rather than closure, the
architecture cannot output "validated". It outputs the **survivor**: the claim, or the part of a
claim, that has withstood every layer of attack — including the attack on over-demolition — and whose
only remaining uncertainty is the declared residue handed outward. The survivor is not certified
true; it is the **maximally-guarded residue**: what is left when every available angle of destruction
has been tried and failed, and the procedure has been honest about the angles it could not try. In a
domain where circularity forbids confirmation, that residue is the strongest guarantee on offer.

| Output | Claims | Does NOT claim |
|---|---|---|
| **Falls** (accusation wins) | an attack succeeded; the claim does not stand | — |
| **Survivor** (contested, routed out) | withstood every internal angle; residue named, handed to an external eye | not "true", not "validated" — internal grounds cannot reach that |
| **Certified true** (unreachable) | — | the architecture never issues this from inside |

## II.4 Why this is not merely falsificationism

Plain falsificationism attacks claims and keeps the unfalsified. This architecture adds three things
it lacks: an **anti-over-demolition guard that is itself adversarial** (so zeal cannot masquerade as
rigor); an **explicit arrest of the meta-level regress by declared non-closure** (so the procedure
does not secretly certify itself); and a **survivor gate** that treats the output as a
handed-outward residue rather than a retained truth (so the external eye is structurally required,
not optional). Together these suit the self-referential case that plain falsificationism does not
address — where attacker and attacked share a nature and independence must be imported from outside.

---

# Part III — The diachronic reliability of survivors

## III.1 Why reliability must be diachronic

A survivor cannot be validated at a single instant against an independent criterion; there is none.
What remains is **accumulation over time**: a survivor can be repeatedly set against *independent
lines of inquiry* — different in nature, not sharing its bias — and its overlap with them tracked as
it grows or fails to. Reliability here is not a property an output has; it is a **trajectory** an
output earns. Two diachronic notions carry this: **commensurability** (a survivor's structured
overlap with an independent line) and **plausibility** (the standing that accrues as overlap
accumulates).

## III.2 The formal home: partial structures and quasi-truth

A **partial structure** represents an object by relations only partially defined: each relation is a
triple ⟨R⁺, R⁻, R?⟩ — tuples known to hold, known not to hold, and **undetermined**. A sentence is
**quasi-true** in a partial structure when it holds in *some* total structure extending it. This is
the epistemic situation of a survivor, and it gives each term a precise seat:

- A **survivor** and a **ground-truth line** are two partial structures over the same object. Neither
  is total; neither is "the truth to conform to" (circularity forbids it). They are **two partial
  coverings that may overlap** — the "two coexisting truths covering the object with overlap".
- **Commensurability** is the **overlap of their defined (R⁺) parts**, carried by a
  structure-preserving map between the two partial structures.
- The survivor's **declared residue** (II.2–II.3) is the **R?** component — the undetermined region
  handed outward. Part II's "residue to an external eye" gets a formal seat: not a defect, a typed
  part of the object.
- **Plausibility** is **quasi-truth relative to accumulated overlap**: a survivor is plausibly true
  to the degree it is quasi-true in partial structures partially mapping onto independent ground-truth
  lines. Two overlapping partial coverings do not prove a shared total truth; they make the survivor
  *plausibly* true in virtue of the overlap.

## III.3 "Morphism", resolved without overclaim

Commensurability is a **partial homomorphism** between partial structures (French–Ladyman;
da Costa–French): a map preserving structure **on the defined (R⁺) part**, leaving R? unconstrained.
This single object carries **both** intuitions that seemed to point to different structures: the
**backward resonance** (reciprocity) is the case where the map runs both ways on R⁺ — a **partial
isomorphism**; the **"at-least" of relations** (a guaranteed lower bound of preserved structure) is
the partial homomorphism's guarantee on R⁺, with R? the admitted remainder. "Morphism" was therefore
not a metaphor and not overreach — it was **imprecise for the weaker term**. The precise claim:
*commensurability is a partial homomorphism; its symmetry (partial iso), systematic asymmetry (a
partial adjunction), or degree-dependence (lax) is empirical, not chosen.* The experiment (Part IV)
does not decide *whether* it is a morphism; it discriminates *which variant*. What the data support
is the **direction** — a partial homomorphism with a **systematic asymmetric return** (adjunction),
never lax — **not a coefficient**: the numeric value is instrument-dependent and stays declared-open.

## III.4 The diachronic twist (the proposed contribution)

Partial-truth, as developed by da Costa and French, is **synchronic**: overlap at a time. The
contribution proposed here makes it **diachronic**:

- **Accumulated commensurability** C(t): the R⁺ overlap between a survivor and independent
  ground-truth lines as it grows across successive, nature-independent lines over time. Each new
  independent line either extends R⁺ or fails to.
- **Plausibility** as the **trajectory of quasi-truth**: a survivor's standing is the shape of C(t)
  — a guaranteed non-decreasing lower bound (monotone floor), a threshold, or a rise-and-fall.
  Plausibility is a **curve**, not a scalar, and its shape is an object of the experiment.
  **The monotone floor is not vacuous.** Although cumulative coverage cannot decrease (it is a union),
  its **marginal per-line contribution empirically plateaus to zero**, and the **per-line overlap is
  non-monotone** — so the floor is an *envelope* whose informative content is *where* it plateaus, not
  the tautological fact that a union grows. (Demonstrated on the data; see the marginal-contribution
  read-out in the bench.)

Reliability without ground truth is thereby reframed as **the diachronic accumulation of partial
overlap from nature-independent lines**, bounded below rather than certified. On novelty, honestly:
the synchronic partial-truth program is well established, and "partial structures over time" is
occupied in an adjacent domain (quasi-temporal structures in the histories approach to physics);
what this search did not find is the *specific* application — diachronic partial structures for
self-referential validity — which therefore appears **open, not virgin**.

## III.5 Positioning (what this does and does not claim)

- **Against Agrippa / Münchhausen** (regress / circle / dogmatic axiom; responses: foundationalism,
  coherentism, infinitism). This account does **not** solve the regress for *truth* — read as a
  fourth escape, it invites a fair rebuttal. Its claim is narrower and defensible: it breaks the
  **shared-bias circle** specifically, by importing **independence of nature** (the external eye)
  rather than a better foundation. Truth stays out of reach; *self-confirmation* is defeated.
- **Against Cronbach–Meehl.** It extends construct validity to the case the nomological network
  cannot handle — where validation measures are **not independent criteria** but **partial coverings
  of the same object** — redefining validity as accumulated partial-overlap rather than correlation
  with an independent criterion.
- **Against Dung's abstract argumentation — a conceded, narrowed claim.** The "attack the attack"
  control *is* Dung's defense/admissibility relation (Dung 1995), and two differences we earlier
  hoped to claim do **not** survive contact with the literature: (i) *diachrony does not distinguish
  us* — Timed Abstract Argumentation Frameworks (Cobo, Martínez & Simari 2010) and dynamic AF already
  make the framework evolve in time; (ii) *the self-referential pathologies are already handled* —
  SCC-recursive/CF2 semantics (Baroni, Giacomin & Guida 2005) and semi-stable semantics (Caminada
  2006) treat odd cycles and self-defeating arguments. **The one genuine difference that remains** is
  **declared non-closure**: the top level does not compute a closed verdict but hands the (possibly
  timed) grounded extension **outward, held open, with its residue R?**. This is a **posture on what
  the output means** — the grounded extension externalized rather than certified — **not a new
  semantics**. We therefore claim a contribution of *posture*, not of *mechanism*.
- **Against coalgebra and coalgebraic simulation.** The nearest formal neighbour to commensurability
  is not bisimulation but **coalgebraic simulation via lax relation lifting** (Hughes & Jacobs 2004),
  which is genuinely **directional and asymmetric** — like our backward < 1 — and where two-way
  similarity does not in general coincide with bisimilarity. It does **not** occupy our space for two
  structural reasons: (a) it presupposes a behaviour functor and its canonical setting is the **final
  coalgebra** (Aczel 1988; Aczel & Mendler 1989) — a ground-truth-like canonical object our
  self-referential, criterion-free case lacks; (b) it models behavioural equivalence between systems
  of the **same nature** over transitions, not criterion-free partial overlap of relational content
  (the R⁺/R⁻/R? triples). This yields a **positive** argument for partial structures over coalgebra:
  coalgebra is *total* on behaviour with a *final object* and cannot host the undetermined residue R?
  nor the absence of ground truth; partial structures carry R? natively. *(The one question a
  desk-review cannot close — whether a lax relation lifting over a category of partial structures
  **without** a final coalgebra would coincide with our construction — is handed to a category-theory
  expert as a precise open problem.)*
- **Against AGM / iterated belief revision.** The diachronic dynamics of epistemic states is studied
  by AGM (Alchourrón, Gärdenfors & Makinson 1985) and iterated revision (Darwiche & Pearl 1997). It
  does **not** occupy our space because it is revision **toward a criterion**: new information is
  accepted as true, under minimal change, converging to the evidence. The survivor is commensurability
  **without a criterion**, between peers, with **no convergence target** — the defining difference.
- **Within construct-validity-for-AI.** This paper is a **special case and extension** of the active
  program that imports measurement theory into AI evaluation (Jacobs & Wallach 2021; benchmarking
  epistemology 2025; quantifying construct validity in LLM evaluations 2026): that program treats
  benchmark validity and judge-agreement under an *available* criterion; here the criterion is
  **absent** (self-referential case), so validity is reconstructed structurally (survivor gate) and
  diachronically (partial-overlap accumulation) rather than as agreement with a criterion.

---

# Part IV — The experiment

The experiment discriminates, empirically, the variant of the commensurability partial-morphism
(partial iso / partial adjunction / lax) and the shape of the plausibility curve (monotone floor /
threshold / non-monotone), instead of fixing them by intuition. It has two stages; the first is
done, the second is specified here. A second, independent arm (IV.4) instantiates the accumulation thesis at high N on an external scientific ledger, with non-circular corroboration.

## IV.1 Stage 1 — instrument attestation (done)
A **deterministic** ruler discriminates the three partial-morphism variants on structures with
**known** overlap: constant backward/forward ratio 1 → partial isomorphism; constant <1 → partial
adjunction; degree-varying ratio → lax. A **forward-coverage attestation gate** refuses to classify
when, at full overlap, the forward coverage does not approach 1 (a blind ruler must not be allowed to
emit a structure verdict). Result: the ruler reads the structure of *known* regimes cleanly. This
proves the instrument can *read* structure — nothing about the real object yet.

## IV.2 Stage 2 — measurement on real, independent material (specified)
**Object.** Fix the variant of the *real* commensurability between engine survivors and independent
ground-truth lines, diachronically. The load-bearing risk is **construction-circularity**: if the
same agent builds the pairs and measures them, it imposes the structure it then "finds" — the very
circularity the theory studies. The design is built to prevent exactly that.

**Materials (independently constructed).**
- *Survivors*: pre-existing survivor-gate outputs (contested residues with declared limits) drawn
  from unrelated domains (building law, auctions, the AROMA case, the non-closure case). Not authored
  for the experiment.
- *Ground-truth lines*: independent lines of inquiry addressing the same object (published
  literature, primary sources), selected by a **pre-registered retrieval criterion** (e.g. top-k
  semantic retrieval, or domain-expert selection) — **not hand-picked to overlap**.
- *Time order*: the natural chronology in which independent lines accrue, or a controlled
  add-one-line-at-a-time accumulation, to build C(t).

**Measure (semantic, directional, deterministic).**
1. Represent each survivor and each ground-truth line as a set of **aspects** (claim/relation units).
2. Match aspects by **embeddings**: forward overlap = fraction of survivor aspects with a
   semantically matched ground-truth aspect (cosine ≥ τ); backward = the reverse. Forward/backward
   overlap are the R⁺ overlaps in each direction (partial homomorphism on the defined part).
3. The **matching threshold τ** is calibrated against a **human-validated** equivalence set. (This
   uses human/LLM judgment only for the *local* question "are these two aspects the same concept?" —
   a local semantic judgment — never for the *global* commensurability measure, which stays
   deterministic. The role split is the defense against the LLM-measures-LLM circularity.)

**Discrimination.**
- *Structure*: read the backward/forward **ratio across degrees**. Constant 1 → partial iso
  (symmetric backward resonance); constant <1 → partial adjunction (systematic asymmetric return);
  degree-varying → lax (degree-dependent preservation).
- *Plausibility*: C(t) = accumulated R⁺ overlap as independent lines are added over time. Monotone
  non-decreasing → guaranteed lower bound ("at-least"); jump → threshold; rise-and-fall →
  non-monotone.

**Controls (anti-construction-bias, pre-registered).**
- **Attestation**: known-equivalent paraphrase pairs must drive forward → ~1, or the ruler is not
  attested and no structure verdict is issued.
- **Negative control**: unrelated ground-truth lines must give ~0 overlap at every degree (flat
  floor) — if they don't, the matcher over-matches and the ruler is blind by saturation.
- **Blindness**: the agent selecting ground-truth lines and extracting aspects does not know the
  hypothesized structure; the measurer does not construct the pairs.
- **Pre-registration**: τ, the aspect-extraction procedure, the retrieval criterion, and the
  discrimination rule are fixed *before* the run.
- **Power**: ≥10 degrees, ≥30 pairs/degree, report intervals; the signal is the **shape**, not a point.

**Falsification (declared in advance).** The experiment fails to support the theory if: (a) overlap
never rises with true semantic overlap (ruler blind → not attested); (b) the ratio pattern is pure
noise across degrees (commensurability has no stable morphism-variant — "morphism" would then be
unsupported); (c) results flip across domains (the structure is a dataset artifact, not a property of
commensurability).

**Honest scope.** The zero-cost proxy (aspect extraction without validated embeddings) is weaker than
the full design; the prior in-session attempt failed precisely there (lexical matching collapsed the
signal to noise). A publishable result needs **real embeddings + human-validated aspect sets +
independently-built corpora**. Stage 1 already proves the ruler discriminates known structures; Stage
2 as specified is the measurement that fixes the real variant — and is honest that, if real semantic
overlap proves unmeasurable at accessible cost, *that itself* is the result: it delimits the
experiment the field must run.

---

## IV.3 First Stage-2-minus run (executed, robustified)
The deterministic ruler was run on **real material**: five survivors from an operating engine (the
theory paper itself; the AROMA over-demolition case; the non-closure/governor case; a feasibility
ceiling result; a cross-vendor Type-I gate) against an eleven-line pool of **independent literature**
(Tal/Chang; Agrippa/Klein; Cronbach–Meehl; Dung; da Costa–French; Jacobs–Wallach; reliability-without-
validity; Kapoor–Narayanan; the refutations-track program; ensemble/cross-vendor; phenomenology).
Robustified against the three fragilities of a single reading — one survivor, one accumulation order,
one annotator — via **400 order-permutations per survivor** and **annotator noise** (15% aspect drop,
300 replicates):

- **Structure = PARTIAL-ADJUNCTION**: 88% of order-permutations across the five survivors, 95% under
  annotator noise; backward (asymmetric-return) coefficient **0.46 ± 0.11**, stably below 1.
- **Plausibility = MONOTONE-FLOOR** (coverage of the survivor only grows as independent lines accrue).
- The single-run "lax" reading was diagnosed as an **order artifact**: the chosen order's backward
  trend falls inside the distribution of random-order trends, so order-invariantly the backward is
  ≈constant <1 (adjunction), not declining (lax).

Within the zero-cost regime this **fixes "morphism" on data**: a partial homomorphism with a
**systematic asymmetric return** (adjunction, coefficient ≈0.46) and a **growing lower bound** of
preservation — not iso, not lax. **Why still "minus":** aspects were author-tagged (construction-bias
residual, only perturbation-tested, not independently annotated), a single annotator, and no
embeddings. The full Stage 2 (IV.2) remains the publishable measurement; what IV.3 establishes is the
*direction*, robustly.

**A second run, with real embeddings.** The measurement was then repeated with **real in-browser
embeddings** (three sentence-transformer models as independent annotators; mechanical sentence
aspects; the ground-truth lines accumulated in their **true publication chronology**, 1955→2026,
so the accumulation order is no longer a choice), with an attestation gate that refuses a verdict
unless a paraphrase control drives forward-coverage to ~1 while an off-topic control stays ~0. Once
calibrated to attest (attestation coverage 1.00, negative control 0.00), the non-saturated
instruments converge with the hand-tagged run: on the least-saturated real model the survivors read
**partial-adjunction** (backward ≈0.63–0.83, systematically <1), **never lax** on any instrument,
and the plausibility is a growing lower bound (monotone-floor/threshold). Isomorphism appears only
as a **saturation artifact** of the loosest matcher (when the calibration lowers the threshold to
attest against a topically-homogeneous corpus, everything on-topic matches). Corrected for that
artifact, three independent instruments (hand tags; and real embeddings across models) agree on the
*direction*: a partial homomorphism with a **systematic asymmetric return** (adjunction), not
symmetric and not degree-dependent. The **coefficient** is instrument-dependent (≈0.46–0.83) and
remains the declared residue: a publishable value needs a topically-diverse corpus with graded
overlap, better embeddings, and human-validated aspect equivalence.

---

## IV.4 A second, independent arm: high-N instantiation on an external scientific ledger

The commensurability ruler (IV.1–IV.3) fixes the *morphism variant* of the survivor↔ground-truth
relation. A second arm tests the other half of the thesis — that reliability accumulates over
**independent domains**, with a **floor**, a **graded verdict**, and an **informative profile** —
on data built by a community with no connection to this work, at a scale the ruler cannot reach.
We read the Kepler Objects of Interest (KOI) catalogue of the NASA Exoplanet Archive through the
paper's lens. The claim is deliberately modest: not a result about exoplanets, but that an
independently-maintained, high-volume reliability ledger exhibits, on open data, the structure the
theory predicts — with a physically independent channel supplying the non-circular corroboration
that the internal reading, by construction, cannot.

**Route, and why this testbed.** A preliminary pilot on medieval-name etymology (n≈7, open corpora)
did not yield clean data, but earned the selection criteria then used: a domain contributes to
accumulation only if it is (i) independent by provenance, (ii) high in precision, and (iii)
informative about the ground truth. The exoplanet ledger was chosen because those three are
naturally and abundantly satisfied there, on open, deterministically queryable data — not for novelty.

**Mapping to C₃.** The KOI disposition falls in three classes that map onto the truth quantale
C₃ = {⊥ < k < ⊤}: FALSE POSITIVE (⊥) < CANDIDATE (k, indeterminate) < CONFIRMED (⊤), with
4 839 / 1 978 / 2 746 objects (N = 9 563 after discarding one corrupt row). Four **independent
false-positive diagnostics** — not-transit-like, stellar-eclipse, centroid-offset, ephemeris-match
— are the independent domains (each a distinct physical cross-check that can falsify the claim); the
continuous `koi_score` is the positive-accumulation axis toward ⊤. The diachronic axis is
instantiated, as the theory requires, as accumulation of independent lines, not calendar time.

**Internal instantiation (caveat first).** Diagnostics and disposition share a vetting pipeline, so
this reading is in part *definitional*: it shows the field's own reliability taxonomy realises the
paper's structure and quantifies the separation; it is not by itself non-circular. Stated so before
the numbers. Mean independent falsifications: 1.40 for ⊥ vs 0.004 for the rest (permutation test,
p < 0.001). The gate is a floor: P(⊥ | ≥1 independent falsification) = 99.6 %, and 99.4 % of ⊤ pass
all four checks — the dual, on the falsification side, of the join on the confirmation side. Among
survivors (zero falsifications) the residual ⊤-vs-k split is carried not by the diagnostics (all
zero) but by the positive axis (mean `koi_score` 0.04 / 0.80 / 0.96 across ⊥/k/⊤); the indeterminate
tier k spans the whole score range, so the final verdict conflates trajectories the profile separates
— the empirical shadow of the interleaving distance of the first paper.

**External, non-circular corroboration — the seven rescue cases are the result; the 97 % is not.**
The load-bearing test uses a channel physically independent of transit photometry: a mass from
radial velocity / dynamics (a Doppler/gravitational observable, different instruments and pipelines).
Of 290 Kepler planets with such an independent mass, 249 join by name to the KOI table.

We must be exact about what the aggregate concordance can and cannot carry, because the naive reading
over-claims. All 249 joined planets are already CONFIRMED in the transit taxonomy, and 242 (97.2 %)
also pass all four independent transit falsifications. But this 97.2 % is **conditioned on a doubly
selected sample**: radial-velocity mass is measured preferentially on already-promising targets, and
every joined object is already ⊤ in the transit channel — so the figure measures agreement *on the
positive class, among objects both channels chose to examine*, not agreement between two channels run
on a common, unselected population. The sample where the two channels could **disagree at scale** —
transit false positives — receives no radial-velocity follow-up and is structurally absent. The
97.2 % is therefore **not** "two independent channels agree at 97 %"; it is "where both channels
looked and the transit verdict was already positive, they concur." That is weak, selection-limited
evidence, and we no longer rest the non-circular claim on it.

**The non-circular weight rests on the seven discordant objects.** These are real planets, confirmed
by the physically independent radial-velocity channel, that the transit domain *alone* would have
down-graded (six carry the stellar-eclipse flag, one not-transit-like — physically unsurprising,
since genuine hot Jupiters can show a secondary eclipse the radial-velocity channel resolves). Here
the two channels genuinely **diverge**, and the independent channel **overrides** a single domain's
error. This is the one place selection does not manufacture the agreement: nothing about follow-up
selection forces the independent channel to *contradict* the transit flags, yet on these seven it
does, correctly. Structurally they are the thesis in miniature on real data — accumulation of
independent domains correcting the error of a single domain — and, unlike the 97.2 %, they are not an
artifact of the selected sample. Seven is a small, honest number; it is the real result of this arm,
and it is reported as such rather than inflated into an aggregate concordance the data cannot support.

![**Figure 2.** Arm 1 (Kepler KOI). *Left:* the reliability ledger's graded tiers, with mean `koi_score` rising monotonically across ⊥ / k / ⊤. *Right:* the external radial-velocity channel. All 249 joined planets are already ⊤ in transit and the follow-up is selection-limited, so the 242 concordances carry little weight; the seven divergences, where the physically independent channel *overrides* the transit verdict, are what selection cannot manufacture — and they carry the arm's non-circular content.](figure_paper/fig2_exoplanets.png)


**Independence diagnostic.** Accumulation is meaningful only over genuinely independent lines. The
six pairwise φ-coefficients among the four diagnostics are −0.23, +0.01, +0.06, +0.15, +0.10, +0.52;
five are near zero (the diagnostics fail for different reasons), while centroid-offset and
ephemeris-match are moderately correlated (+0.52) — reported, not smoothed. This exception is not
cosmetic: centroid-offset and ephemeris-match **share contamination-detection logic**, so for the
*diachronic independence thesis* the arm effectively accumulates **three-and-a-half independent
lines, not four**. For the **floor** (H1/H2) this does not bite — the gate needs only that *at least
one* line falsify, and redundancy between two lines does not lower that count — but for the claim of
accumulation over *independent* domains the +0.52 is a genuine crack, stated as such: one of the four
"independent" domains is partly an echo of another, and the independence the thesis rests on is
correspondingly weaker than a naive four-line reading would suggest.

**Limits, stated plainly.** (a) The internal reading is partly definitional; the non-circular weight
rests on the external channel and the independence diagnostic. (b) The external test is subject to
follow-up selection — radial-velocity mass is measured preferentially on promising targets, so it
establishes concordance on the positive class and the rescue cases, not a full error-rate curve
(false positives receive no such follow-up). (c) The join covered 249 of 290 independent-mass planets
(41 lost to name-format mismatch). None is hidden; each bounds the claim.

**What this arm establishes.** On open, high-volume data from an independent community, the paper's
abstract structure — graded C₃ verdict, survivor gate as a floor under independent falsification,
reliability profile beyond the final value — is realised. The non-circular corroboration is carried
**not by the aggregate concordance** (selection-limited, as shown) **but by the seven divergence
cases** where a physically independent channel overrides a single domain's error — accumulation of
independent domains correcting one domain, observed on real data. It is a feasibility demonstration
of the mechanism on a real reliability ledger, not a claim about exoplanet science, and its
non-circular content is deliberately modest: seven honest cases, not a manufactured 97 %. Every figure derives from ADQL queries against the NASA Exoplanet Archive TAP
service (endpoint `https://exoplanetarchive.ipac.caltech.edu/TAP/sync`, `format=csv`) — permanent,
re-runnable artifacts archived with the paper.

---

## IV.5 Three ledgers: what the measurements corrected

This section reports two findings, neither of which is the one it was designed to produce. The
measurements we specified to support our claims **falsified them**, and what replaced them is
narrower and, we think, more interesting. We state the arc plainly: (a) the recurrence of the graded
structure across fields is a *frame*, not a finding, and we say why; (b) the quantity we proposed as
the finding — that contestedness varies sharply by domain — did not survive its own decomposition;
(c) what did survive, from the control the objection demanded, is that the indeterminate tier is
resolved not by peer accumulation but by external adjudication.

**Why "the structure recurs" is the frame, not the finding.** A verdict tier {⊥ < k < ⊤} with an
explicit suspension class is close to a *functional necessity* for any mature classification system
operating under uncertainty: such a system must be able to withhold judgement, so it must have a
tier for "not yet decided", a floor for "refuted", and a top for "accepted". Finding that structure
in three ledgers therefore risks confirming only that all three are decision systems under
uncertainty — which was never in doubt. Worse, three ledgers *selected* for exhibiting the structure
would manufacture the regularity they then report. We accordingly (i) declare the selection
denominator below, and (ii) rest the contribution not on the recurrence but on a quantity that could
have come out otherwise.

**The proposed finding, and its falsification.** We proposed that contestedness — the rate at which
independent channels examining the same object disagree — is a domain-specific property spanning an
order of magnitude. The raw rates invited that reading:

| domain | ledger | raw disagreement | judgement-level | population |
|---|---|---|---|---|
| physics | Kepler KOI | near-concordance on positive class; 7 rescue cases | — | follow-up-selected |
| clinical genetics | ClinVar / ACMG | **19.8 %** (163,647 / 826,425) | 19.8 % | whole multi-submitted population |
| software security | NVD / CVE | 60 % (39/65, same CVSS version) | **≈23 %** (15/65) | double-scored sample |

The decomposition we ourselves specified dissolved the spread. Of the 39 security disagreements,
**24 are one severity grade apart** (calibration: two scorers agree the flaw is severe, differ by a
grade) and **15 are two or more** (judgement). The judgement-level rate is 15/65 ≈ 23 %, against
genetics' 19.8 %: **the same order.** The physics ledger cannot be placed beside them at all, since
its independent channel is follow-up-selected. So the order-of-magnitude spread was an artifact of
counting calibration as judgement, and we withdraw it. What remains is that contestedness is
*measurable* and, on the two ledgers measurable without selection, sits near **one object in five**.
This is the quantity that could have falsified an implicit assumption of the theory — that
accumulation over independent lines converges at a rate the theory need not specify — and on the two
ledgers where it can be measured without selection, that rate is **not** wildly domain-specific: it is
about one in five, twice. The theory's implicit assumption of uniform convergence is therefore neither
retired nor confirmed; it is, for the first time, *measured*, and found not to vary where we expected
it to. The form of the accumulation is the frame; its rate is the empirical content — and the
empirical content came back smaller than the hypothesis.

![**Figure 3.** The proposed contestedness spread, and its collapse. The raw security rate (60 %, hatched) appeared an order of magnitude above genetics. Decomposing the 39 disagreements shows 24 are one severity grade apart — calibration, not judgement. The judgement-level rate (23.1 %) sits beside the genetics baseline (19.8 %): the same order. The claim this arm was designed to establish is withdrawn, by the measurement the arm itself specified.](figure_paper/fig3_contestedness.png)
 The genuinely surprising result of this arm
lies elsewhere, in §IV.5.3: **what closes the indeterminate tier is not accumulation at all.**

### IV.5.1 Selection denominator (declared)

A recurrence claim without a denominator is three chosen confirmations. The inclusion criteria were
fixed *before* the ledgers were read, and were earned by a **failed pilot** (medieval-name etymology,
n ≈ 7, open corpora), which did not yield clean data and thereby fixed the criteria: a ledger enters
only if it is (i) independent by provenance, (ii) high in precision, (iii) informative about the
ground truth, and — added for IV.5 — (iv) exposes *independent channels* whose agreement can be read
off the record.

> **The denominator (declared).** Of the reliability ledgers weighed against (i)–(iv), *n_considered* = 9 were examined and *n_excluded* = 5 failed a criterion, each named with the criterion it failed: **medieval-name etymology** — (ii) precision (worn attested forms defeat the morphology channel); **species delimitation** (GBIF/BOLD) — (iii), the accepted-species ground truth is itself contested; **multi-method historical dating** — (iv), the independent dating channels are not readable from one queryable record; **Wikidata statement ranks** — (iv), rank is an editorial truth-status, not an accumulation of independent channels on the record; **GRADE / Cochrane evidence grading** — (iv), the evidence lives in prose, not a queryable independent-channel record. *n_included* = 3 (Kepler KOI, ClinVar, NVD). One further ledger — **gravitational-wave events** (GWOSC) — *qualifies* on (i)–(iv) but is not analysed here (small N, a few hundred events); it is named as a fourth candidate, not an exclusion. The denominator is small and the included set is a **minority** of those examined — reported so the recurrence reads as a declared, mostly-negative selection, not confirmations found by looking only where the structure was expected.

We flag this rather than quietly omit it: the contestedness finding survives an unfavourable
denominator (each rate is an internal measurement of its own ledger), whereas the recurrence claim
does not.

### IV.5.1b Falsifiability: mature ledgers that lack the structure

The recurrence is informative only if the structure is not universal — if one can point to mature reliability ledgers that *lack* {⊥ < k < ⊤} + suspension + independent channels. Three real ones do. **CODATA fundamental constants**: a recommended value with an uncertainty interval, continuous, with *no discrete suspension tier* — a mature reliability system whose verdict is not a graded {⊥,k,⊤} at all. **Certificate-revocation lists / spam blocklists**: binary in/out, single issuing authority, no k tier and no independent channels. **Registry-by-fiat** (ISO country codes, IANA assignments): normative assignment by a single authority, no independent-channel accumulation, no abstention. These show the structure is *contingent*, not a functional necessity of every reliability ledger: a system can be mature and withhold nothing, or decide by fiat with one voice. The recurrence of §IV.5.2 is therefore falsifiable — and, given the declared denominator, a modest positive claim rather than a tautology.

### IV.5.2 The three ledgers

**Physics — Kepler KOI (IV.4).** C₃ = FALSE POSITIVE / CANDIDATE (k) / CONFIRMED; four independent
transit falsifications; the non-circular weight carried by the seven rescue cases where a physically
independent channel overrides the transit verdict. Its independent channel is follow-up-selected, so
it yields concordance on the positive class, not a full error curve.

**Clinical genetics — ClinVar / ACMG.** We analyse only the *structure* of the reliability taxonomy;
no interpretation of any variant is made or implied. The review-status ordinal (0–4 "gold stars")
is an explicit axis of accumulated independent concordance; the verdict is a C₃ tier
(benign < *uncertain significance* = k < pathogenic); "conflicting classifications" is a recorded
disagreement class. Among the 826,425 variants with ≥ 2 independent submitters, **19.8 %** carry
recorded disagreement (163,647 conflicting). This supplies precisely what the exoplanet arm could
not: a **population-wide** disagreement measurement, because the second independent channel (a
different laboratory) is present *by construction* on every multiply-submitted variant, not by
selective follow-up. Agreement and disagreement are therefore measurable on both classes. Moreover the abstention tier resolves — and we tested *which* accumulation does it, twice. A
within-gene facet control first suggested peer accumulation was inert: across the whole population the
VUS (k) fraction falls 60.9 % → 44.6 % → 17.6 % over the review tiers, but holding the gene fixed the
1★→2★ peer step is flat (BRCA1 32.9 % → 35.6 %; MLH1 42.0 % → 41.2 %), so that decline looked like a
**population confound**, with only the expert-panel tier resolving k (VUS 0.6 %/2.7 % within
BRCA1/MLH1). *That reading was itself an aggregation artifact,* and the definitive test — longitudinal,
on a cohort fixed by construction — corrects it. Tracking the **169,218** variants born *uncertain
significance* with ≥ 3 dated submissions through their own submission histories (ClinVar's bulk
`submission_summary`, one dated classification per submission), peer accumulation **does** resolve k:
of variants that never reach an expert panel, **18.7 %** resolve to a definite tier, and the rate
climbs monotonically with the number of independent submitters — **14.0 %** (3–4 submitters) →
**28.5 %** (5–9) → **48.9 %** (10 +). Variants whose history includes an expert panel resolve at
**53.1 %**. So both mechanisms operate: an external authority resolves k most efficiently (≈ 3× the
peer-only rate), but accumulation of many independent peers also resolves it, and at high accumulation
(10 +) approaches the authority rate (48.9 % vs 53.1 %). Resolution is slow either way (mean ≈ 7.8
years). The within-gene flat step was a facet comparison across *different* variant populations at 1★
and 2★; the fixed-cohort longitudinal design removes that confound and reverses the negative reading.

*This reading must be discounted for a confound we have met before, and we name it by its name.* The
review tiers do not differ only in the *number* of concordant independent channels: they differ in
reviewer **type** (an expert panel is a curated authority, not merely more submitters), and — the
load-bearing objection — in the **population of variants that reaches each tier**. Variants escalated
to an expert panel are not a random sample; they are the clinically consequential ones, on which
evidence is most abundant. The falling VUS fraction may therefore measure *which variants arrive at
the higher tiers* rather than *accumulation resolving k*. **This is the same selection confound that
forced us to downgrade the 97.2 % concordance of arm 1** (§IV.4), where radial-velocity follow-up was
performed preferentially on promising targets: in both cases the second channel is present exactly
where the object was already easier to decide. We treated it the same way here — as a reason the
monotone VUS decline was *suggestive of* rather than *evidence for* accumulation resolving the
indeterminate tier — and then ran the clean test: the fixed-cohort longitudinal trajectory analysis of
§IV.5.2, which tracks the same variants over time and so removes exactly this selection confound. Its
verdict (peer accumulation resolves k along a dose–response, external adjudication faster still)
supersedes the provisional facet reading. *Further honest limits:* "conflicting"
is ClinVar's own aggregation rule; the star ordinal conflates *number* and *type* of reviewer.

**Software security — NVD / CVE (stress test; the weakest of the three).** Chosen because it is
maximally distant from natural science — an attempt to break the regularity, not to confirm it. The
`vulnStatus` ordinal (Analyzed / Modified / Deferred / **Rejected**) is a maturation-and-floor axis;
the independent channels are the NVD Primary and the CNA/CISA-ADP Secondary scores. On a sample of
174 CVEs, 65 carried both scores **at the same CVSS version** (v3.1) and disagreed on severity in 39 (≈ 60 %); the any-version figure (24/43 ≈ 56 %) is essentially identical, so the disagreement is **not** a version artifact.

*This figure carries the least weight of the three, for reasons we state rather than bury.* (a) n = 65
double-scored CVEs (from a 174-CVE sample) is small; the interval around 60 % is wide, and this is a
first estimate, not a settled rate. (b) *Resolved.* The version confound is ruled out: restricting to
a single CVSS version (v3.1) leaves the rate essentially unchanged — 39/65 ≈ 60 % same-version against
24/43 ≈ 56 % any-version — so the disagreement is **not** an artifact of comparing v3.1 against v4.0.
(c) *Resolved, decomposed.* Of the 39 disagreements, 24 (61.5 %) are one grade apart (e.g. HIGH vs
MEDIUM) and 15 (38.5 %) span two or more grades (14 of them CRITICAL vs MEDIUM). The majority is
therefore **disagreement of calibration**; but a substantial minority — 15/65 ≈ 23 % of double-scored
CVEs — is **disagreement of judgement** (≥ 2 grades). At the judgement level the security rate
(≈ 23 %) is on a par with the genetics ledger (19.8 %), not far above it. The raw 60 % overstated the
endpoint: the contestedness spread across ledgers is real but flatter than the raw figure suggested,
and NVD now bounds both its direction and its judgement-level endpoint.

We therefore do **not** claim "in security, independent evaluators disagree in the majority of cases".
We claim only that the security ledger shows disagreement of a **different order** from the genetics
ledger, that this order is not a version artifact, and that its exact magnitude awaits the
adjacency decomposition. The direction of the spread does not depend on that decomposition; its
endpoint does.

### IV.5.3 What this establishes, and what it does not

Both open measurements of §IV.5.2 have now been made, and both **corrected the claim they were meant
to support**. We report the correction rather than the claim.

**The contestedness spread largely collapses under decomposition.** The raw security rate (≈60 %)
suggested an order-of-magnitude spread against genetics (19.8 %). Decomposing the 39 disagreements
into calibration (one severity grade apart) and judgement (two or more) gives 24 and 15 respectively:
the **judgement-level** disagreement is 15/65 ≈ **23 %**, against the genetics ledger's 19.8 % — the
same order, not a different one. Most of the apparent security contestedness was two scorers agreeing
that a vulnerability is severe and differing by one grade. **We therefore withdraw the claim that
contestedness varies by an order of magnitude between mature ledgers.** What survives is weaker and
must be stated as such: contestedness is *measurable* (three ledgers, three internal rates, none
depending on how the ledgers were selected); the two ledgers with unselected, population-wide
measurement land at 19.8 % and ≈23 %, i.e. roughly one object in five contested by independent
channels examining it; and the physics ledger cannot be compared to them because its independent
channel is follow-up-selected. A spread may exist; these data do not establish it. This is the
falsification of our own IV.5 headline by the measurement we ourselves specified — recorded, not
buried.

**Both accumulation and external adjudication resolve the indeterminate tier — the longitudinal test corrects our earlier reading.**
The population-wide VUS decline (60.9 % → 44.6 % → 17.6 %) and a within-gene facet control together
first suggested a clean dichotomy: peer accumulation inert (flat 1★→2★ within BRCA1 32.9 % → 35.6 %
and MLH1 42.0 % → 41.2 %), only an expert panel resolving k (VUS to 0.6 % / 2.7 %, a factor of 15–60).
The longitudinal measurement on the whole population (§IV.5.2) shows that dichotomy was too strong. On
the 169,218 variants born k, tracked through their own dated submission histories, peer accumulation
resolves k along a monotone dose–response (14.0 % → 28.5 % → 48.9 % as independent submitters grow),
while trajectories that reach an expert panel resolve at 53.1 %. The external adjudicator is more
*efficient* — roughly three times the peer-only base rate — but it is not the *only* resolver, and at
high peer accumulation the two rates converge (48.9 % vs 53.1 %).

This both supports Part III's accumulation thesis and preserves Part II's external-eye thesis in a
weaker, truer form: the residue is resolved **fastest** by an eye of a different standing, not resolved
**only** by one. That is still the structure Part II argues for on procedural grounds — the meta-level
regress is arrested by handing the residue to an external eye whose independence the architecture
cannot manufacture from inside (§II.2) — but the empirical arrest is a matter of *efficiency*, not of
exclusivity. The earlier within-gene reading was a facet comparison across different variant
populations at 1★ and 2★; the fixed-cohort longitudinal design removes that confound. We record the
reversal as we recorded the claim. Honest limits: "resolved" is a proxy (majority of the three most
recent dated submissions, not ClinVar's official aggregate); expert-panel trajectories are a selected
subset, so 53.1 % is a flag, not a causal estimate; and the dose–response may partly reflect variant
tractability, though the fixed-VUS-start cohort controls the origin. *One further confound deserves naming in its sharpest form, and we have now run the measurement that
answers it: submitter count might be a **proxy for time in the system** rather than a cause of
resolution.* Variants that accumulate ten or more independent submitters have, plausibly, also been in
ClinVar longer, and mean time-to-resolution among peer-only trajectories is 7.8 years — long enough
that exposure duration could carry the effect the submitter count appears to carry. The fixed-VUS-start
cohort equalises the *origin* but not the *elapsed time*, so we stratified the dose–response by
years-in-system (first dated submission to the 2026 snapshot). The submitter-count effect **survives
inside every exposure stratum**:

| years in system | 3–4 submitters | 5–9 submitters | 10 + submitters |
|---|---|---|---|
| 0–2  | 6.4 % (n=10,493)  | 16.3 % (n=589)    | 50.0 % (n=2)     |
| 3–5  | 6.3 % (n=46,654)  | 12.8 % (n=8,508)  | 25.4 % (n=177)   |
| 6–9  | 19.6 % (n=51,079) | 29.5 % (n=20,283) | 35.7 % (n=1,963) |
| 10 + | 27.0 % (n=12,119) | 39.7 % (n=10,877) | 58.2 % (n=3,265) |

At equal exposure, more independent channels still resolve more — monotonically, in each of the four
age bands where the cells are populated (the 0–2 × 10+ cell is n=2 and carries no weight). Time also
matters over the longer run (resolution rises down the columns from the 6–9 band onward); but the
accumulation effect is present *within* fixed time, so submitter count was **not** merely reading the
clock.

The table contains a sharper argument than the stratification was designed to make, and we state it
because it is the cleanest disconfirmation of the time hypothesis available in these data. *Between the
0–2 and 3–5 year bands, elapsed time does nothing:* at 3–4 submitters the resolution rate goes 6.4 % →
6.3 % (n = 10,493 and 46,654) — flat, marginally negative, on large cells. Three additional years in
the system, holding channels fixed, buy no resolution at all. Yet inside that same 3–5 year band, where
the clock has demonstrably stopped contributing, accumulation still lifts resolution from 6.3 % to
12.8 % to 25.4 %, a fourfold rise. **Where time does nothing, accumulation does everything.** An
exposure-driven account has no way to produce that pattern: it predicts the rise down the column, not
the rise across a row in which the column is flat. The confound is not merely controlled for; it is
falsified on its own ground.

![**Figure 4.** Arm 2 (ClinVar), the decisive measurement. *Left:* resolution of the indeterminate tier among 166,009 peer-only variants born *uncertain significance*, stratified by exposure. Within every populated exposure band, more independent channels resolve more. In the shaded band the clock is flat — three extra years at fixed channel count buy nothing (6.4 % → 6.3 %, n = 10,493 and 46,654) — yet accumulation still lifts resolution fourfold inside it. An exposure-driven account cannot produce a rise across a row whose column is flat. *Right:* both mechanisms resolve k. External adjudication is roughly three times the peer base rate, but only four points above heavily-accumulated peers: the external eye is the *faster* resolver, not the *only* one.](figure_paper/fig4_stratified.png)


This closes the named confound in the direction that supports Part III: accumulation does causal work,
as far as an observational stratification can show. Residual limits stay honest — stratification is not
randomisation, and variant tractability may still correlate with submitter count inside a stratum — but
the specific "it is only elapsed time" alternative is falsified by the table.

**Establishes.** That contestedness is a measurable, internally-comparable property of a reliability
ledger; that on the two ledgers measurable without follow-up selection it stands near one in five;
and that, on the one ledger where the two mechanisms can be separated on a fixed cohort, **both**
resolve the indeterminate tier — peer accumulation along a monotone dose–response (14.0 % → 28.5 % →
48.9 %), external adjudication at ≈53.1 %, i.e. roughly three times the peer base rate but only
4 points above heavily-accumulated peers. The external eye is the *faster* resolver, not the *only*
one.

**Does not establish.** That contestedness varies substantially across domains (withdrawn above).
That the C₃-plus-suspension structure is a *trans-domain regularity* rather than a functional
necessity of decision systems under uncertainty — though §IV.5.1's mostly-negative denominator
(3 included of 9 examined) and §IV.5.1b's mature counter-examples (CODATA, blocklists,
registry-by-fiat) make the recurrence a **modest, contingent, falsifiable** claim rather than a
manufactured one. That external adjudication is *necessary* to resolve k: the longitudinal population test
(169,218 variants born k) shows peer accumulation also resolves it — up to 48.9 % at high submitter
counts — so the external eye is the *most efficient* resolver, not the sole one.

All figures derive from open, re-runnable queries (NASA TAP; NCBI eutils; NVD REST API; ClinVar UI
facets and the ClinVar bulk `submission_summary` release); no LLM judgement enters any score.

All figures derive from open, re-runnable queries (NASA TAP; NCBI eutils; NVD REST API); no LLM
judgement enters any score.

# Status (the theory applied to itself)

This paper is, by its own commitments, a **survivor**, not a validated result. It has withstood, in
independent review, the over-demolition of "morphism" (resolved as partial homomorphism, qualified
and empirically fixable) and the regress objection (arrested by declared non-closure). Its
**declared residue**, handed to an external eye (the engine on a separate context, and the human):
*is partial structures the correct formal home, or does it miss the diachrony it is asked to carry?
is diachronic partial-truth genuinely virgin, or already occupied in an adjacent literature this
search did not reach? does Stage 2 succeed, or does real semantic overlap prove unmeasurable at
accessible cost — which would itself delimit the experiment?* *And on the second arm (IV.4): the internal exoplanet reading is descriptive (shared pipeline) — does the external radial-velocity corroboration, bounded by follow-up selection, carry the non-circular weight the theory needs, or must an unbiased external channel be found?* These are not hidden; they are the R?
this paper declares. *And on the third arm (IV.5): both measurements we specified **falsified the
claims they were meant to support**, and we report the falsification as the result. The contestedness
spread — proposed as this arm's finding — **is withdrawn**: decomposing the security disagreements
into calibration and judgement leaves a judgement-level rate (15/65 ≈ 23 %) on a par with genetics
(19.8 %), so the order-of-magnitude spread was an artifact of counting one-grade calibration
mismatches as judgement. What survives is only that contestedness is *measurable*, and sits near one
in five on the two ledgers measurable without selection. Meanwhile the
recurrence of the C₃-plus-suspension structure remains a **modest, contingent** claim — the selection
denominator is declared (§IV.5.1: 3 included of 9 examined, a minority) and §IV.5.1b names mature
ledgers that lack the structure (CODATA, blocklists, registry-by-fiat), so the recurrence is
falsifiable rather than tautological. The two measurements, in detail. **(a) The NVD endpoint — closed.**
The version confound is resolved (v3.1: 39/65 ≈ 60 % ≈ any-version 56 %), and the 39 disagreements are
now decomposed: 24 one-grade (calibration), 15 two-or-more-grade (judgement). The judgement-level rate
(15/65 ≈ 23 %) is on a par with genetics (19.8 %); the raw 60 % overstated the endpoint, which is now
measured. **(b) ClinVar's resolving k — now tested longitudinally, N4 closed.** A within-gene facet control first
suggested the peer step (1★→2★) was flat (BRCA1 32.9 %→35.6 %; MLH1 42.0 %→41.2 %) and that only the
expert panel resolved k (VUS 0.6 %/2.7 %). The longitudinal test we had deferred is now run on the
**whole population**: tracking 169,218 variants born *uncertain significance* through their dated
submission histories (ClinVar's bulk `submission_summary`), peer-only accumulation resolves k at
18.7 %, rising monotonically 14.0 %→28.5 %→48.9 % with the number of independent submitters, while
trajectories that reach an expert panel resolve at 53.1 %. **Both** mechanisms resolve k: external
adjudication most efficiently (≈3×), peer accumulation also, converging on the authority rate at high
N. This corrects — and reverses — the earlier within-gene reading (a facet comparison across different
variant populations), and it closes N4 **as a mechanism-separation on a fixed cohort**, now hardened against the sharpest
confound: "resolved" is a proxy (majority of the three most recent dated submissions, not ClinVar's
official aggregate) and expert-panel trajectories are a selected subset, so 53.1 % is a flag, not a
causal estimate; but the objection that **submitter count is merely a proxy for time in the system**
(mean peer-only time-to-resolution 7.8 years) has been tested and rejected — stratifying the
dose–response by years-in-system, the submitter-count effect survives inside every exposure band
(6.3 %→12.8 %→25.4 % at 3–5 years; 27.0 %→39.7 %→58.2 % at 10+), and, decisively, *between* the 0–2 and
3–5 year bands elapsed time contributes nothing at fixed channel count (6.4 % → 6.3 %, n = 10,493 and
46,654) while accumulation inside that same band still quadruples resolution. Where the clock is flat
the accumulation effect persists undiminished: an exposure-driven account cannot generate that pattern,
so the confound is falsified rather than merely controlled.
(e.g. at 6–9 years: 19.6 % → 29.5 % → 35.7 %; at 10+ years: 27.0 % → 39.7 % → 58.2 %). At equal
exposure, more independent channels still resolve more, so accumulation does causal work as far as an
observational stratification can show — not merely elapsed time. What remains is the ordinary limit of
any stratified control (it is not randomisation; tractability may still correlate within a stratum),
stated because a survivor that hid it would not be one.* These are not hidden; they are the R?

---

## Nearest neighbour: descriptive diagnosis versus normative procedure

The closest recent work is **Corral** (Ríos-García, Alampara, Gupta *et al.*, 2026), which annotates
the reasoning traces of AI research agents as graphs of epistemic operations and measures whether
those traces exhibit Popperian falsification, refutation-driven belief revision, and convergent
multi-test evidence. Across 25,000+ traces it finds evidence *ignored* in 68 % of cases,
refutation-driven revision in 26 %, and **convergent multi-test evidence in only 7 %**.

We take Corral to be complementary rather than competing, and the distinction is worth stating
plainly. Corral is **descriptive**: it diagnoses, at scale, what agents in fact do. The present work
is **normative, formal, and empirical**: it proposes a procedure for managing circularity *where no
external criterion exists*, formalises the resulting notion of reliability, and asks how mature human
reliability ledgers manage the same predicament. The two meet at a single point, and it is the point
of this paper: Corral's rare "convergent multi-test evidence" *is* accumulation over independent
lines, measured as almost absent in current agents. Their finding is, to our knowledge, the strongest
external evidence that the mechanism analysed here is both load-bearing and scarce.

One further observation, offered without irony. Corral annotates its traces **using a language model**
and validates that annotation against **expert human annotators**, reporting 95.7 % human–model
agreement. That design is an instance of precisely the self-referential evaluation this paper is
about, closed exactly as §II.2 argues it must be: not by a further control of the same nature, but by
an external eye of a different one. We read this as corroboration of the procedural thesis, arrived at
independently and without reference to it.

The gap this paper occupies is stated most directly by Thais *et al.* (2026): current AI-for-science
work "conflates predictive accuracy with epistemic warrant and lacks operational instruments for
assessing whether claims are justified in the philosophical sense." Corral supplies a *diagnostic*
instrument. We attempt a *constructive* one — a procedure, a formal account of what it produces, and
three empirical tests of whether mature ledgers behave as the account predicts. Neither replaces the
other.

# Declarations

**Use of AI in the research and in the writing.** This work was produced with substantial use of a
large language model, deployed as an **adversarial instrument** rather than a generative one: to
re-derive the theorems from independently written code, to attack the author's own claims, to specify
the measurements reported in Part IV, and to report the results when those measurements falsified the
claims they were designed to support (four times; §IV.4–§IV.5). The model wrote no scoring code whose
output was accepted unverified, and **no LLM judgement enters any figure or statistic in this paper**.
The author is solely responsible for all claims, errors, and omissions. We note that the theory
advanced here bears directly on this disclosure: an evaluation procedure whose author declined to
declare that its instrument shares the nature of its object would be a poor advertisement for its own
thesis.

**Data availability.** All data are public and all analyses are re-runnable. The NASA Exoplanet
Archive (operated by Caltech under contract with NASA) is queried through the open TAP endpoint;
NCBI ClinVar is accessed through `eutils` and the public bulk release `submission_summary.txt.gz`;
the NIST National Vulnerability Database is accessed through the open REST API 2.0. We gratefully
acknowledge these three archives and the communities that maintain them; each is cited in the
references and should be cited independently by anyone re-using these analyses. Queries, scripts,
raw outputs, pre-registrations, and negative results are in the repository.

**Restriction on the use of ClinVar.** ClinVar is analysed **only** for the structure of its
reliability taxonomy — who classified, at what review level, and when. No clinical interpretation of
any variant is made, implied, or should be inferred from this work.

**Competing interests.** The author declares no competing interests.

**Funding.** This research received no external funding.

# Code, data, and the adversarial engine

**The engine.** The stratified adversarial audit procedure of Part II is implemented as an
open-source engine — a five-layer adversarial hive (destruens, construens, generative, deep-causal,
meta-epistemic governor) over a deterministic, dependency-free Python core that enforces the
discipline *in code*: the verdict state machine, the defence gate, per-dimension coverage, dedup,
metrics, and the governor's self-limit. By construction the core **never** reports `VALIDATED` on
internal grounds. Its independence ladder makes the thesis of §II.2 operational: a different role on
the same model yields self-falsification, a different vendor yields `CROSS_MODEL_REVIEWED` — and only
a **human expert** can return `VALIDATED`.

> **`https://github.com/eddo-cto/adversarial-audit-engine`** — MIT licence · release **v0.10.1**
> (July 2026) · Python standard library only.

Two components bear directly on Part II. A deterministic **grounding gate** permits a finding to
condemn only on a quote that exists verbatim in the source, so no fabricated or paraphrased quotation
can demolish an artefact; its guarantee (existence, recall-robustness) and its declared limit
(out-of-context quotation, an irreducibly semantic residue) are stated rather than papered over. And
**negation spectrometry** turns the over-demolition guard from an aspiration into a bounded number:
each auditor is calibrated on a control battery of valid and broken artefacts, yielding a measured
false-demolition rate, power, and an assumption-free residual Type-I error that captures the
shared-blind-spot correlation an independence bound would ignore. The engine, in other words, measures
its own Type-I error and refuses to certify itself — the two commitments this paper argues for.

**Replication package for Part IV.** Every figure derives from open endpoints and deterministic
scripts, with **no LLM judgement anywhere in the scoring path**. The package below — scripts, ADQL and
REST queries, raw outputs, the frozen pre-registration of arm 1, the failed pilot that fixed the
inclusion criteria of §IV.5.1, and every negative result — is distributed with this paper and
deposited, with a permanent DOI, on Zenodo (concept DOI 10.5281/zenodo.21288401, resolving to the latest version). It is included in the engine
repository under `papers/managing-circularity/`.

| arm | archive | endpoint | script |
|---|---|---|---|
| 1 — physics | NASA Exoplanet Archive | TAP `sync` (ADQL, open) | `run_esopianeti.py`, `QUERIES_TAP_riproducibili.md` |
| 2 — genetics | NCBI ClinVar | `eutils` + bulk `submission_summary.txt.gz` | `n4_longitudinale.awk`, `n4_stratificato.awk` |
| 3 — security | NIST NVD | REST API 2.0 (open) | `run_nvd.py` |
| figures | — | — | `make_figures.py` |

**Data use.** ClinVar is analysed **only** for the structure of its reliability taxonomy — who
classified, at what review level, when. No clinical interpretation of any variant is made, implied, or
should be inferred from this work.

# References

**Nearest neighbour and the stated gap.**
- Ríos-García, A. F., Alampara, N., Gupta, A., *et al.* (2026). *AI scientists produce results without
  reasoning scientifically.* arXiv:2604.18805. [I]
- Thais, S., *et al.* (2026). *AI for Science Needs Scientific Alignment.* PhilSci-Archive:28744. [I]

**Archives (please cite independently if re-using these analyses).**
- NASA Exoplanet Archive, Kepler Objects of Interest (cumulative table). Operated by the California
  Institute of Technology under contract with NASA. TAP service, accessed July 2026.
- Landrum, M. J., *et al.* ClinVar. National Center for Biotechnology Information, U.S. National
  Library of Medicine. `eutils` and `submission_summary` release, accessed July 2026.
- National Vulnerability Database. National Institute of Standards and Technology, U.S. Department of
  Commerce. REST API 2.0, accessed July 2026.

*Cited by level: **[I]** primary source engaged; **[II]** the source it builds on; **[n]** the
historical root. See the companion gap-closure note for the citation-lineage analysis.*

**Partial structures / quasi-truth.**
[I] da Costa, N. C. A., & French, S. (2003). *Science and Partial Truth: A Unitary Approach to Models
and Scientific Reasoning*. Oxford University Press.
[II] French, S., & Ladyman, J. (1999). Reinflating the semantic approach. *International Studies in the
Philosophy of Science*, 13(2), 103–121.
[n] Mikenberg, I., da Costa, N. C. A., & Chuaqui, R. (1986). Pragmatic truth and approximation to
truth. *The Journal of Symbolic Logic*, 51(1), 201–221.

**Coalgebra / simulation.**
[I] Hughes, J., & Jacobs, B. (2004). Simulations in coalgebra. *Theoretical Computer Science*,
327(1–2), 71–108.
[II] Aczel, P., & Mendler, N. (1989). A final coalgebra theorem. In *Category Theory and Computer
Science*, LNCS 389, 357–365. Springer.
[n] Aczel, P. (1988). *Non-Well-Founded Sets*. CSLI Lecture Notes 14. Stanford: CSLI.

**Argumentation frameworks.**
[I] Dung, P. M. (1995). On the acceptability of arguments and its fundamental role in nonmonotonic
reasoning, logic programming and n-person games. *Artificial Intelligence*, 77(2), 321–357.
[I] Baroni, P., Giacomin, M., & Guida, G. (2005). SCC-recursiveness: A general schema for argumentation
semantics. *Artificial Intelligence*, 168(1–2), 162–210.
[I] Caminada, M. (2006). Semi-stable semantics. In *COMMA 2006*, 121–130. IOS Press.
[I] Cobo, M. L., Martínez, D. C., & Simari, G. R. (2010). On admissibility in timed abstract
argumentation frameworks. In *ECAI 2010*, 1007–1008. IOS Press.

**Belief revision.**
[I] Darwiche, A., & Pearl, J. (1997). On the logic of iterated belief revision. *Artificial
Intelligence*, 89(1–2), 1–29.
[II] Alchourrón, C. E., Gärdenfors, P., & Makinson, D. (1985). On the logic of theory change: Partial
meet contraction and revision functions. *The Journal of Symbolic Logic*, 50(2), 510–530.

**Construct validity / measurement.**
[n] Cronbach, L. J., & Meehl, P. E. (1955). Construct validity in psychological tests. *Psychological
Bulletin*, 52(4), 281–302.
[II] Jacobs, A. Z., & Wallach, H. (2021). Measurement and Fairness. In *FAccT '21*, 375–385. ACM.
[I] Raji, I. D., Bender, E. M., Paullada, A., Denton, E., & Hanna, A. (2021). AI and the Everything in
the Whole Wide World Benchmark. *NeurIPS Datasets & Benchmarks Track*.
[I] *The Benchmarking Epistemology: Construct Validity for Evaluating ML Models* (2025). arXiv:2510.23191.
[I] *Quantifying construct validity in large language model evaluations* (2026). arXiv:2602.15532.
[I] *Measuring what Matters: Construct Validity in LLM Benchmarks* (2025). arXiv:2511.04703.
[I] *Measurement to Meaning: A Validity-Centered Framework for AI Evaluation* (2025). arXiv:2505.10573.
[I] *Reliability without Validity: … LLM-as-a-Judge* (2026). arXiv:2606.19544.
[I] Kapoor, S., & Narayanan, A. (2022). Leakage and the Reproducibility Crisis in ML-based Science.
arXiv:2207.07048 (later *Patterns*, 2023).

**Circularity of measurement / regress.**
[I] Tal, E. (2013). Measurement in Science. *Stanford Encyclopedia of Philosophy*.
[II] Chang, H. (2004). *Inventing Temperature: Measurement and Scientific Progress*. Oxford University
Press.
**External data (experiment, Part IV.4).**
[I] NASA Exoplanet Archive — Kepler Objects of Interest (cumulative KOI table) and Planetary Systems (ps) table, queried via the TAP service, https://exoplanetarchive.ipac.caltech.edu/TAP/sync . NASA Exoplanet Science Institute / IPAC–Caltech. Accessed 2026-07.
[I] NCBI ClinVar (review status & clinical significance), NCBI E-utilities esearch, db=clinvar,
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi . Accessed 2026-07.
[I] NIST National Vulnerability Database (NVD) CVE API 2.0,
https://services.nvd.nist.gov/rest/json/cves/2.0 . Accessed 2026-07.


[n] Sextus Empiricus, *Outlines of Pyrrhonism* (Agrippa's trilemma); Albert, H. (1968). *Traktat über
die kritische Vernunft* (Münchhausen trilemma); Klein, P. (2005). Infinitism is the solution to the
regress problem. In *Contemporary Debates in Epistemology*.
