# A free level-3 independent eye (no paid API)

The engine's whole value is **independence**, yet every real run so far has been **level 1** (one instance
wearing many role-hats). The fix — a *different-vendor* eye — is what raises a run to level 3 and turns
agreement into evidence instead of a shared-prior artifact. That eye does **not** require a paid API: the
existing `OpenAICompatibleClient` adapter already talks to free endpoints. Nothing here changes the paid
path, which stays available for clients who have API budgets (same adapter, different `base_url` + key).

## Recommended: a local open-weight model via Ollama ($0 marginal)

1. Install Ollama (`https://ollama.com`) and pull a model, e.g. `ollama pull llama3.1:8b`
   (or the strongest your hardware allows: `qwen2.5`, `deepseek-r1`, …).
2. Point the adapter at the local OpenAI-compatible endpoint:

```python
from aae.adapters import OpenAICompatibleClient
eye = OpenAICompatibleClient(
    model="llama3.1:8b",
    base_url="http://localhost:11434/v1",   # Ollama, local
    api_key="ollama",                        # any non-empty string
)
# eye.identity == "ollama-local:llama3.1:8b"
# independence_level_between("anthropic:claude-...", eye.identity) == 3  (different vendor)
```

Use `eye` as the **external-auditor / governor** client. The vendor label is derived from the URL and
feeds the attested identity, so the run is credited at **level 3** by the same rule as a paid vendor —
`CROSS_MODEL_REVIEWED`, reliability up, still **not** validated (only a human closes the loop).

## No-hardware alternatives (free tiers, same adapter)

```python
# Groq free tier
OpenAICompatibleClient(model="llama-3.1-70b-versatile",
                       base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY)
# OpenRouter free models (model id ends in ":free")
OpenAICompatibleClient(model="meta-llama/llama-3.1-8b-instruct:free",
                       base_url="https://openrouter.ai/api/v1", api_key=OR_KEY)
```

These are APIs but **free within limits** — the objection is cost, not the mechanism, and it is the very
adapter kept for paying clients.

## Honest caveats (read before trusting the level-3 badge)

- **Capability gap.** A weaker independent model makes its *agreement* worth less (the capability↔
  independence confound of the system paper's §6). Its *disagreement*, though, is real signal — a
  different-family model does not share Claude's specific blind spots, which is exactly the point of the
  independence axis. Use the strongest model you can.
- **Free tiers are volatile.** Rate limits and ToS change; do not build a client-facing SLA on a free tier.
- **Human copy-paste is *claimed*, not *attested*.** Pasting the artifact into a different vendor's chat
  UI is genuinely different-vendor, but the engine credits only what the *calling adapter* attests
  (`I2`): a hand-carried result is `CROSS_MODEL_CLAIMED`, independence **not** credited, unless an operator
  signs it (an attestation extension, not yet built). Prefer the adapter routes above.
- **Still never `VALIDATED`.** Level 3 improves reliability; level 4 (the human) remains the only closer.
