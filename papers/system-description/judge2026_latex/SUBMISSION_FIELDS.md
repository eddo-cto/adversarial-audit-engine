# OpenReview submission — copy-paste fields (JUDGe @ NeurIPS 2026)

**Track:** Short Paper (4 pages + references → poster).
**Deadline:** 29 August 2026, 11:59 PM AoE. **Double-blind:** keep the PDF anonymous (it is).

---

## Title
A Judge That Cannot Certify Itself: A Code-Enforced Trust Protocol for Adversarial LLM Auditing

## TL;DR (one sentence)
A trust protocol that makes an adversarial LLM auditor unable to certify itself — non-closure is
cryptographic, cross-model independence is adapter-attested, and an under-run is refused in code — emitted
per run as a machine-checked judge-deployment disclosure record.

## Abstract (plain text)
LLM-based evaluators fail most dangerously when they are reliable without being valid: internally
consistent, confident, and biased. The largest systematic study of LLM-as-a-judge to date reports exactly
this dissociation — test–retest consistency above 0.95 coexisting with severe position bias, and
exact-match agreement overstating discrimination by 33–41 points of kappa once chance-corrected. Such a
judge is at its most harmful the moment it is allowed to certify itself: to declare its own output
validated, or to count its own internal agreement as independence. We present a trust protocol — a small
set of invariants an adversarial LLM-audit pipeline is made to obey in ordinary code, not in prompts, and
each pinned by a test. (1) The pipeline can never return VALIDATED on internal grounds; human closure is a
cryptographic HMAC of the audit-ledger digest under a key the model cannot reach. (2) Cross-model
independence is attested by the calling adapter, not read from a self-report. (3) A run is admitted only
under an A+B contract — a measured minimum of layers actually executed and every other layer carrying an
explicit applicable/not-applicable verdict — otherwise the pipeline refuses to close and exits non-zero, a
refusal that overrides even a valid human attestation. (4) The engine is turned on itself and the audit
trail is shipped. We make no detection-superiority claim; the contribution is the closure discipline
itself, and a per-run disclosure record — which layers ran, which were adjudicated out and why, what
independence was attested, whether closure was reached — that a judge cannot silently violate. This is a
machine-checked instance of the judge-deployment disclosure standard JUDGe is convening.

## Keywords
LLM-as-a-judge; evaluator reliability and validity; adversarial auditing; enforced non-closure;
cryptographic attestation; run-validity contract; reproducibility; disclosure standard; trust protocol

## Suggested primary / secondary areas (match to the form's dropdown)
- Primary: Production evaluation pipeline case studies (systems / governance)
- Secondary: Adversarial robustness of safety evaluators; Multi-judge ensembles and disagreement
  resolution; Human–model alignment in evaluation

## Upload
- PDF: `judge2026_trust_protocol.pdf` (line-numbered submission version — keep the line numbers).
- Authors field: enter your real name/affiliation (OpenReview hides it from reviewers in double-blind);
  the PDF itself stays anonymous.

## Pre-submit checklist
- [ ] PDF is the official-style, line-numbered, 4-page version.
- [ ] No author name / affiliation / repo URL visible anywhere in the PDF.
- [ ] (Optional) anonymized artifact link for reviewers — see note below.
- [ ] Submit before 29 Aug AoE.

## Optional: anonymized artifact link (lets reviewers test the repo)
The paper says an anonymized repository is "provided for review." To make that real without breaking
double-blind, create an anonymized mirror (e.g. https://anonymous.4open.science) of the public repo and
paste that link in place of "an anonymized repository" — but first scrub author-identifying content
(commit names, the companion papers' author/DOI, any email). If scrubbing is too much before the deadline,
submit without a live link (common for workshops) and disclose the repository on acceptance.
