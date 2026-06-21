"""
triadic.py — Deep validation layer: deductive -> inductive -> abductive.

Validated in the peer-review test (round on a real paper): the ABDUCTIVE pass
is the load-bearing addition — it generates rival explanations for the observed
result (the move a great reviewer makes and a pure destruens under-covers).
Deductive and inductive are explicit passes that overlap with existing roles
but cleanly catch mode-specific errors (internal contradiction / calibration;
generalization / sample-to-claim).

Order note: deductive->inductive->abductive is the order for VALIDATING a
finished artifact (does it follow -> does it generalize -> is there a better
explanation). It is intentionally NOT Peirce's inquiry order
(abduction->deduction->induction), which is for GENERATING knowledge.

Anti-optimism: the abductive pass carries an ANCHORING GATE. A rival hypothesis
is admitted only if it is (a) anchored to a fact/mechanism in the dossier and
(b) falsifiable (it states the discriminating test that would confirm/refute
it). A merely-conceivable rival is rejected — the mirror of the destruens
defense-gate.

Deploy as an adaptive DEEP layer (when the artifact makes inferential claims,
e.g. science, models, analyses), not always — the Freno.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .llm import LLMClient
from .schema import Finding, Accusation, Defense, DefectClass, EvidenceBase, Posta, CostToFix


# --------------------------------------------------------------------------
# Abductive rival hypothesis
# --------------------------------------------------------------------------

@dataclass
class RivalHypothesis:
    id: str
    claim: str                      # the alternative explanation of the result
    anchored_to: str = ""           # the dossier fact/mechanism it rests on
    discriminating_test: str = ""   # what would confirm/refute it
    strength_vs_authors: str = ""   # relative strength vs the artifact's own thesis
    passes_gate: bool = False       # anchored AND falsifiable

    def evaluate_gate(self) -> bool:
        """Anchoring gate: admit only if anchored to a fact AND falsifiable."""
        self.passes_gate = bool(self.anchored_to.strip()) and \
            bool(self.discriminating_test.strip())
        return self.passes_gate


@dataclass
class TriadicResult:
    deductive: list[Finding] = field(default_factory=list)
    inductive: list[Finding] = field(default_factory=list)
    abductive: list[RivalHypothesis] = field(default_factory=list)

    @property
    def admitted_rivals(self) -> list[RivalHypothesis]:
        return [r for r in self.abductive if r.passes_gate]

    def summary(self) -> str:
        return (f"triadic: deductive={len(self.deductive)} "
                f"inductive={len(self.inductive)} "
                f"abductive(admitted)={len(self.admitted_rivals)}/{len(self.abductive)}")


# --------------------------------------------------------------------------
# Prompts (carry distinctive markers used by the mock backend)
# --------------------------------------------------------------------------

_DEDUCTIVE_SYS = (
    "You run the DEDUCTIVE ANALYSIS pass of a deep validation layer. Question: "
    "do the artifact's CONCLUSIONS follow necessarily from its premises and "
    "data? Check logical validity, internal contradictions, recomputation, and "
    "claims that exceed what the data deductively supports. Return JSON "
    "{\"findings\":[{element, taxonomy_cell, accusation:{text,base,evidence,"
    "sections}, defense:{attempted,present,fact}, cost_to_fix, action, "
    "declared_limit, severity}]}."
)

_INDUCTIVE_SYS = (
    "You run the INDUCTIVE ANALYSIS pass. Question: does the specific evidence "
    "support the GENERALIZATION claimed? Scrutinize sample/representativeness, "
    "internal-vs-external validity, overfitting, prevalence/base-rate transfer, "
    "and 'n=1 -> universal' leaps. Same JSON shape as the deductive pass."
)

_ABDUCTIVE_SYS = (
    "You run the ABDUCTIVE ANALYSIS pass (inference to the best explanation). "
    "Generate concrete RIVAL explanations that could account for the observed "
    "result as well as or better than the artifact's own thesis. ANCHORING "
    "GATE: a rival is admissible ONLY if it is (a) anchored to a fact/mechanism "
    "in the dossier and (b) falsifiable — it must state the discriminating test "
    "that would confirm or refute it. Do not offer merely-conceivable rivals. "
    "Return JSON {\"rivals\":[{id, claim, anchored_to, discriminating_test, "
    "strength_vs_authors}]}."
)


def _parse_findings(data, role_key: str) -> list[Finding]:
    out: list[Finding] = []
    raw = data.get("findings", []) if isinstance(data, dict) else []
    for rf in raw:
        if not isinstance(rf, dict) or not rf.get("element"):
            continue
        acc = rf.get("accusation", {}) or {}
        dfn = rf.get("defense", {}) or {}
        try:
            base = EvidenceBase(str(acc.get("base", "reading")).lower())
        except ValueError:
            base = EvidenceBase.READING
        out.append(Finding(
            id=str(rf.get("id") or f"{role_key}-?"),
            element=str(rf.get("element")),
            taxonomy_cell=str(rf.get("taxonomy_cell", "mechanisms")),
            defect_class=(DefectClass.EPISTEMIC if role_key != "deductive"
                          else DefectClass.IDIOSYNCRATIC_LOCAL),
            posta=Posta.MEDIUM,
            accusation=Accusation(text=str(acc.get("text", "")), base=base,
                                  evidence=str(acc.get("evidence", "")),
                                  sections=list(acc.get("sections", []) or [])),
            defense=Defense(attempted=bool(dfn.get("attempted", False)),
                            present=bool(dfn.get("present", False)),
                            fact=dfn.get("fact")),
            cost_to_fix=CostToFix.MEDIUM,
            action=str(rf.get("action", "")),
            declared_limit=rf.get("declared_limit"),
            source_role=f"triadic:{role_key}",
            severity=str(rf.get("severity", "")),
        ))
    return out


class TriadicLayer:
    def __init__(self, client: LLMClient):
        self.client = client

    def run(self, artifact: str, dossier: str) -> TriadicResult:
        user = f"DOSSIER:\n{dossier}\n\nARTIFACT:\n{artifact}"

        ded = self._safe_json(_DEDUCTIVE_SYS, user)
        ind = self._safe_json(_INDUCTIVE_SYS, user)
        abd = self._safe_json(_ABDUCTIVE_SYS, user)

        result = TriadicResult(
            deductive=_parse_findings(ded, "deductive"),
            inductive=_parse_findings(ind, "inductive"),
        )
        for rr in (abd.get("rivals", []) if isinstance(abd, dict) else []):
            if not isinstance(rr, dict) or not rr.get("claim"):
                continue
            rival = RivalHypothesis(
                id=str(rr.get("id") or "AB-?"),
                claim=str(rr.get("claim")),
                anchored_to=str(rr.get("anchored_to", "")),
                discriminating_test=str(rr.get("discriminating_test", "")),
                strength_vs_authors=str(rr.get("strength_vs_authors", "")),
            )
            rival.evaluate_gate()
            result.abductive.append(rival)
        return result

    def _safe_json(self, system: str, user: str):
        try:
            return self.client.complete_json(system, user, max_tokens=3072)
        except ValueError:
            return {}
