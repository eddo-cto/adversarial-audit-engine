# A Judge That Cannot Certify Itself: A Code-Enforced Trust Protocol for Adversarial LLM Auditing

*Submission to JUDGe @ NeurIPS 2026 — "Can We Trust the Judge?" · Short paper (poster track) ·
Double-blind: author identity and repository URL are withheld; the artifact is available at an anonymized
repository and will be de-anonymized on acceptance.*

---

## Abstract

LLM-based evaluators fail most dangerously when they are **reliable without being valid** — internally
consistent, confident, and biased. The largest systematic study of LLM-as-a-judge to date reports exactly
this: test–retest consistency above 0.95 coexisting with severe position bias, and exact-match agreement
overstating discrimination by 33–41 points of κ once chance-corrected [1]. Such a judge is at its most
harmful the moment it is permitted to **certify itself** — to declare its own output validated, or to
count its own internal agreement as independence. We present a **trust protocol**: a small set of
invariants an adversarial LLM-audit pipeline is made to obey *in ordinary code*, not in prompts, and each
pinned by a test. (1) The pipeline can never return `VALIDATED` on internal grounds; human closure is a
**cryptographic HMAC** of the audit-ledger digest under a key the model cannot reach, so a model that
authors the payload cannot sign its own validation. (2) Cross-model independence is **attested by the
calling adapter**, not read from a self-report. (3) A run is admitted as a run only under an **A+B
contract** — a *measured* minimum of layers actually executed, **and** every other layer carries an
explicit applicable/not-applicable verdict — otherwise the pipeline **refuses to close** and exits
non-zero, a refusal that overrides even a valid human attestation. (4) The engine is turned on itself and
the audit trail is shipped, including a different-vendor review that killed an earlier version of our own
central claim. We make **no detection-superiority claim**; the contribution is the closure discipline
itself, and a per-run **disclosure record** — which layers ran, which were adjudicated out and why, what
independence was attested, whether closure was reached — that a judge cannot silently violate. This is a
machine-checked instance of the judge-deployment disclosure standard JUDGe is convening.

## 1. The problem: self-certification, not inaccuracy

Evaluation validity is a property of a judge *in a system*, not in isolation [2]. A well-calibrated judge
can fail systematically once its output gates a safety decision or feeds back into training. The specific
failure this paper targets is **self-certification**: a judge that treats its own stability as validity
and its own agreement as independence. Norman et al. [1] give the empirical warrant — reliability and
validity are dissociated across 21 judges and ~541k judgments — but a diagnosis is not a mechanism. If a
biased-but-consistent judge can stamp its own output "validated," everything downstream inherits an error
the system cannot see. The question we take up is not *how accurate is the judge* but *can the judge be
stopped from closing its own loop*.

## 2. The protocol

The system is an orchestrator that spawns adversarial LLM sub-agent roles (an oracle that cites facts and
emits no verdicts; a verifier that recomputes and, where code is runnable, *executes* it; a propagator
that builds the concrete sequence violating a guarantee) and hands their findings to a **deterministic
core** that assigns verdicts and decides closure. The orchestrator coordinates; it does not judge. Four
invariants live in that core.

**I1 — Non-closure is cryptographic.** The completion state machine reaches `VALIDATED` only on a valid
HMAC of the ledger digest under an operator key (`AAE_HUMAN_KEY`) held outside the model's reach. A bare
"human-approved" token that does not verify closes nothing. A `Stop` hook re-verifies the HMAC in the
operator's environment and, if a `VALIDATED` does not verify, downgrades the ledger on disk. The model
authors the payload but not the key: it cannot forge its own validation.

**I2 — Independence is attested, not claimed.** Different-vendor review is credited (independence
level 3) only from the identity the *calling adapter* reports. A different-vendor label present only in
the payload is recorded as `CROSS_MODEL_CLAIMED` and buys no independence credit. This directly answers
the "self-preference / correlated-blind-spot" facet: a second model prompted adversarially by the same
vendor is not counted as an independent draw.

**I3 — The A+B run-validity contract.** A pipeline that silently skips layers can still print a confident
verdict; the danger is a run that *looks* complete because no one counted what did not happen. A run is
admitted only if **(A)** a measured minimum of required layers actually executed — measured from each
layer's own output (findings by source role, the oracle from its distinct cited sources, the governor
from the meta verdict), not from self-report — **and (B)** every other layer carries an explicit
`RAN`/`NOT_APPLICABLE`/`MISSING` status with justification. The manifest computes `run_validity`; if it
is not `VALID`, completion is forced to `INVALID_RUN`, which **overrides every other state, including a
valid human `VALIDATED`**, and the process exits non-zero. Closure cannot be bought by signing an
incomplete process. The required minimum was itself **measured** across 10 runs over 8 artifact classes,
not assumed — and the measurement corrected an earlier over-inclusion (one role we had frozen as required
was recovered as optional when two classes reached their defects without it).

