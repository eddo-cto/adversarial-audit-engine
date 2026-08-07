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

from aae.schema import Ledger, Posta, ActionState
from aae.orchestrator import parse_finding, AuditResult
from aae.gates import enforce_defense_gate, enforce_coverage_gate, evaluate_completion
from aae.source_grade import enforce_source_grade_gate, source_grade_coverage
from aae.run_manifest import build_manifest
from aae.grounding import enforce_grounding
from aae import metrics as metrics_mod
from aae import run_metrics as rmx
from aae.triage import TriageResult
from aae.meta_epistemic import MetaGovernor
from aae.attestation import content_digest, verify_human_attestation


def run(payload: dict, out_dir: str) -> AuditResult:
    ledger = Ledger(artifact_name=payload.get("artifact_name", "artifact"))
    for rf in payload.get("findings", []):
        f = parse_finding(rf, role_key=rf.get("source_role", "role"))
        if f:
            ledger.add(f)
    ledger.excluded_cells = dict(payload.get("excluded_cells", {}))
    ledger.adjudicate_all()
    enforce_defense_gate(ledger)
    # Round-12 source-grade gate (§7.1): a condemnation resting on a non-primary
    # datum, when a primary is reachable, is downgraded to NEEDS_READING. The
    # operator may declare no primary exists via source_primary_reachable=false.
    primary_reachable = bool(payload.get("source_primary_reachable", True))
    ledger.flags.extend(enforce_source_grade_gate(ledger, primary_reachable=primary_reachable))
    enforce_coverage_gate(ledger)
    # F-SECTIONS fix: the schema's structural checks (e.g. a non-local class
    # needs >=2 cited sections; at least one declared limit) only run via
    # integrity_report(). Call it on the documented path and surface problems
    # as flags, so the rule is enforced where the operator actually runs.
    ledger.flags.extend(f"INTEGRITY: {p}" for p in ledger.integrity_report())
    # anti-hallucination: a condemning finding whose quote is not verbatim in the
    # source text is downgraded (possible fabrication). Pass the artifact text in
    # payload["source_text"] to activate it.
    src_text = payload.get("source_text", "")
    if src_text:
        enforce_grounding(ledger.findings, src_text)

    internal = payload.get("internal_identity", "anthropic:internal")
    external = payload.get("external_identity")
    try:
        max_posta = Posta(payload.get("max_posta", "high"))
    except ValueError:
        max_posta = Posta.HIGH

    # Round-12 self-instrumentation check (§7.6): a high-stakes run that records
    # NO deliberately-discarded hypotheses has an unknown generated/discarded
    # denominator — the false-positive discipline is then asserted, not measured.
    discarded = sum(1 for f in ledger.findings
                    if f.action_state == ActionState.DELIBERATELY_DISCARDED)
    if max_posta == Posta.HIGH and discarded == 0:
        ledger.flags.append(
            "SELF-INSTRUMENTATION: no discarded hypotheses recorded on a high-stakes "
            "run — the generated/discarded denominator is unknown, so the false-"
            "positive rate is asserted, not measured. Record killed hypotheses with "
            "action_state=deliberately_discarded.")

    # Round-11: closure is ENFORCED, not conventional.
    #  * Human closure = a valid HMAC over the ledger digest under an operator key
    #    the model cannot reach (AAE_HUMAN_KEY). A bare token does NOT validate.
    #  * Independence level 3 is credited only from the adapter-attested identity
    #    (AAE_EXTERNAL_ATTESTED_IDENTITY), never from the model-authored payload.
    digest = content_digest(ledger.artifact_name,
                            [{"element": f.element, "verdict": f.verdict.value}
                             for f in ledger.findings])
    ledger.content_digest = digest
    key = os.environ.get("AAE_HUMAN_KEY")
    token = os.environ.get("AAE_HUMAN_ATTESTATION")
    human_verified = verify_human_attestation(digest, token, key)
    human_claimed = bool(token) and not human_verified
    attested_identity = os.environ.get("AAE_EXTERNAL_ATTESTED_IDENTITY") or None

    completion = evaluate_completion(ledger, max_posta=max_posta,
                                    external_identity=external,
                                    internal_identity=internal,
                                    human_verified=human_verified,
                                    human_claimed=human_claimed,
                                    attested_identity=attested_identity)
    # evaluate_completion has set ledger.independence_level. Persist the completion
    # state and digest so the Stop hook can re-verify and enforce on the artifact.
    ledger.completion_state = completion.state

    # Round-14: record the per-grade breakdown (the import was previously dead).
    ledger.source_grade_coverage = source_grade_coverage(ledger)

    m = metrics_mod.compute(ledger)
    result = AuditResult(ledger=ledger,
                         triage=TriageResult(dimensions_present=[], deploy_roles=[]),
                         completion=completion, metrics=m)
    result.meta = MetaGovernor(None).assess(result, use_llm=False)  # deterministic

    # Round-13/16 execution manifest. Scaffolding is MEASURED from real outputs:
    # governor from the meta verdict just produced, oracle from the cited sources,
    # triage from its decision record (which also auto-adjudicates the optional
    # layers it did not select). Emitting layers are measured from source_role.
    manifest = build_manifest(ledger, payload.get("execution"),
                              triage=payload.get("triage"),
                              governor_ran=result.meta is not None)
    ledger.run_manifest = manifest.to_dict()

    os.makedirs(out_dir, exist_ok=True)
    stem = "".join(c if c.isalnum() else "_" for c in ledger.artifact_name)
    with open(os.path.join(out_dir, f"{stem}.ledger.json"), "w", encoding="utf-8") as fh:
        fh.write(ledger.to_json())
    summary = (result.summary() if hasattr(result, "summary") else "")
    with open(os.path.join(out_dir, f"{stem}.summary.txt"), "w", encoding="utf-8") as fh:
        fh.write(summary)

    # longitudinal, bias-resistant metrics: accrue one record per run.
    rec = rmx.from_ledger(ledger)
    with open(os.path.join(out_dir, "_runs.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"artifact": ledger.artifact_name, "verdicts": rec.verdicts,
                             "grounding_downgrades": rec.grounding_downgrades,
                             "by_class": rec.by_class,
                             "run_manifest": ledger.run_manifest,
                             "source_grade_coverage": ledger.source_grade_coverage,
                             "flags": ledger.flags}, ensure_ascii=False) + "\n")
    return result


