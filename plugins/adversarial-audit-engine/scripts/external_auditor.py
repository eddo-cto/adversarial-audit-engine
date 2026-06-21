#!/usr/bin/env python3
"""
external_auditor.py — the cross-vendor independent eye, as a runnable tool.

This is the wiring that finally raises independence above the F-07 limit: it
runs the external-auditor role on a DIFFERENT vendor's model and returns its
findings + its identity, so run_core can stamp the ledger with the true
independence level (3 if a different vendor actually ran it).

Backends (pick a FREE one for real independence at no cost):
  --backend mock                         (offline plumbing test)
  --backend openai-compat --model llama-3.1-8b-instant \
      --base-url https://api.groq.com/openai/v1 --env-key GROQ_API_KEY   (Groq free tier)
  --backend openai-compat --model llama3 \
      --base-url http://localhost:11434/v1 --env-key OLLAMA            (Ollama, local, free)
  --backend gemini --model gemini-1.5-flash                              (Gemini free tier)

Input: artifact path (--artifact) and optional internal findings (--findings)
to re-attack. Output (stdout or --out): {"external_identity": "...",
"findings": [ ... source_role="external-auditor" ... ]} — ready to merge into
run_core's payload as external_identity + appended findings.
"""
from __future__ import annotations
import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..")))  # -> aae parent
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..")))  # bundled aae at plugin root

from aae.llm import MockLLMClient


EXTERNAL_AUDITOR_SYS = (
    "You are the INDEPENDENT EXTERNAL AUDITOR of an artifact already audited by "
    "another team. Re-attack it from a separate perspective: find what the "
    "internal hive missed and contest its verdicts. Hostile, no justificationism, "
    "no rubber-stamping. Defense-gate: attempt the strongest defense before "
    "condemning; a base of 'pattern' may flag but not condemn. "
    "Return JSON {\"findings\":[{\"element\",\"taxonomy_cell\",\"defect_class\","
    "\"posta\",\"accusation\":{\"text\",\"base\",\"evidence\",\"sections\"},"
    "\"defense\":{\"attempted\",\"present\",\"fact\"},\"cost_to_fix\",\"action\","
    "\"declared_limit\",\"severity\"}]}. defect_class in [lookup,numeric,"
    "idiosyncratic_local,non_local_mechanical,non_local_conceptual_documented,"
    "non_local_conceptual_novel,epistemic,ethical,phenomenological]. "
    "State plainly which model/vendor is running you (it determines the "
    "independence level the governor will assign)."
)


def build_client(args):
    if args.backend == "mock":
        return MockLLMClient()
    if args.backend == "openai-compat":
        from aae.adapters import OpenAICompatibleClient
        return OpenAICompatibleClient(args.model, base_url=args.base_url,
                                      vendor=args.vendor, env_key=args.env_key)
    if args.backend == "gemini":
        from aae.adapters import GeminiClient
        return GeminiClient(args.model or "gemini-1.5-flash")
    raise SystemExit(f"unknown backend: {args.backend}")


def main() -> int:
    p = argparse.ArgumentParser(prog="external_auditor")
    p.add_argument("--artifact", required=True)
    p.add_argument("--findings", default=None, help="internal findings JSON to re-attack")
    p.add_argument("--backend", default="mock",
                   choices=["mock", "openai-compat", "gemini"])
    p.add_argument("--model", default="")
    p.add_argument("--base-url", default="https://api.openai.com/v1")
    p.add_argument("--vendor", default=None)
    p.add_argument("--env-key", default="OPENAI_API_KEY")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    artifact = open(args.artifact, encoding="utf-8").read()
    user = "ARTIFACT:\n" + artifact
    if args.findings:
        internal = open(args.findings, encoding="utf-8").read()
        user += "\n\nINTERNAL FINDINGS (re-attack / contest these):\n" + internal

    client = build_client(args)
    try:
        data = client.complete_json(EXTERNAL_AUDITOR_SYS, user, max_tokens=3072)
    except ValueError:
        data = {"findings": []}
    findings = data.get("findings", []) if isinstance(data, dict) else []
    for f in findings:
        f["source_role"] = "external-auditor"

    out = {"external_identity": client.identity, "findings": findings}
    text = json.dumps(out, indent=2, ensure_ascii=False)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
