"""
independence_ledger.py — the standing independence report, emitted per run.

This is a RULE, not a new layer. The engine already computes independence
*pairwise* (`adapters.independence_level_between`) and gates the final state on
one external identity (`gates.evaluate_completion`). What was missing is a
first-class artifact that aggregates ALL the identities that actually
participated in a run — every auditor, the adjudicator, an optional external
eye — and states, in one place:

  * the achieved independence level across the whole set (not just one pair);
  * whether any observed agreement is INTRA-nature or INTER-nature;
  * the verdict ceiling that level implies (never VALIDATED on internal grounds);
  * the rho caveat, in plain words.

Why this matters (2026 context): the field is discovering that LLM-judge
agreement is "reliable without being valid" — high test-retest coexists with
strong bias, and same-family multi-agent setups amplify rather than cancel
shared priors. Almost every ensemble/debate tool ASSERTS independence; none
EMIT it. Emitting it, every run, is the honest differentiator the engine
already earns and no neighbour reports.

"Nature" = model family / vendor. Same vendor with a different model raises the
level a little (2) but is still one nature (shared priors). INTER-nature
requires a different vendor (level 3). Only a human eye reaches level 4.

Pure standard library. No new capability.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .adapters import independence_level_between
from .schema import IndependenceLevel


def _vendor(identity: str) -> str:
    return identity.split(":", 1)[0].strip().lower()


def _is_human(identity: str | None) -> bool:
    return bool(identity) and identity.strip().lower().startswith("human")


@dataclass(frozen=True)
class IndependenceLedger:
    """The emitted independence report for one run."""
    participants: tuple           # tuple[(identity, role)]
    natures: tuple                # distinct machine vendors, sorted
    achieved_level: IndependenceLevel
    scope: str                    # "single" | "intra-nature" | "inter-nature" | "human-closed"
    ceiling: str                  # max reachable verdict state
    caveat: str

    def to_dict(self) -> dict:
        return {
            "participants": [{"identity": i, "role": r} for i, r in self.participants],
            "natures": list(self.natures),
            "achieved_level": int(self.achieved_level),
            "achieved_level_name": self.achieved_level.name,
            "scope": self.scope,
            "ceiling": self.ceiling,
            "caveat": self.caveat,
        }

    def render(self) -> str:
        lines = ["INDEPENDENCE LEDGER",
                 f"  level    : {int(self.achieved_level)} ({self.achieved_level.name})",
                 f"  scope    : {self.scope}",
                 f"  natures  : {', '.join(self.natures) or '(none)'}",
                 f"  ceiling  : {self.ceiling}",
                 "  roles    :"]
        for identity, role in self.participants:
            lines.append(f"    - {role}: {identity}")
        lines.append(f"  caveat   : {self.caveat}")
        return "\n".join(lines)


def build_independence_ledger(*, auditors: list[str],
                              adjudicator: str | None = None,
                              external: str | None = None) -> IndependenceLedger:
    """Aggregate every participating identity into one honest independence report.

    `auditors`   : identities ("vendor:model") that audited the artifact.
    `adjudicator`: identity that adjudicated landings, if separate.
    `external`   : an external reviewer identity; "human:*" closes to level 4.
    """
    participants: list[tuple[str, str]] = []
    for a in auditors:
        participants.append((a, "auditor"))
    if adjudicator:
        participants.append((adjudicator, "adjudicator"))
    if external:
        participants.append((external, "external"))

    human_present = _is_human(external) or any(_is_human(i) for i, _ in participants)

    machine = [i for i, _ in participants if not _is_human(i)]
    natures = tuple(sorted({_vendor(i) for i in machine}))

    # achieved level = the best independence actually present among machine pairs
    level = IndependenceLevel.SAME_INSTANCE_ROLES
    for i in range(len(machine)):
        for j in range(i + 1, len(machine)):
            level = max(level, independence_level_between(machine[i], machine[j]))
    if human_present:
        level = IndependenceLevel.HUMAN_DOMAIN_EXPERT

    if human_present:
        scope = "human-closed"
        ceiling = "VALIDATED"
        caveat = ("Closed by a human external eye (level 4): the only identity of a "
                  "different nature that can validate.")
    elif level >= IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR:
        scope = "inter-nature"
        ceiling = "CROSS_MODEL_REVIEWED"
        caveat = ("Inter-nature agreement observed (≥2 vendors): agreement here is "
                  "not a shared-prior artifact. Still a machine ceiling — NOT "
                  "VALIDATED without a human eye.")
    elif level == IndependenceLevel.DIFFERENT_MODEL_SAME_VENDOR:
        scope = "intra-nature"
        ceiling = "EXTERNAL_REVIEW_PENDING"
        caveat = ("Same vendor, different model: one nature. Agreement cannot be "
                  "read as independence (shared priors, ρ→1). A different vendor or "
                  "a human eye is required to lift the ceiling.")
    else:
        scope = "single"
        ceiling = "EXTERNAL_REVIEW_PENDING"
        caveat = ("Single nature/instance: agreement among roles is NOT independence "
                  "(ρ→1). An external identity of a different nature is required.")

    return IndependenceLedger(
        participants=tuple(participants),
        natures=natures,
        achieved_level=level,
        scope=scope,
        ceiling=ceiling,
        caveat=caveat,
    )
