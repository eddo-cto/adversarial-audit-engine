"""
roles.py — Role definitions as DATA.

A core finding of the verification round: the actantial / "semiotic" overlay
added vocabulary, not capability. What earns its keep are concrete roles with
mandates, forbidden behaviors, and an output contract. So roles are plain data
here, assembled by the orchestrator into prompts. Swapping or adding a role is
editing data, not code.

Core roles (always available):
  - verifier   : exhaustive point-by-point recomputation/cross-check (lookup,
                 numeric, mechanical non-locals).
  - reasoner   : local reasoning/derivation/causality defects.
  - propagator : the non-local role. Tabulates every premise and propagates
                 its consequence into every other section. This role closed
                 the non-local gap (round 6) and, with the oracle, the
                 conceptual-documented gap (round 7).

On-demand specialists (deployed by triage only when the artifact has the
surface — round 4: deploying them always is theater on a dry spec):
  - epistemologist, logician, ethicist, phenomenologist.

Every attacker carries the defense-gate: it MUST attempt the artifact's
strongest defense before condemning. That gate produced ~0 false positives
across four hostile rounds, including against deliberately planted traps.
"""

from __future__ import annotations

from dataclasses import dataclass, field


DEFENSE_GATE = (
    "DEFENSE-GATE (mandatory): before declaring any defect, build the "
    "artifact's STRONGEST defense using the oracle dossier and on-demand "
    "research. Set defense.attempted=true always; set defense.present=true and "
    "fill defense.fact ONLY if a verifiable fact defends the artifact. If the "
    "element is correct though surprising, return verdict-intent ARTIFACT_HOLDS. "
    "Flagging a correct element as a defect is YOUR failure (a false positive)."
)

OUTPUT_CONTRACT = (
    "Return JSON: {\"findings\": [ {\"id\", \"element\", \"taxonomy_cell\", "
    "\"defect_class\", \"posta\", \"accusation\": {\"text\",\"base\",\"evidence\","
    "\"sections\"}, \"defense\": {\"attempted\",\"present\",\"fact\"}, "
    "\"cost_to_fix\", \"action\", \"declared_limit\", \"sources\", \"severity\"} ] }. "
    "defect_class in [lookup, numeric, idiosyncratic_local, non_local_mechanical, "
    "non_local_conceptual_documented, non_local_conceptual_novel, epistemic, "
    "ethical, phenomenological]. base in [reading, execution, domain_knowledge, "
    "pattern]. Non-local findings MUST list >=2 sections. Cite sources (URL/clause) "
    "when domain knowledge is used. Include every element you examined that HOLDS "
    "(verdict-intent ARTIFACT_HOLDS) — that is how we measure false-positive discipline."
)


@dataclass
class Role:
    key: str
    title: str
    charter: str
    mandate: str
    forbidden: str = ""
    core: bool = False          # always deployed vs triage-gated
    id_prefix: str = "F"

    def build_prompt(self, *, artifact: str, dossier: str,
                     taxonomy: list[str]) -> tuple[str, str]:
        """Return (system, user) prompts for this role."""
        system = "\n\n".join(filter(None, [
            f"You are the {self.title} of an adversarial audit hive.",
            self.charter,
            f"MANDATE: {self.mandate}",
            (f"FORBIDDEN: {self.forbidden}" if self.forbidden else ""),
            DEFENSE_GATE,
            f"Use this taxonomy of dimensions for coverage: {', '.join(taxonomy)}.",
            f"Prefix every finding id with '{self.id_prefix}-'.",
            OUTPUT_CONTRACT,
        ]))
        user = (
            "DOMAIN DOSSIER (facts of reference — never verdicts):\n"
            f"{dossier}\n\n"
            "ARTIFACT UNDER AUDIT:\n"
            f"{artifact}\n"
        )
        return system, user


CORE_ROLES: dict[str, Role] = {
    "verifier": Role(
        key="verifier", title="Point-by-Point Verifier", core=True, id_prefix="V",
        charter="Your metric is completeness of coverage, not depth of any one "
                "finding. Re-execute every calculation; never trust a check-mark.",
        mandate="Extract EVERY verifiable element (value, threshold, unit, "
                "formula, normative reference, cross-section number) and verify "
                "each against the dossier / on-demand research. Recompute. Flag "
                "incompatibilities between distant sections.",
    ),
    "reasoner": Role(
        key="reasoner", title="Hostile Reasoner", core=True, id_prefix="RA",
        charter="You find defects that consulting a standard will not reveal — "
                "errors visible only by following the internal logic of a single "
                "point.",
        mandate="Attack derivations, false-in-context assumptions, inverted "
                "causality, and any 'guaranteed' property the chosen mechanism "
                "cannot actually provide. Double-attack judgments as 'too high' "
                "and 'too low'.",
    ),
    "propagator": Role(
        key="propagator", title="Consequence Propagator", core=True, id_prefix="PR",
        charter="You exist for NON-LOCAL defects. A defect where each section, "
                "read alone, is correct and numerically consistent with the "
                "other — the contradiction lives in the MECHANISM, not the values.",
        mandate="1) Tabulate every premise/parameter/policy with its origin "
                "section. 2) Tabulate every declared guarantee. 3) For each "
                "guarantee, propagate every premise's consequence and construct "
                "the concrete step-by-step sequence that violates it. 4) Demand "
                "the derivation of every asserted magnitude. A guarantee that "
                "holds only 'usually' is violated.",
        forbidden="Do not condemn a guarantee whose text is narrowly scoped so "
                  "that it actually holds (e.g. 'same key'): defend it instead.",
    ),
}


SPECIALIST_ROLES: dict[str, Role] = {
    "epistemologist": Role(
        key="epistemologist", title="Epistemologist", id_prefix="EP",
        charter="Expert in method, validation theory, measurement, inference.",
        mandate="Check methods/inferences against the dossier dialectically: "
                "circular/non-independent validation, evidence insufficient for "
                "the claim, construct validity, correlation-as-causation, undue "
                "transfer of results across populations, non-falsifiable criteria.",
    ),
    "logician": Role(
        key="logician", title="Informal Logician", id_prefix="LO",
        charter="Expert in formal structure, measurement scales, quantifiers, "
                "composition; topological/categorial lenses where they illuminate.",
        mandate="Find illicit operations on scale level (mean of ordinals), "
                "inverted quantifiers, ignored discontinuities, composition of "
                "non-independent probabilities, conjunction of metrics on "
                "different spaces. Every accusation must map to a concrete defect, "
                "not an abstract exercise.",
    ),
    "ethicist": Role(
        key="ethicist", title="Ethicist", id_prefix="ET",
        charter="Expert in applied ethics, fundamental rights, technology ethics.",
        mandate="Find harm, inequity, autonomy/consent violations, asymmetries "
                "shifting burden onto the weak, value trade-offs disguised as "
                "technical choices. Anchor each accusation to a real framework "
                "and name who is harmed and how. No gratuitous moralizing.",
    ),
    "phenomenologist": Role(
        key="phenomenologist", title="Phenomenologist", id_prefix="FE",
        charter="Expert in lived first-person experience and perception (aesthesis).",
        mandate="Find where the artifact fails in how it is EXPERIENCED: "
                "'objective' measures that ignore first-person experience, numbers "
                "that reify a lived complexity, false precision, anchoring, the gap "
                "between 'delivered' and 'understood'. Each accusation must name a "
                "concrete effect on real experience. No empty poetry.",
    ),
}


def all_roles() -> dict[str, Role]:
    return {**CORE_ROLES, **SPECIALIST_ROLES}
