#!/usr/bin/env python3
"""
run_core.py — the deterministic-core bridge for the Claude Code plugin.

The /audit command collects findings from the (possibly cross-vendor) role
agents and hands them to THIS script. Here the discipline is enforced in CODE,
not in prompts: verdict state machine, defense-gate, coverage-gate, dedup,
metrics, honest independence level, completion (never 'VALIDATED' internally),
and the meta-epistemic governor.

Input JSON (path as arg1, or stdin):
{
  "artifact_name": "spec.md",
  "internal_identity": "anthropic:claude-...",     // model that ran the hive
  "external_identity": "google:gemini-...",        // null if no external eye
  "max_posta": "high",                              // low|medium|high
  "excluded_cells": {"ethics": "no impact on persons"},
  "findings": [ { element, taxonomy_cell, defect_class, posta,
                  accusation:{text,base,evidence,sections},
                  defense:{attempted,present,fact},
                  cost_to_fix, action, declared_limit, sources, severity,
                  source_role } ]
}
Writes <out>/<stem>.ledger.json and <stem>.summary.txt; prints the summary.
"""
from __future__ import annotations
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..")))  # -> aae parent
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..")))  # bundled aae at plugin root

from aae.schema import Ledger, Posta
from aae.orchestrator import parse_finding, AuditResult
from aae.gates import enforce_defense_gate, enforce_coverage_gate, evaluate_completion
from aae import metrics as metrics_mod
from aae.triage import TriageResult
from aae.meta_epistemic import MetaGovernor
from aae.adapters import independence_level_between


def run(payload: dict, out_dir: str) -> AuditResult:
    ledger = Ledger(artifact_name=payload.get("artifact_name", "artifact"))
    for rf in payload.get("findings", []):
        f = parse_finding(rf, role_key=rf.get("source_role", "role"))
        if f:
            ledger.add(f)
    ledger.excluded_cells = dict(payload.get("excluded_cells", {}))
    ledger.adjudicate_all()
    enforce_defense_gate(ledger)
    enforce_coverage_gate(ledger)

    internal = payload.get("internal_identity", "anthropic:internal")
    external = payload.get("external_identity")
    try:
        max_posta = Posta(payload.get("max_posta", "high"))
    except ValueError:
        max_posta = Posta.HIGH

    completion = evaluate_completion(ledger, max_posta=max_posta,
                                    external_identity=external,
                                    internal_identity=internal)
    # honest independence level from the two model identities, UNLESS a human
    # external eye was recorded — in which case evaluate_completion already set
    # the ledger to HUMAN_DOMAIN_EXPERT (level 4) and we must not overwrite it.
    if not (external and external.lower().startswith("human")):
        ledger.independence_level = independence_level_between(internal, external)

    m = metrics_mod.compute(ledger)
    result = AuditResult(ledger=ledger,
                         triage=TriageResult(dimensions_present=[], deploy_roles=[]),
                         completion=completion, metrics=m)
    result.meta = MetaGovernor(None).assess(result, use_llm=False)  # deterministic

    os.makedirs(out_dir, exist_ok=True)
    stem = "".join(c if c.isalnum() else "_" for c in ledger.artifact_name)
    with open(os.path.join(out_dir, f"{stem}.ledger.json"), "w", encoding="utf-8") as fh:
        fh.write(ledger.to_json())
    summary = (result.summary() if hasattr(result, "summary") else "")
    with open(os.path.join(out_dir, f"{stem}.summary.txt"), "w", encoding="utf-8") as fh:
        fh.write(summary)
    return result


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else None
    payload = json.load(open(src, encoding="utf-8")) if src else json.load(sys.stdin)
    out_dir = os.environ.get("AAE_OUT", os.path.join(os.getcwd(), "aae_out"))
    result = run(payload, out_dir)
    print(result.summary())
    print(f"\nwritten to: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
