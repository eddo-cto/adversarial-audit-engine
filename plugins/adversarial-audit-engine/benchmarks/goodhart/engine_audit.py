"""
engine_audit.py — the FAITHFUL auditor: real defense-first role contract on a (local) model -> discipline.

This replaces the strawman role_runner for the general-v3 operating-point experiment. The decisive fix over
the toy run: the DEFENSE IS DECIDED BY THE MODEL, not hard-coded. Each role must first attempt the claim's
STRONGEST defense; a condemnation stands only if that defense fails. So a TRUE claim -> model finds the defence
holds -> ARTIFACT_HOLDS -> not condemned -> low false-positive. That is exactly the engine's defense-gate,
restored. `discipline` then adjudicates with all its gates (grounding, source-grade, Type-I, governor).

The model call is an injected `chat` transport, so the assembly + mapping stay unit-testable without any LLM.
Anti-leak: the prompt is built from the CLAIM only; the gold label is never shown.
"""
from __future__ import annotations

import json
import re
from typing import Callable, Optional

_EXCLUDED = {c: "n/a" for c in ("premises", "inputs", "mechanisms", "outputs", "boundary", "interface")}

# general-v3 class_hint -> (engine defect_class, accusation base). date has no class -> lookup.
_MAP = {
    "numeric": ("numeric", "execution"),
    "date": ("lookup", "reading"),
    "lookup": ("lookup", "reading"),
    "epistemic": ("epistemic", "domain_knowledge"),
    "non_local_mechanical": ("non_local_mechanical", "execution"),
    "non_local_conceptual_documented": ("non_local_conceptual_documented", "reading"),
}

ROLE_ANGLES = {
    "verifier":   "recompute/verify the claim from first principles.",
    "reasoner":   "check the claim's logical form and any hidden assumption.",
    "propagator": "check whether the claim is consistent with the reference it depends on.",
}
ROLES = ("verifier", "reasoner", "propagator")


def build_audit_prompt(artifact: str, role: str = "verifier") -> str:
    """Defense-first contract (faithful to roles.py): attempt the STRONGEST defence, condemn only if it fails."""
    angle = ROLE_ANGLES.get(role, ROLE_ANGLES["verifier"])
    return (
        f"You are the '{role}' auditor of a single factual CLAIM. Your angle: {angle}\n"
        "FIRST attempt the claim's STRONGEST defence — try hard to show it could be CORRECT (recompute, recall "
        "the rule, check the source). Condemn ONLY if that defence genuinely fails.\n\n"
        f"CLAIM: {artifact}\n\n"
        'Answer with ONE JSON object and nothing else: '
        '{"defense_holds": true|false, "fact": "<the verifying fact if it holds>", "defect": true|false}. '
        'defense_holds=true means the claim is actually correct (defended); defect=true ONLY if the defence '
        'fails and the claim is really wrong.'
    )


def parse_audit(text: str) -> Optional[dict]:
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(obj, dict) or "defect" not in obj:
        return None
    return obj


def _finding(obj: dict, role: str, class_hint: str) -> Optional[dict]:
    dc, base = _MAP.get(class_hint, ("epistemic", "domain_knowledge"))
    holds = bool(obj.get("defense_holds", False))
    defect = bool(obj.get("defect", False))
    fact = str(obj.get("fact", "") or "")
    secs = ["the claim", "the referenced fact/computation"]      # >=2 for non-local classes
    common = {"source_role": role, "element": "the claim", "taxonomy_cell": "mechanisms",
              "defect_class": dc, "posta": "medium", "source_grade": 1,
              "attack": {"attempted": True, "vector": "attempt the strongest defence, then recompute"}}
    if holds or not defect:
        # the model defended the claim (or found no defect) -> HELD (cleared)
        return {**common, "posta": "low",
                "accusation": {"text": "possibly wrong", "base": base, "evidence": fact or "checked",
                               "sections": secs},
                "defense": {"attempted": True, "present": True, "fact": fact or "defence holds"}, "action": ""}
    # defence genuinely failed -> condemnation (defense-gate satisfied: a real attempt was made and failed)
    return {**common, "cost_to_fix": "substantial",
            "accusation": {"text": "the claim does not hold", "base": base,
                           "evidence": str(obj.get("fact", "") or "recomputation shows it fails"), "sections": secs},
            "defense": {"attempted": True, "present": False, "fact": ""},
            "action": "correct the claim at the source"}


def _run_role(chat, artifact, role, class_hint) -> Optional[dict]:
    try:
        obj = parse_audit(chat(build_audit_prompt(artifact, role)))
    except Exception as e:                               # never crash a run on one hung call
        import sys
        print(f"[engine_audit] {role} failed ({type(e).__name__}); skipped", file=sys.stderr)
        return None
    return _finding(obj, role, class_hint) if obj is not None else None


class RealRoleRunner:
    """artefact(text)+class_hint -> findings payload via the real defense-first contract. axes-aware."""

    def __init__(self, chat: Callable[[str], str], internal_identity: str = "ollama-local:auditor"):
        self.chat = chat
        self.internal_identity = internal_identity

    def __call__(self, item: dict, cell) -> dict:
        art = item["artifact"]; hint = item.get("class_hint", "epistemic")
        roles = ROLES if getattr(cell, "axes", True) else (ROLES[0],)
        findings = [f for r in roles if (f := _run_role(self.chat, art, r, hint)) is not None]
        return {"artifact_name": item.get("id", "item"), "internal_identity": self.internal_identity,
                "max_posta": "medium", "excluded_cells": dict(_EXCLUDED), "findings": findings}


def make_eye(eye_chat: Callable[[str], str]) -> Callable[[dict, object], Optional[dict]]:
    """Independent different-vendor eye: one defense-first re-audit -> external finding or None."""
    def eye(item: dict, cell) -> Optional[dict]:
        f = _run_role(eye_chat, item["artifact"], "verifier", item.get("class_hint", "epistemic"))
        if f is not None:
            f["source_role"] = "external_auditor"
        return f
    return eye
