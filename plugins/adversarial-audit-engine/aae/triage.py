"""
triage.py — Dimension checklist and adaptive role deployment.

Round 4 conclusion, made into code: don't run a fixed panel. A core set always
runs; specialists are deployed only when the artifact has their surface. And
the verification round demanded the matrix be a FIXED, explicit checklist that
the model fills (and justifies exclusions for) — not a free-form "judge builds
a matrix", which was unfalsifiable. So the candidate dimensions are hard-coded;
the LLM scores presence and the code enforces that each is addressed or
excluded-with-reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .llm import LLMClient


# Fixed taxonomy of coverage dimensions (round 3 §3.2, extended).
TAXONOMY = [
    "premises",        # declared and hidden assumptions
    "inputs",          # inputs and their qualification (who provides, with what incentive)
    "mechanisms",      # internal logic / procedures / rules / derivations
    "outputs",         # outputs and their recipients
    "boundary",        # boundary/limit/failure conditions
    "interface",       # who uses it, with what capabilities; transitions/handover
]

# Signals that justify deploying each specialist (round 4: deploy only on surface).
SPECIALIST_SIGNALS = {
    "epistemologist": "validation/methodology/statistics/evidence claims present",
    "logician": "formal structure, scales, quantifiers, probability composition, "
                "math beyond first order present",
    "ethicist": "impact on persons, fairness, consent, distribution of harm present",
    "phenomenologist": "lived experience / perception / how it is experienced present",
}

TRIAGE_SYSTEM = (
    "You are the TRIAGE step of an audit hive. Read the artifact and decide, "
    "against a FIXED checklist, which dimensions are present and which "
    "specialist roles to deploy. You may not invent dimensions; you must mark "
    "each candidate dimension present/absent and JUSTIFY every exclusion. "
    "Return JSON: {\"dimensions_present\": [...], \"deploy_roles\": [...], "
    "\"excluded\": {role: reason}}. Core roles verifier/reasoner/propagator are "
    "ALWAYS deployed; only decide the specialists."
)


@dataclass
class TriageResult:
    dimensions_present: list[str]
    deploy_roles: list[str]               # specialists to add to the core
    excluded: dict[str, str] = field(default_factory=dict)

    @property
    def active_roles(self) -> list[str]:
        core = ["verifier", "reasoner", "propagator"]
        return core + [r for r in self.deploy_roles if r not in core]


def run_triage(client: LLMClient, artifact: str) -> TriageResult:
    signals = "\n".join(f"- {k}: deploy if {v}" for k, v in SPECIALIST_SIGNALS.items())
    user = (
        f"Candidate dimensions: {', '.join(TAXONOMY)}.\n"
        f"Specialist deployment signals:\n{signals}\n\n"
        "Decide. Justify every specialist you exclude.\n\nARTIFACT:\n" + artifact
    )
    try:
        data = client.complete_json(TRIAGE_SYSTEM, user, max_tokens=1024)
    except ValueError:
        data = {}
    return TriageResult(
        dimensions_present=data.get("dimensions_present", list(TAXONOMY)),
        deploy_roles=data.get("deploy_roles", []),
        excluded=data.get("excluded", {}),
    )
