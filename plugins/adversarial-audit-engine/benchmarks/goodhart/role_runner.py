"""
role_runner.py — the LLM auditor side of the Goodhart loop: artefact -> findings payload (step 2).

Where escape actually happens. `EngineAuditor` (auditor_engine.py) needs `role_runner(artifact, cell) -> payload`;
this builds that payload by running the attacking roles on the artefact through an injected `chat` transport
(`Callable[[str], str]`). The engine's deterministic `discipline` then adjudicates the payload — so the
role_runner NEVER decides truth, it only faithfully turns the model's judgement into schema-valid findings.
A model that fails to catch a false claim yields no condemnation -> the artefact clears -> that IS the escape.

Invariants in code:
  - ANTI-LEAK: the role_runner is handed ONLY the artefact (the claim). It never receives, reads, or embeds
    the gold label. The built prompt is asserted (in tests) to contain the claim but not any gold verdict.
  - FAITHFUL, NOT DECIDING: it maps the model's own answer to a finding; it does not recompute truth itself
    (that would make the auditor secretly competent and hide the model's real escape behaviour).

Contract with the model (kept minimal and robust for small local models): the role is asked to attack the
claim and answer with a single JSON object:
    {"defect": true|false, "recomputation": "<how you checked>"}
`defect:true`  -> a condemning numeric finding (execution base, defense attempted & failed) -> engine may CATCH.
`defect:false` -> a held finding (defense present, fact = the model's recomputation)        -> CLEARED.
Unparseable / empty answer -> no finding -> CLEARED (a model that says nothing catches nothing).
"""
from __future__ import annotations

import json
import re
from typing import Callable, Optional

try:
    from attack_seed import moves_for
except Exception:                       # pragma: no cover - only if imported oddly
    def moves_for(_): return []

_EXCLUDED = {c: "n/a" for c in ("premises", "inputs", "mechanisms", "outputs", "boundary", "interface")}


def build_role_prompt(artifact: dict, cell) -> str:
    """Assemble the numeric-verifier prompt: the claim + a menu of generic attack moves. Never the gold."""
    claim = str(artifact.get("expr", ""))
    menu = "\n".join(f"- {m}" for m in moves_for("numeric")) or "- recompute the claim independently"
    return (
        "You are a numeric verifier auditing a single arithmetic/relational CLAIM. Attack it: recompute it "
        "independently and decide whether it is TRUE or FALSE.\n\n"
        f"CLAIM: {claim}\n\n"
        f"Attack moves you may use:\n{menu}\n\n"
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


def _finding_from(obj: dict) -> dict:
    recomp = str(obj.get("recomputation", "") or "recomputation")
    if obj["defect"]:            # model claims FALSE -> condemning finding (engine may catch)
        return {
            "source_role": "verifier", "element": "the arithmetic claim", "taxonomy_cell": "mechanisms",
            "defect_class": "numeric", "posta": "medium", "cost_to_fix": "substantial", "source_grade": 1,
            "accusation": {"text": "the claim does not hold", "base": "execution", "evidence": recomp},
            "defense": {"attempted": True, "present": False, "fact": ""},
            "attack": {"attempted": True, "vector": "recompute the claim independently"},
            "action": "recompute and correct the claim",
        }
    # model claims TRUE -> held finding (defense present) -> cleared
    return {
        "source_role": "verifier", "element": "the arithmetic claim", "taxonomy_cell": "mechanisms",
        "defect_class": "numeric", "posta": "low", "source_grade": 1,
        "accusation": {"text": "possibly wrong", "base": "execution", "evidence": recomp},
        "defense": {"attempted": True, "present": True, "fact": recomp},
        "attack": {"attempted": True, "vector": "recompute the claim independently"}, "action": "",
    }


class RoleRunner:
    """artefact -> findings payload, via an injected chat transport. Matches EngineAuditor's role_runner."""

    def __init__(self, chat: Callable[[str], str], internal_identity: str = "ollama-local:auditor"):
        self.chat = chat
        self.internal_identity = internal_identity

    def __call__(self, artifact: dict, cell) -> dict:
        prompt = build_role_prompt(artifact, cell)          # ANTI-LEAK: prompt built from the claim only
        answer = self.chat(prompt)
        obj = parse_model_finding(answer)
        findings = [_finding_from(obj)] if obj is not None else []   # no parse -> nothing caught -> cleared
        return {
            "artifact_name": "goodhart-arith", "internal_identity": self.internal_identity,
            "max_posta": "medium", "excluded_cells": dict(_EXCLUDED), "findings": findings,
        }
