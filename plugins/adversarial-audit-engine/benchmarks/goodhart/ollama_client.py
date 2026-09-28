"""
ollama_client.py — the ONLY live piece: a chat transport over a local Ollama server.

stdlib only (urllib). `make_chat(model)` returns a `chat(prompt) -> str` closure that POSTs to the local
Ollama /api/chat endpoint and returns the assistant text. Deterministic settings for "modalità scienza":
temperature 0 and a fixed seed by default. The HTTP call itself is the only thing that cannot be unit-tested
in the sandbox; the request assembly and response parsing go through a `_post` seam that tests monkeypatch.

Nothing else in benchmarks/goodhart imports this — the forger, gold, harness, analysis and role_runner all
take an injected `chat`, so the whole apparatus stays testable without a network or a model.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Callable

DEFAULT_HOST = "http://localhost:11434"


def _post(url: str, payload: dict, timeout: float = 120.0) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:      # noqa: S310 - local, trusted host
        return json.loads(resp.read().decode("utf-8"))


def parse_chat_response(obj: dict) -> str:
    """Extract the assistant text from an Ollama /api/chat response (non-streaming)."""
    msg = obj.get("message") or {}
    return str(msg.get("content", "") or "")


def make_chat(model: str, host: str = DEFAULT_HOST, seed: int = 0, temperature: float = 0.0,
              timeout: float = 120.0, post: Callable[[str, dict, float], dict] = _post) -> Callable[[str], str]:
    """Return chat(prompt)->str hitting <host>/api/chat with the given model. `post` is a seam for tests."""
    url = f"{host.rstrip('/')}/api/chat"

    def chat(prompt: str) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature, "seed": seed},
        }
        return parse_chat_response(post(url, payload, timeout))

    return chat