**I4 — Self-audit, shipped.** The engine is run against its own artifacts and papers and the ledgers are
committed. This is not decoration: a same-vendor self-audit (independence level 1) found four defects in
our own closure guarantees; a later different-vendor review (level 3) killed the original headline
empirical claim and forced two guarantees from convention into cryptographic code; and the measurement
instrument of I3, when first run, found three real defects *in itself*. We report these because a system
whose value is adversarial honesty must show the audits that caught it.

Each invariant is a test in a 173-test suite run in CI across Python 3.10–3.13, including an end-to-end CI
step that **fails if the pipeline ever prints `VALIDATED` without a human**.

## 3. Relation to existing work

**Reliability vs. validity of judges [1].** We take their empirical finding as the motivation and supply
the missing *enforcement* layer. They measure that judges are reliable-without-valid and recommend a
"Minimum Viable Validation Protocol"; but a recommendation is advisory — a judge can decline it and
certify itself anyway. We make the most dangerous consequence — self-certification — structurally
impossible in code. We do not re-measure judge bias.

**Adversarial defect discovery.** The closest adversarial system, Refute-or-Promote [3], shares the
adversarial kill-mandate and a cross-model critic and demonstrates them at scale (a 31-day campaign,
~171 candidates, ~79% killed pre-disclosure, real CVEs and accepted ISO C++ reports). We claim no
priority on those ideas. The difference is the objective: Refute-or-Promote optimizes **precision of
discovery** with a **human orchestrator** and no enforced non-closure — its cross-model step *improves*
reliability but nothing *forbids* a confident close. We optimize **trustworthiness of closure**: judging
is code, independence must be adapter-attested, closure is cryptographic, and an under-run is refused
non-bypassably. A better *finder* versus a *finder that cannot lie about having finished*; the two are
complementary.

**Adversarial robustness of judges.** Work on prompt-injection attacks against judges [4] asks whether a
judge can be *fooled from outside*. We ask the orthogonal question — whether a judge can be *stopped from
certifying itself from inside* — and enforce the answer in code rather than in a prompt.

**JUDGe's disclosure template.** The workshop's community deliverable is a judge-deployment disclosure
standard (provenance, deployment context, known failure modes, human validation). Our execution manifest
and A+B record are a *machine-checked instance* of such a disclosure: emitted per run, refused when
incomplete.

## 4. Limitations

We make no detection-superiority claim; our small-sample empirical study (n=7 real errors, one run per
model nature) is a descriptive dissociation, not a recall result, and is reported as such in the
companion systems paper. The cryptographic non-closure is only as strong as the operator's key hygiene —
it contracts forgery from a payload field to an out-of-band secret, it does not eliminate it. Real
cross-vendor independence depends on an adapter the operator must wire up; absent it, the external-auditor
role is theatre, and the code says so. And the whole apparatus is a **survivor**: every internal audit
sits at independence level 1–2 and validates nothing — by construction, only an external human eye closes
the loop. That is the protocol's own thesis applied to itself.

## References

[1] J. D. Norman, M. U. Rivera, D. A. Hughes. *Reliability without Validity: A Systematic, Large-Scale
Evaluation of LLM-as-a-Judge Models Across Agreement, Consistency, and Bias.* arXiv:2606.19544, 2026.

[2] JUDGe @ NeurIPS 2026 — *Can We Trust the Judge?* Workshop call and failure taxonomy.
https://judge2026.github.io/, 2026.

[3] A. Agarwal. *Refute-or-Promote: An Adversarial Stage-Gated Multi-Agent Review Methodology for
High-Precision LLM-Assisted Defect Discovery.* arXiv:2604.19049, 2026.

[4] *Adversarial Attacks on LLM-as-a-Judge Systems: Insights from Prompt Injections.* arXiv:2504.18333,
2025.

---

*Anonymized for double-blind review. Artifact (MIT-licensed engine, 4 reproducible benchmarks, 173 tests,
CI-checked protocol invariants) available at an anonymized repository; de-anonymized on acceptance.
Companion systems paper describes the architecture and the full self-audit trail.*
