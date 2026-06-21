"""
oracle.py — The research oracle.

Round 7's decisive lesson: the oracle is not mere fact-grounding. By surfacing
documented domain mechanisms, it turns "novel-combination" conceptual defects
into catchable ones — it dissolves their novelty. So it must be POWERFUL
(deep domain research), and it must answer on demand for individual roles
(round 6: on-demand research closes the fact-dependent class).

Two responsibilities:
  - build_dossier(): up-front structured facts/mechanisms for the artifact.
  - answer(query): on-demand factual answer for a role mid-analysis.

The oracle returns FACTS, never verdicts (anti-anchoring guardrail). It also
serves as a false-positive shield: it supplies the canonical fact that lets a
role DEFEND a correct-but-surprising element (rounds 5 & 7).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .llm import LLMClient


ORACLE_SYSTEM = (
    "You are the RESEARCH ORACLE of an audit hive. Build a FACTUAL domain "
    "dossier the other agents will use. You do NOT find defects and you do NOT "
    "judge the artifact — you provide the correct facts, values, formulas, and "
    "MECHANISMS of the domain, with sources (URLs/clauses). Be rigorous on "
    "formulas and on documented mechanisms and their known consequences, "
    "because a documented mechanism is what lets a reviewer catch a "
    "combinatorial ('novel') defect."
)

ORACLE_QUERY_SYSTEM = (
    "You are the RESEARCH ORACLE answering a single targeted question for one "
    "audit role, mid-analysis. Answer with FACTS only (values, formulas, "
    "mechanisms, standards) and cite sources. Never give a verdict on the "
    "artifact; never say whether something is a defect."
)


@dataclass
class Dossier:
    text: str
    sources: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return self.text


class Oracle:
    def __init__(self, client: LLMClient, *, allow_web: bool = True):
        self.client = client
        self.allow_web = allow_web
        self._cache: dict[str, str] = {}

    def build_dossier(self, artifact: str, *, domain_hint: str = "") -> Dossier:
        user = (
            (f"Domain hint: {domain_hint}\n\n" if domain_hint else "")
            + "Read the artifact and produce the dossier of correct domain "
            "facts and mechanisms relevant to auditing it. Structure by theme. "
            "For every fact give the value/criterion, the source, and (where a "
            "value is often cited wrongly) the common confusion.\n\n"
            "ARTIFACT:\n" + artifact
        )
        try:
            data = self.client.complete_json(ORACLE_SYSTEM, user, max_tokens=4096)
            text = data.get("dossier") if isinstance(data, dict) else str(data)
            sources = data.get("sources", []) if isinstance(data, dict) else []
        except ValueError:
            # tolerate a prose dossier
            text = self.client.complete(ORACLE_SYSTEM, user, max_tokens=4096)
            sources = []
        return Dossier(text=text or "", sources=sources or [])

    def answer(self, query: str) -> str:
        """On-demand factual answer for a role. Cached within a run."""
        if query in self._cache:
            return self._cache[query]
        ans = self.client.complete(ORACLE_QUERY_SYSTEM, query, max_tokens=1024)
        self._cache[query] = ans
        return ans
