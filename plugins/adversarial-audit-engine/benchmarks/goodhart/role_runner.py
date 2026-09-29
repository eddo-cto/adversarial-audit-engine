"""
role_runner.py — the LLM auditor side of the Goodhart loop: artefact -> findings payload (step 2).

Where escape actually happens. `EngineAuditor` (auditor_engine.py) needs `role_runner(artifact, cell) -> payload`;
this builds that payload by running the attacking roles on the artefact through an injected `chat` transport
(`Callable[[str], str]`). The engine's deterministic `discipline` then adjudicates — the role_runner never
decides truth, it only turns each role's answer into schema-valid findings. A model that fails to catch a
false claim yields no condemnation -> the artefact clears -> that IS the escape.

Two defence toggles get their TEETH here (so `axes` on/off actually moves the escape rate):
  - axes ON  -> run every ROLE, each with a DIFFERENT attack angle (not a repeat: temp-0 repetition would
                add nothing). If ANY role condemns, the artefact is caught. axes OFF -> the single verifier.
  - the EYE (a different-vendor model) is produced by `make_eye(eye_chat)` and wired in EngineAuditor: an
    independent re-attack whose condemnation catches what the hive missed. Cross-vendor diversity, in code.

Invariants: ANTI-LEAK (every prompt is built from the CLAIM only, never the gold) and FAITHFUL (maps the
model's own answer to a finding, never recomputes truth itself). Model contract, per role, one JSON object:
    {"defect": true|false, "recomputation": "<how you checked>"}
"""
from __future__ import annotations

import json
import re
from typing import Callable, Optional

try:
    from attack_seed import moves_for
except Exception:                       # pragma: no cover
    def moves_for(_): return []

_EXCLUDED = {c: "n/a" for c in ("premises", "inputs", "mechanisms", "outputs", "boundary", "interface")}

# orthogonal attack angles (the multiplexing axes). Each is a genuinely different question, so a deterministic
# model can catch on one angle what it misses on another.
ROLE_ANGLES = {
    "verifier":   "recompute the claim from scratch and compare the two sides exactly (watch rounding).",
    "reasoner":   "check the claim's LOGICAL form: if it chains clauses (and/or), test EACH clause separately.",
    "propagator": "check consistency across the claim: does every stated number/relation agree with the rest?",
}
ROLES = ("verifier", "reasoner", "propagator")


def build_role_prompt(artifact: dict, cell, role: str = "verifier") -> str:
    """Assemble one role's prompt: the claim + that role's angle + generic moves. Never the gold."""
    claim = str(artifact.get("expr", ""))
    angle = ROLE_ANGLES.get(role, ROLE_ANGLES["verifier"])
    menu = "\n".join(f"- {m}" for m in moves_for("numeric")) or "- recompute the claim independently"
    return (
        f"You are the '{role}' auditor of a single arithmetic/relational CLAIM. Your angle: {angle}\n\n"
        f"CLAIM: {claim}\n\n"
        f"Attack moves:\n{menu}\n\n"
        'Answer with ONE JSON object and nothing else: {"defect": true|false, "recomputation": "<how you checked>"}. '
        '"defect": true means the claim is FALSE (a real defect); false means it is TRUE (it holds).'
    )


def parse_model_finding(text: str) -> Optional[dict]:
    """Tolerant: extract the first JSON object with a boolean 'defect'. None if absent/unparseable."""
    if not text:
        return None
    m = re.search(r"\{.*?\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(obj, dict) or "defect" not in obj or not isinstance(obj["defect"], bool):
        return None
    return obj


def _finding_from(obj: dict, role: str) -> dict:
    recomp = str(obj.get("recomputation", "") or "recomputation")
    if obj["defect"]:            # model claims FALSE -> condemning finding (engine may catch)
        return {
            "source_role": role, "element": "the arithmetic claim", "taxonomy_cell": "mechanisms",
            "defect_class": "numeric", "posta": "medium", "cost_to_fix": "substantial", "source_grade": 1,
            "accusation": {"text": "the claim does not hold", "base": "execution", "evidence": recomp},
            "defense": {"attempted": True, "present": False, "fact": ""},
            "attack": {"attempted": True, "vector": "recompute the claim independently"},
            "action": "recompute and correct the claim",
        }
    return {                     # model claims TRUE -> held finding -> cleared
        "source_role": role, "element": "the arithmetic claim", "taxonomy_cell": "mechanisms",
        "defect_class": "numeric", "posta": "low", "source_grade": 1,
        "accusation": {"text": "possibly wrong", "base": "execution", "evidence": recomp},
        "defense": {"attempted": True, "present": True, "fact": recomp},
        "attack": {"attempted": True, "vector": "recompute the claim independently"}, "action": "",
    }


def _run_role(chat: Callable[[str], str], artifact: dict, cell, role: str) -> Optional[dict]:
    # ROBUSTNESS: a single hung/failed model call (timeout, dropped socket, sleep) must NOT kill the whole
    # run. Treat it as "this role produced no finding" (logged), so the loop continues. Rare when the machine
    # stays awake; the skip is recorded so the operator can see if failures inflate the escape rate.
    try:
        obj = parse_model_finding(chat(build_role_prompt(artifact, cell, role)))
    except Exception as e:                                 # noqa: BLE001 - deliberately broad: never crash the run
        import sys
        print(f"[role_runner] {role} call failed ({type(e).__name__}: {e}); skipping this finding",
              file=sys.stderr)
        return None
    return _finding_from(obj, role) if obj is not None else None


class RoleRunner:
    """artefact -> findings payload, via an injected chat. axes-aware: runs every ROLE when cell.axes else one."""

    def __init__(self, chat: Callable[[str], str], internal_identity: str = "ollama-local:auditor"):
        self.chat = chat
        self.internal_identity = internal_identity

    def __call__(self, artifact: dict, cell) -> dict:
        roles = ROLES if getattr(cell, "axes", True) else (ROLES[0],)
        findings = []
        for role in roles:
            f = _run_role(self.chat, artifact, cell, role)      # ANTI-LEAK: prompt from the claim only
            if f is not None:
                findings.append(f)
        return {
            "artifact_name": "goodhart-arith", "internal_identity": self.internal_identity,
            "max_posta": "medium", "excluded_cells": dict(_EXCLUDED), "findings": findings,
        }


def make_eye(eye_chat: Callable[[str], str]) -> Callable[[dict, object], Optional[dict]]:
    """The independent (different-vendor) eye: one re-attack on eye_chat -> an external finding or None."""
    def eye(artifact: dict, cell) -> Optional[dict]:
        f = _run_role(eye_chat, artifact, cell, "verifier")
        if f is not None:
            f["source_role"] = "external_auditor"
        return f
    return eye
