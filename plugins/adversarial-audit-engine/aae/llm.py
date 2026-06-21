"""
llm.py — LLM client abstraction.

The engine is software around a semantic core. That core is an LLM. We keep
it behind a small interface so the deterministic scaffold (orchestration,
gates, schema, metrics) is testable WITHOUT network or API keys, and so the
backend is pluggable.

Three implementations:
  - LLMClient        : the interface every backend implements.
  - MockLLMClient    : deterministic, offline. Returns canned/heuristic JSON.
                       Used for smoke tests and CI. No network, no keys.
  - AnthropicLLMClient: real backend (optional; requires `anthropic` + key).

Roles ask the LLM for JSON. `complete_json` enforces that and parses it.
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class LLMMessage:
    role: str        # "system" | "user"
    content: str


class LLMClient(ABC):
    """Minimal interface. A backend must be able to answer a prompt and,
    on request, return parseable JSON."""

    name: str = "abstract"
    identity: str = "abstract"   # used by the independence check (gates.py)

    @abstractmethod
    def complete(self, system: str, user: str, *, max_tokens: int = 4096,
                 temperature: float = 0.2) -> str:
        ...

    def complete_json(self, system: str, user: str, *, max_tokens: int = 4096,
                      temperature: float = 0.2) -> Any:
        """Call complete() and parse the first JSON object/array found.
        Raises ValueError if no JSON can be parsed."""
        raw = self.complete(
            system + "\n\nRespond with ONLY valid JSON, no prose, no code fences.",
            user, max_tokens=max_tokens, temperature=temperature,
        )
        return _extract_json(raw)


def _extract_json(raw: str) -> Any:
    raw = raw.strip()
    # strip code fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # last resort: grab the largest {...} or [...] span
        for opener, closer in (("{", "}"), ("[", "]")):
            start = raw.find(opener)
            end = raw.rfind(closer)
            if start != -1 and end > start:
                try:
                    return json.loads(raw[start:end + 1])
                except json.JSONDecodeError:
                    continue
    raise ValueError(f"Could not parse JSON from model output:\n{raw[:500]}")


# --------------------------------------------------------------------------
# Mock backend — offline, deterministic
# --------------------------------------------------------------------------

class MockLLMClient(LLMClient):
    """Offline backend for testing the scaffold. It does NOT reason; it returns
    structurally valid, role-appropriate stubs so the orchestration, gates,
    state machine, and metrics can be exercised end to end without a network."""

    name = "mock"
    identity = "mock-deterministic-v1"

    def complete(self, system: str, user: str, *, max_tokens: int = 4096,
                 temperature: float = 0.2) -> str:
        s = system.lower()
        # Use distinctive markers, not loose keywords: DEFENSE_GATE mentions the
        # "oracle dossier", so a bare "oracle" substring leaks into every role.
        if "answering a single targeted" in s:          # oracle on-demand query
            return "MOCK FACT: the canonical value/mechanism would appear here."
        if "research oracle" in s:                       # oracle dossier build
            return json.dumps({
                "dossier": "MOCK DOSSIER: domain facts and mechanisms here.",
                "themes": ["facts", "mechanisms"],
                "sources": ["https://example.org/mock"],
            })
        if "triage step" in s:
            return json.dumps({
                "dimensions_present": ["premises", "inputs", "mechanisms",
                                        "outputs", "boundary", "interface"],
                "deploy_roles": [],
                "excluded": {
                    "epistemologist": "no validation/statistics claims",
                    "logician": "no formal-structure surface",
                    "ethicist": "no impact on persons in this artifact",
                    "phenomenologist": "no lived-experience surface",
                },
            })
        if "consequence propagator" in s:                # the propagator role
            return json.dumps({"findings": [{
                "id": "PR-MOCK-1",
                "element": "mock premise vs mock guarantee",
                "taxonomy_cell": "mechanisms",
                "defect_class": "non_local_mechanical",
                "posta": "medium",
                "accusation": {"text": "mock non-local accusation",
                               "base": "reading", "evidence": "mock",
                               "sections": ["§2", "§7"]},
                "defense": {"attempted": True, "present": False, "fact": None},
                "cost_to_fix": "medium",
                "action": "mock corrective action",
                "declared_limit": "mock: external validation pending",
                "sources": []}]})
        if "abductive analysis" in s:                    # triadic abductive pass
            return json.dumps({"rivals": [{
                "id": "AB-MOCK-1",
                "claim": "mock rival explanation of the result",
                "anchored_to": "mock dossier mechanism",
                "discriminating_test": "mock test that would confirm/refute",
                "strength_vs_authors": "comparable"}]})
        if "deductive analysis" in s or "inductive analysis" in s:
            return json.dumps({"findings": [{
                "id": "TR-MOCK-1", "element": "mock inferential claim",
                "taxonomy_cell": "mechanisms",
                "accusation": {"text": "mock", "base": "reading",
                               "evidence": "mock", "sections": ["§1"]},
                "defense": {"attempted": True, "present": False, "fact": None},
                "cost_to_fix": "medium", "action": "mock",
                "declared_limit": "mock", "severity": "media"}]})
        if "meta-epistemic governor" in s:               # 5th layer
            return json.dumps({"checks": [
                {"dimension": "confound",
                 "finding": "mock: whoever supplied the facts may have supplied "
                            "the answers (oracle-leakage)", "severity": "warning"}],
                "residue_to_human": "mock: external eye must confirm coverage of "
                                    "unknown-unknowns"})
        if "root-cause clustering" in s:                 # deep-causal kernel 1
            return json.dumps({"roots": [{
                "id": "CR-A", "name": "mock root cause",
                "description": "mock deep premise",
                "generated_findings": ["finding 1", "finding 2"]}]})
        if "chiasm cross-validation" in s:               # deep-causal kernel 2
            return json.dumps({"predictions": [
                {"id": "P-1", "from_root": "CR-A",
                 "predicted_symptom": "mock predicted defect",
                 "location": "§x", "why_follows": "mock",
                 "discriminating_test": "mock test"},
                {"id": "P-2", "from_root": "CR-A",
                 "predicted_symptom": "mock speculation (no test)",
                 "location": "", "why_follows": "", "discriminating_test": ""}]})
        if "scenario diffusion" in s:                    # deep-causal kernel 3
            return json.dumps({"scenarios": [
                {"id": "S-1", "mechanism": "mock reachable falsifiable scenario",
                 "reachable": True, "falsifiable": True,
                 "discriminating_test": "mock test"},
                {"id": "S-2", "mechanism": "mock non-falsifiable scenario",
                 "reachable": True, "falsifiable": False,
                 "discriminating_test": ""}]})
        if "market scout" in s:                          # discovery scan
            u = user.lower()
            # shared domain 'insurance' across primitives -> creates an
            # intersection; plus a unique domain; plus one gated-out candidate.
            uniq = "incident-rca" if "abduction" in u else (
                "compliance" if "consequence" in u else (
                "patent" if "cause_of_absence" in u else "pharma-dossier"))
            return json.dumps({"candidates": [
                {"name": f"mock-{uniq}", "domain": uniq,
                 "capability_fit": 5, "under_served": 4, "wtp": 4,
                 "defensibility": 3, "low_liability": 4, "low_friction": 4,
                 "gate_legal": True, "gate_value_without_validation": True,
                 "absence_label": "contingent_documented",
                 "unexpected_correlation": f"mock corr in {uniq}",
                 "sources": ["https://example.org/mock"]},
                {"name": "mock-insurance", "domain": "insurance",
                 "capability_fit": 4, "under_served": 4, "wtp": 5,
                 "defensibility": 4, "low_liability": 3, "low_friction": 2,
                 "gate_legal": True, "gate_value_without_validation": True,
                 "absence_label": "contingent_documented",
                 "unexpected_correlation": "", "sources": []},
                {"name": "mock-gated", "domain": "regulated-x",
                 "capability_fit": 5, "under_served": 5, "wtp": 5,
                 "defensibility": 5, "low_liability": 1, "low_friction": 1,
                 "gate_legal": True, "gate_value_without_validation": False,
                 "absence_label": "known_structural",
                 "unexpected_correlation": "", "sources": []}]})
        if "cause-of-absence" in s:                       # construens layer
            return json.dumps({
                "causes": [{
                    "id": "C-MOCK-1", "area": "market",
                    "optimistic_hypothesis": "absence is a removable opportunity",
                    "structural_attack": "absence is structural (mock)",
                    "label": "contingent_documented", "confidence": 0.6}],
                "surviving_fragments": [{
                    "description": "mock surviving reduced form",
                    "constraints": ["mock constraint"], "confidence": 0.5}],
                "honest_null": False})
        if "arbiter" in s or "arbitro" in s:
            return json.dumps({"decisions": []})
        # default: a single generic finding from an attacker role
        return json.dumps({"findings": [{
            "id": "MOCK-1",
            "element": "mock element",
            "taxonomy_cell": "mechanisms",
            "defect_class": "idiosyncratic_local",
            "posta": "low",
            "accusation": {"text": "mock accusation", "base": "reading",
                           "evidence": "mock", "sections": ["§1"]},
            "defense": {"attempted": True, "present": False, "fact": None},
            "cost_to_fix": "low",
            "action": "mock fix",
            "declared_limit": "mock limit",
            "sources": []}]})


# --------------------------------------------------------------------------
# Anthropic backend — optional, real
# --------------------------------------------------------------------------

class AnthropicLLMClient(LLMClient):
    """Real backend. Requires `pip install anthropic` and ANTHROPIC_API_KEY.
    `identity` encodes model+vendor so the independence check can tell two
    reviewers apart (a different model = a different identity)."""

    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-4-6",
                 api_key: Optional[str] = None):
        try:
            import anthropic  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "AnthropicLLMClient requires the 'anthropic' package: "
                "pip install anthropic"
            ) from e
        import anthropic
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("Set ANTHROPIC_API_KEY or pass api_key=...")
        self._client = anthropic.Anthropic(api_key=key)
        self.model = model
        self.identity = f"anthropic:{model}"

    def complete(self, system: str, user: str, *, max_tokens: int = 4096,
                 temperature: float = 0.2) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in resp.content
                       if getattr(block, "type", None) == "text")
