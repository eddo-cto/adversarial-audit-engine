"""
adapters.py — Cross-vendor LLMClient adapters (dependency-free, stdlib only).

This is the lever the meta-governor keeps asking for: real independence comes
from a DIFFERENT vendor running the external-auditor / governor, not from a
second Claude instance (the F-07 limit). These adapters let any role run on a
different model — including FREE options — so the independence level rises from
1 (same instance) to 3 (different vendor).

No third-party packages: both clients use urllib, so they run anywhere.

Free / low-cost endpoints that speak the OpenAI-compatible protocol (use
OpenAICompatibleClient with the right base_url):
  - Ollama (local, free):        base_url="http://localhost:11434/v1", api_key="ollama"
  - Groq (free tier):            base_url="https://api.groq.com/openai/v1"
  - OpenRouter (free models):    base_url="https://openrouter.ai/api/v1"  (model "...:free")
  - Together / others:           their OpenAI-compatible base_url
GeminiClient uses Google's free-tier generativeLanguage REST API.

independence_level_between() computes the achieved independence from two
identities, so the orchestrator can stamp the ledger honestly.
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error

from .llm import LLMClient
from .schema import IndependenceLevel


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class OpenAICompatibleClient(LLMClient):
    """Works with any OpenAI-/chat-completions-compatible endpoint: OpenAI,
    Groq, OpenRouter, Together, Ollama (local), etc. The `vendor` label feeds
    the independence check, so set it to the real provider."""

    name = "openai-compatible"

    def __init__(self, model: str, base_url: str = "https://api.openai.com/v1",
                 api_key: str | None = None, vendor: str | None = None,
                 env_key: str = "OPENAI_API_KEY"):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get(env_key) or "none"
        self.vendor = vendor or _vendor_from_url(base_url)
        self.identity = f"{self.vendor}:{model}"

    def complete(self, system: str, user: str, *, max_tokens: int = 4096,
                 temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.api_key}"}
        try:
            data = _post_json(f"{self.base_url}/chat/completions", payload, headers)
        except urllib.error.URLError as e:
            raise RuntimeError(f"{self.identity} request failed: {e}") from e
        return data["choices"][0]["message"]["content"]


class GeminiClient(LLMClient):
    """Google Gemini via the free-tier generativeLanguage REST API."""

    name = "gemini"

    def __init__(self, model: str = "gemini-1.5-flash", api_key: str | None = None,
                 env_key: str = "GEMINI_API_KEY"):
        self.model = model
        self.api_key = api_key or os.environ.get(env_key)
        if not self.api_key:
            raise RuntimeError(f"Set {env_key} or pass api_key=...")
        self.identity = f"google:{model}"

    def complete(self, system: str, user: str, *, max_tokens: int = 4096,
                 temperature: float = 0.2) -> str:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.api_key}")
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": max_tokens,
                                 "temperature": temperature},
        }
        try:
            data = _post_json(url, payload, {"Content-Type": "application/json"})
        except urllib.error.URLError as e:
            raise RuntimeError(f"{self.identity} request failed: {e}") from e
        return data["candidates"][0]["content"]["parts"][0]["text"]


def _vendor_from_url(base_url: str) -> str:
    u = base_url.lower()
    for key, name in (("openai.com", "openai"), ("groq", "groq"),
                      ("perplexity", "perplexity"),
                      ("openrouter", "openrouter"), ("together", "together"),
                      ("localhost", "ollama-local"), ("127.0.0.1", "ollama-local"),
                      ("anthropic", "anthropic")):
        if key in u:
            return name
    return "openai-compatible"


def independence_level_between(identity_a: str, identity_b: str | None) -> IndependenceLevel:
    """Honest independence level from two role identities.
       same string              -> 1 (not independent)
       same vendor, diff model  -> 2
       different vendor         -> 3
       (human review remains level 4 and is set out-of-band.)"""
    if not identity_b or identity_a == identity_b:
        return IndependenceLevel.SAME_INSTANCE_ROLES
    va = identity_a.split(":", 1)[0]
    vb = identity_b.split(":", 1)[0]
    if va == vb:
        return IndependenceLevel.DIFFERENT_MODEL_SAME_VENDOR
    return IndependenceLevel.DIFFERENT_MODEL_DIFFERENT_VENDOR
