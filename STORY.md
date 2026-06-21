# I built an engine that tries to destroy your work — and it refuses to ever say "validated"

Large language models are agreeable by temperament. Ask one to review your spec, your trading thesis, your proof, and it will mostly find ways to like it. That is precisely the wrong instinct for review. Serious review needs an adversary — something that *wants* to find the flaw, that treats your artifact as guilty until a defense survives.

So I built one. Not a clever prompt: a software-engineered engine, hardened across seven adversarial rounds, that deploys a hive of blind attacker roles against a high-complexity artifact and tries to falsify it. The most important thing about it is the line it will not cross: **it never reports "validated" on internal grounds. Only a human does.**

This is the story of what survived the rounds, and why the honest limits are the point — not a footnote.

## The bet: discipline in code, not in the prompt

A prompt that says "be a harsh critic" decays. It drifts, it rationalizes, it rubber-stamps under pressure. So the discipline lives in Python, not in instructions. The LLM provides the semantics — reading, reasoning, domain knowledge — while deterministic code enforces the rules that the rounds proved matter: a verdict state machine, a defense-gate, per-dimension coverage, deduplication, metrics, and a meta-level governor. The model is the engine of meaning; the code is the engine of discipline.

## Seven rounds, and what each one taught

**Round 1** pitted two hostile hives against an artifact at once — one hunting for holes, one hunting for over-engineering. The surprise wasn't the holes; it was the false positives. The fix became a permanent rule: the **defense-gate**. No accusation may condemn until the engine has first tried to mount the *strongest possible defense* of the artifact and failed. Attempting the best defense before the verdict drove false positives to near zero across every later round.

**Round 2** moved to a different domain with a blind sub-agent and a web-research oracle, and forced a question that haunts every reviewer: what's your recall? Not globally — *per class of defect*. Lookup errors, numeric errors, local idiosyncratic bugs, and non-local conceptual flaws have wildly different detectability. Reporting one number hides the failures.

**Round 3** introduced the "stem-cell" hive: an oracle for research, a verifier that checks the artifact point by point, and attackers that spawn against specific vectors. Specialization beat a single generalist critic.

**Round 4** added domain specialists — an epistemologist, an informal logician, a continuum-mathematics expert, an ethicist, a phenomenologist — and immediately created a new risk: too much machinery. That produced the **Freno** ("the brake"): an explicit anti-over-engineering check. If a layer doesn't earn its complexity against real findings, it gets cut. Most proposals get cut.

**Round 5** was deliberately hostile: an artifact seeded with unfavorable errors and traps. It exposed the deepest humility in the whole project — the **fallible yardstick**. The ground truth you check against can itself be wrong. An engine that trusts its answer key inherits the answer key's mistakes. So the yardstick is treated as fallible, and disagreement with it is a signal, not a verdict.

**Round 6** added the **propagator** — the role that hunts *non-local* defects. A premise broken in section one can silently invalidate a guarantee in section four. Local checking never catches these; you have to trace consequences across the whole artifact. This round also surfaced the **oracle confound**: if your research oracle pre-supplies "typical errors," it leaks the answers and the hive looks smarter than it is. We isolated the oracle to stop the leak.

**Round 7** pushed to conceptual non-local defects and drew a hard line between two kinds: those documented somewhere in the literature, and those that are genuinely novel. The first the engine can argue; the second it cannot decide internally. Novel conceptual flaws are **routed to a human by construction**. Refusing to bluff on them is a feature.

## The architecture that survived

Five layers, each tested before it was allowed in:

The **destruens** does point-by-point verification plus non-local propagation. The **construens** diagnoses *why something is absent* using an inverted defense-gate — the optimistic "this is fixable" hypothesis must itself survive attack. The **generative** layer reasons deductively, then inductively, then abductively, generating rival hypotheses rather than defending the first one. The **deep-causal** layer clusters root causes, runs a forward/backward chiasm to cross-validate, and diffuses gated scenarios. And the **meta-epistemic governor** validates the validator — checking the run for bias, coverage gaps, lost independence, and the most seductive failure of all: *apparent coherence*. A clean, confident, internally consistent report is not the same as a robust one. In fact one transversal law kept recurring: robustness is inversely correlated with cleanliness, and a clean result produced without independence is just a closed circuit admiring itself.

A verdict state machine ties it together. A *pattern* may flag but may never condemn; only reading or execution can condemn; contested findings route to `NEEDS_EXPERT`. The machine makes it structurally impossible to launder a hunch into a conviction.

## The principle we refused to break

Agents from the same model share the same blind spots. Two Claude instances arguing are not independent; they are one mind wearing two hats. So the engine grades its own independence honestly:

Level 1 is same-model roles — useful self-falsification, but *not* validation. Level 2 is a different model from the same vendor. Level 3 is a genuinely different vendor — independence rises, reliability improves, and the best verdict it can reach is `CROSS_MODEL_REVIEWED`. Level 4 is a competent human, and **only level 4 yields `VALIDATED`.** The cross-vendor eye can run on a different provider's model, but it is still a machine, and the engine says so. Early in development I caught a bug where a different-vendor model's review was being labeled "validated." Declaring a machine's review as validation is exactly the error this whole project exists to prevent. The fix made `VALIDATED` reachable only by a human-prefixed reviewer. The discipline is now in the code, not in my good intentions.

## The lesson I didn't want to learn

I turned the engine on its own origin — the analysis that had created an earlier artifact of mine — and it found a real bug the original analysis had missed. The original had reasoned beautifully *about the rules* and checked the syntax, but it never *executed the path*. The engine did, and the path crashed. Reasoning about a system is not the same as running it. That humbling result is the whole thesis in miniature: rigor is behavioral, not rhetorical.

## What it is not

It is not an oracle, and it will not make you money or make your decisions. It multiplies a competent human reviewer; it does not replace one. Its coverage is per-class and fallible. Without the human at level 4, the honest verdict stays "not validated." If that sounds like under-promising, that's deliberate — in a field full of tools that claim to find you truth, alpha, or certainty, the differentiator is a tool that tells you exactly where its own knowledge ends.

## Try it

The engine ships as a Claude Code plugin with a dependency-free Python core. Add the marketplace, install `adversarial-audit-engine`, and run `/audit` on the artifact you most want to be wrong about. Then bring it a human. It was built to make that human faster and sharper — never to stand in for them.

*Research preview. Not professional advice. The output must be verified by a competent person before any decision.*