def metrics_report(out_dir: str) -> str:
    """Longitudinal panel + bias_audit over all accrued runs in out_dir.
    Descriptive only; no single score; abstention never counts as success."""
    path = os.path.join(out_dir, "_runs.jsonl")
    if not os.path.exists(path):
        return f"Nessuno storico run (_runs.jsonl) in {out_dir}"
    runs = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        runs.append(rmx.RunRecord(verdicts=d.get("verdicts", {}),
                                  grounding_downgrades=d.get("grounding_downgrades", 0),
                                  by_class=d.get("by_class", {})))
    panel = rmx.compute(runs)
    warns = rmx.bias_audit(panel)
    return (panel.as_text() + "\n\n=== bias_audit ===\n" +
            ("\n".join("- " + w for w in warns) if warns else "- nessuna firma degenere"))


USAGE = """\
run_core.py — deterministic-core bridge (verdict state machine, defense-gate,
coverage-gate, dedup, metrics, meta-epistemic governor).

Usage:
  run_core.py <findings.json>      run the core on a findings payload
  run_core.py                      same, reading the payload from stdin
  run_core.py --metrics [dir]      longitudinal, bias-resistant metrics panel
  run_core.py --help               this message
  run_core.py --version            print the engine version

Environment:
  AAE_OUT    output directory (default: ./aae_out)

The payload schema is documented in the module docstring at the top of this
file. The core NEVER reports VALIDATED on internal grounds: the best internal
state is EXTERNAL_REVIEW_PENDING, and closure belongs to a human reviewer.
"""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out_dir = os.environ.get("AAE_OUT", os.path.join(os.getcwd(), "aae_out"))

    if argv and argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0

    if argv and argv[0] in ("-V", "--version"):
        from aae import __version__
        print(f"adversarial-audit-engine {__version__}")
        return 0

    # longitudinal metrics mode:  run_core.py --metrics [out_dir]
    if argv and argv[0] == "--metrics":
        if len(argv) > 1:
            out_dir = argv[1]
        print(metrics_report(out_dir))
        return 0

    if argv and argv[0].startswith("-"):
        print(f"run_core.py: unknown option {argv[0]!r}\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    src = argv[0] if argv else None
    try:
        if src:
            with open(src, encoding="utf-8") as fh:
                payload = json.load(fh)
        else:
            if sys.stdin.isatty():
                print("run_core.py: no payload given and stdin is a terminal.\n",
                      file=sys.stderr)
                print(USAGE, file=sys.stderr)
                return 2
            payload = json.load(sys.stdin)
    except FileNotFoundError:
        print(f"run_core.py: payload file not found: {src}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        where = src or "<stdin>"
        print(f"run_core.py: {where} is not valid JSON (line {e.lineno}, "
              f"column {e.colno}): {e.msg}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict) or "findings" not in payload:
        print("run_core.py: payload must be a JSON object containing a "
              "'findings' list. See --help.", file=sys.stderr)
        return 2

    result = run(payload, out_dir)
    print(result.summary())
    print(f"\nwritten to: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
