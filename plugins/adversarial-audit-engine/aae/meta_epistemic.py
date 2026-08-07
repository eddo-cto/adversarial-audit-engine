"""
meta_epistemic.py — The fifth layer: the Meta-Epistemic Governor.

It does NOT validate the artifact. It validates the VALIDATOR: bias, coverage,
independence, calibration, failure modes — and above all the deepest risk, the
one the other four layers cannot see about themselves: APPARENT COHERENCE, a
framework that looks rigorous but self-confirms within its own limits.

Validated by a falsifiable test: a blind governor, given neutral descriptions of
five past runs, independently rediscovered every confound that had been
documented by hand (oracle-leakage, fallible ground-truth, operator-optimism,
hype-bias) AND surfaced new ones (reversed anchoring; tight-score-range = no
discrimination), AND found the transversal law:

    robustness is INVERSELY correlated with the cleanliness of the result;
    a perfect score without real independence is not quality — it is the
    signature of a closed circuit.

NON-NEGOTIABLE DESIGN CONSTRAINT (fallibilist + human-terminating): a governor
built from the same machinery as the system shares the system's blind spots. It
can detect specific failure-signatures; it CANNOT self-certify. So it ALWAYS
declares its own limit and routes the residue to the human/external eye. The
recursion stops here (meta-1) + human — there is no meta-2 (the Freno). If it
ever 'closed the loop' and certified itself, it would BE the apparent coherence
it exists to detect.

The load-bearing detector is deterministic (the transversal law as code):
clean result + low independence + no declared limits + no CONTESO == suspect.
An LLM pass adds the qualitative confound detection. The verdict is never
"VALIDATED"; the best internal verdict is RELIABLE_WITH_RESERVATIONS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .llm import LLMClient
from .schema import Verdict, IndependenceLevel


class ReliabilityVerdict(str, Enum):
    RELIABLE_WITH_RESERVATIONS = "reliable_with_reservations"
    NOT_INTERNALLY_VERIFIABLE = "not_internally_verifiable"
    # NB: there is deliberately no "RELIABLE"/"VALIDATED" — internal grounds
    # can never reach it; only an external human eye can.


@dataclass
class GovernorCheck:
    dimension: str          # coverage|independence|calibration|confound|apparent_coherence|failure_mode
    finding: str
    severity: str = "info"  # info|warning|critical


@dataclass
class MetaAssessment:
    checks: list[GovernorCheck] = field(default_factory=list)
    verdict: ReliabilityVerdict = ReliabilityVerdict.RELIABLE_WITH_RESERVATIONS
    residue_to_human: str = ""        # what only an external eye can close
    apparent_coherence_score: float = 0.0  # 0 (no signs) .. 1 (strong circuit-closure)

    def critical(self) -> list[GovernorCheck]:
        return [c for c in self.checks if c.severity == "critical"]

    def summary(self) -> str:
        lines = [f"meta-epistemic governor: verdict={self.verdict.value}",
                 f"  apparent-coherence score: {self.apparent_coherence_score:.2f} "
                 f"(higher = more circuit-closure)"]
        for c in self.checks:
            mark = {"critical": "!!", "warning": " *", "info": "  "}[c.severity]
            lines.append(f"  {mark} [{c.dimension}] {c.finding}")
        lines.append(f"  residue (needs external/human): {self.residue_to_human}")
        return "\n".join(lines)


# Distinctive marker for the mock backend: "meta-epistemic governor".
_GOVERNOR_SYS = (
    "You are a META-EPISTEMIC GOVERNOR. You do NOT judge the artifact; you judge "
    "the VERIFICATION PROCESS for signs that it only SIMULATES robustness "
    "(apparent coherence / self-confirmation within its own limits). Be hostile "
    "toward the process: look for why the result should NOT be trusted. Cover: "
    "coverage gaps, real independence (same-model agents are NOT independent), "
    "calibration (is the metric/ground-truth itself fallible?), confounds (did "
    "whoever supplied the facts also supply the answers? biased sources? a "
    "declared prior steering the outcome?), apparent-coherence signatures (too "
    "clean: 100% / zero false positives / no declared limits / no disagreement). "
    "Return JSON {\"checks\":[{dimension,finding,severity}], "
    "\"residue_to_human\": str}. You CANNOT self-certify; always state the "
    "residue that only an external human eye can close."
)


class MetaGovernor:
    def __init__(self, client: LLMClient | None = None):
        self.client = client

    # ---- deterministic detector: the transversal law, as code ----------

    def _structural_checks(self, *, total_findings: int, holds: int,
                           defective: int, needs_expert: int,
                           declared_limits: int, coverage_flags: int,
                           independence: IndependenceLevel,
                           false_positives: int) -> tuple[list[GovernorCheck], float]:
        checks: list[GovernorCheck] = []
        signals = 0.0
        n = 5  # number of weighted signals

        low_independence = int(independence) <= int(IndependenceLevel.SAME_INSTANCE_ROLES)
        if low_independence:
            checks.append(GovernorCheck("independence",
                "agents share one instance/model family — NOT real independence; "
                "shared blind spots are invisible to this run", "critical"))
            signals += 1

        # "too clean": everything holds, no contested, no declared limits
        clean = (total_findings > 0 and defective == 0 and needs_expert == 0
                 and false_positives == 0)
        if clean:
            checks.append(GovernorCheck("apparent_coherence",
                "result is suspiciously clean (no defects upheld, no CONTESO, "
                "no false positives): a signature of circuit-closure, not quality",
                "critical" if low_independence else "warning"))
            signals += 1
        if needs_expert == 0:
            checks.append(GovernorCheck("calibration",
                "no finding routed to CONTESO/expert — the system resolved "
                "everything internally; suspicious for a hard artifact", "warning"))
            signals += 0.5
        if declared_limits == 0:
            checks.append(GovernorCheck("apparent_coherence",
                "no internal limit declared anywhere — honesty signal missing",
                "warning"))
            signals += 1
        if coverage_flags > 0:
            checks.append(GovernorCheck("coverage",
                f"{coverage_flags} taxonomy dimension(s) uncovered/unjustified",
                "warning"))
            signals += 0.5
        else:
            checks.append(GovernorCheck("coverage",
                "coverage gate satisfied — but completeness against the FIXED "
                "taxonomy, not against unknown-unknowns", "info"))

        return checks, min(1.0, signals / n)

    def assess(self, audit_result, *, use_llm: bool = True) -> MetaAssessment:
        """audit_result: an orchestrator.AuditResult. Pure-structural checks are
        always run; the LLM confound pass is optional."""
        led = audit_result.ledger
        m = audit_result.metrics
        holds = m.by_verdict.get(Verdict.ARTIFACT_HOLDS.value, 0)
        defective = m.by_verdict.get(Verdict.ARTIFACT_DEFECTIVE.value, 0)
        checks, ac_score = self._structural_checks(
            total_findings=m.total_findings, holds=holds, defective=defective,
            needs_expert=m.needs_expert, declared_limits=m.declared_limits,
            coverage_flags=sum(1 for fl in led.flags
                               if str(fl).startswith("COVERAGE INCOMPLETE")),
            independence=led.independence_level,
            false_positives=m.false_positive_guard)

        # optional qualitative confound pass
        if use_llm and self.client is not None:
            user = ("Process facts:\n"
                    f"- independence level: {int(led.independence_level)} (1=same instance)\n"
                    f"- findings: {m.total_findings}; defective={defective}; "
                    f"holds={holds}; needs_expert={m.needs_expert}; "
                    f"false_positives={m.false_positive_guard}; "
                    f"declared_limits={m.declared_limits}\n"
                    f"- coverage flags: {led.flags}\n"
                    f"- completion: {audit_result.completion.state}\n"
                    "Judge the PROCESS, not the artifact.")
            try:
                data = self.client.complete_json(_GOVERNOR_SYS, user, max_tokens=2048)
                for c in (data.get("checks", []) if isinstance(data, dict) else []):
                    if isinstance(c, dict) and c.get("finding"):
                        checks.append(GovernorCheck(
                            dimension=str(c.get("dimension", "confound")),
                            finding=str(c.get("finding")),
                            severity=str(c.get("severity", "warning"))))
                residue_llm = data.get("residue_to_human", "") if isinstance(data, dict) else ""
            except ValueError:
                residue_llm = ""
        else:
            residue_llm = ""

        # verdict: low independence OR strong apparent-coherence => not internally verifiable
        low_independence = int(led.independence_level) <= int(IndependenceLevel.SAME_INSTANCE_ROLES)
        verdict = (ReliabilityVerdict.NOT_INTERNALLY_VERIFIABLE
                   if (low_independence or ac_score >= 0.6)
                   else ReliabilityVerdict.RELIABLE_WITH_RESERVATIONS)

        # mandatory recursive meta-declaration: terminate at the human
        residue = (residue_llm or
                   "An external human eye (different identity / domain expert) "
                   "must confirm coverage of unknown-unknowns and resolve any "
                   "metric/ground-truth disputes.") + \
            " | GOVERNOR SELF-LIMIT: built from the same machinery as the system, " \
            "I cannot certify my own reliability; I detect failure-signatures, " \
            "I do not close the loop."

        return MetaAssessment(checks=checks, verdict=verdict,
                              residue_to_human=residue,
                              apparent_coherence_score=ac_score)

    def falsification_type1(self, demolition_scores_valid, demolition_scores_invalid,
                            *, threshold=0.5, k=1, m=1):
        """negation_spectrometry integrated into the governor: turn "the auditor demolishes
        too much" into a MEASURED number. Given the auditor's demolition SCORES on a control
        battery (VALID artifacts that must survive + INVALID that must die), return the
        false-demolition rate FDR (Type-I), power TDR, AUC, and the k-of-m persistence bound.
        Domain-agnostic: the caller supplies the battery. See aae/negation_spectrometry.py."""
        import importlib.util as _u, os as _os, sys as _sys
        _p = _os.path.join(_os.path.dirname(__file__), "negation_spectrometry.py")
        _sp = _u.spec_from_file_location("negation_spectrometry", _p)
        _ns = _u.module_from_spec(_sp); _sys.modules["negation_spectrometry"] = _ns; _sp.loader.exec_module(_ns)
        cal = _ns.calibrate(demolition_scores_valid, demolition_scores_invalid, threshold=threshold)
        cal["type1_bound_kofm"] = _ns.binom_tail(k, m, cal["FDR"]) if m else None
        cal["verdict"] = ("discriminative auditor" if cal["AUC"] >= 0.7 and cal["FDR"] <= 0.2
                          else "over-demolition suspect / weak power")
        cal["note"] = ("measured against an EXTERNAL control battery; with correlated auditors "
                       "the assumption-free residual is >= the independence bound p^m")
        return cal
