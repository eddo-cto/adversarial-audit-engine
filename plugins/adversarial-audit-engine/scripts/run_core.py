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
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..")))  # -> plugin dir (aae's parent)

from aae.pipeline import discipline           # THE one disciplined core
from aae.orchestrator import AuditResult
from aae import run_metrics as rmx


def run(payload: dict, out_dir: str) -> AuditResult:
    """Thin product-path wrapper: enforce the discipline (shared with Orchestrator.run) and write the
    ledger, summary, and the longitudinal run record. The attested eye is read from the environment
    (`AAE_EXTERNAL_ATTESTED_IDENTITY`) — the agent exports it after actually calling the eye."""
    result = discipline(payload)
    ledger = result.ledger

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


def emit_schema() -> str:
    """The exact findings payload the orchestrator must produce — template + the
    live enum vocabularies — so the role agent NEVER has to reverse-engineer the
    core (guess class names, list enums by hand). Introspected from the real enums,
    so it can never drift from what the code accepts. One deterministic call
    replaces ad-hoc introspection."""
    from aae.schema import (DefectClass, Posta, EvidenceBase, CostToFix,
                            ActionState, Verdict)
    from aae.triage import TAXONOMY
    schema = {
        "payload_template": {
            "artifact_name": "<name shown in the report>",
            "internal_identity": "anthropic:claude-<model that ran the hive>",
            "external_identity": None,
            "max_posta": "high",
            "source_primary_reachable": True,
            "source_text": "<full verbatim text of the artifact (activates the grounding gate)>",
            "excluded_cells": {"<taxonomy_cell>": "<why this dimension does not apply>"},
            "triage": {"dimensions_present": ["<taxonomy_cell>", "..."],
                       "deploy_roles": ["verifier", "propagator", "..."]},
            "findings": ["<finding objects: see finding_template>"],
        },
        "finding_template": {
            "source_role": "verifier|propagator|reasoner|oracle|<specialist>",
            "element": "<the specific element under audit>",
            "taxonomy_cell": "<one of vocabularies.taxonomy_cell>",
            "defect_class": "<one of vocabularies.defect_class>",
            "posta": "<one of vocabularies.posta>",
            "accusation": {"text": "<the accusation>",
                           "base": "<one of vocabularies.evidence_base>",
                           "evidence": "<VERBATIM quote from source_text, or executed result>",
                           "sections": ["§..", "§.."]},
            "defense": {"attempted": True, "present": False, "fact": None},
            "cost_to_fix": "<one of vocabularies.cost_to_fix>",
            "action": "<the corrective action>",
            "declared_limit": "<what you could NOT decide internally>",
            "sources": ["<primary source refs>"],
            "severity": "alta|media|bassa|nessuna",
            "source_grade": 1,
            "action_state": "open",
        },
        "vocabularies": {
            "taxonomy_cell": list(TAXONOMY),
            "defect_class": [e.value for e in DefectClass],
            "posta": [e.value for e in Posta],
            "evidence_base": [e.value for e in EvidenceBase],
            "cost_to_fix": [e.value for e in CostToFix],
            "action_state": [e.value for e in ActionState],
            "verdict_OUTPUT_ONLY": [e.value for e in Verdict],
        },
        "rules": [
            "Attempt the STRONGEST defense first for every accusation (defense.attempted=true); "
            "condemnation without a recorded defense is impossible.",
            "accusation.evidence must be VERBATIM from source_text (grounding gate) or an executed "
            "result; a paraphrase is downgraded to 'must be read by a human'.",
            "A non_local_* / conceptual finding needs >= 2 cited sections in accusation.sections.",
            "source_grade: 1=primary filed/executed, 2=institutional/secondary, 3=generalist, "
            "9=undeclared. A condemnation resting on grade>1 is downgraded to NEEDS_READING when a "
            "primary is reachable.",
            "On a HIGH-posta run record >= 1 hypothesis with action_state=deliberately_discarded, "
            "so the false-positive rate is MEASURED, not asserted.",
            "Verdicts are OUTPUT-ONLY — the code assigns them. Never put a verdict in a finding.",
            "The independent eye comes from AAE_EYE (env). After ACTUALLY calling it, export "
            "AAE_EXTERNAL_ATTESTED_IDENTITY=<eye.identity> so the core credits level 3. Never fake one.",
        ],
        "run": "python3 run_core.py <findings.json>   (writes ledger + summary to $AAE_OUT)",
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


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
  run_core.py --schema             print the EXACT findings schema + enum vocab
                                   (produce your findings.json to match this)
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


def _utf8_stdio() -> None:
    """Force UTF-8 stdout/stderr so a summary with accented text or box glyphs does not
    crash on the Windows console codepage (cp1252). A real run had to work around this
    by exporting PYTHONIOENCODING by hand; make it intrinsic. No-op where unsupported."""
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


_PENDING_MARKER = ".audit_pending"


def _mark_audit_pending(out_dir: str) -> None:
    """Drop a marker the moment an audit fetches the schema (the first mandatory
    step). It is cleared ONLY by a completed core run (below). If a surprise — an
    exception, a tool error, or the model deciding to write a prose 'referto'
    instead of invoking the core — derails the run, the marker survives and the
    Stop hook rejects the session. This is engineered, non-bypassable enforcement
    of 'the deterministic core is not optional': it does not rely on the model
    remembering to run the core."""
    try:
        import datetime
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, _PENDING_MARKER), "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"started_at": datetime.datetime.now(
                datetime.timezone.utc).isoformat()}))
    except Exception:
        pass  # never let bookkeeping break the audit


def _clear_audit_pending(out_dir: str) -> None:
    """The core ran and wrote a ledger — the disciplined path completed (even an
    INVALID_RUN counts: the core adjudicated it). Remove the marker."""
    try:
        os.remove(os.path.join(out_dir, _PENDING_MARKER))
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    _utf8_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)
    out_dir = os.environ.get("AAE_OUT", os.path.join(os.getcwd(), "aae_out"))

    if argv and argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0

    if argv and argv[0] in ("-V", "--version"):
        from aae import __version__
        print(f"adversarial-audit-engine {__version__}")
        return 0

    # emit the exact findings schema + enum vocabulary, so the orchestrator produces
    # a valid payload instead of reverse-engineering the core live (the improvisation
    # a real Claude Code run exposed: guessing class names, listing enums by hand).
    if argv and argv[0] == "--schema":
        _mark_audit_pending(out_dir)   # an audit has started; only a core run clears this
        print(emit_schema())
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
    _clear_audit_pending(out_dir)   # the core ran and wrote a ledger: disciplined path complete
    print(result.summary())
    print(f"\nwritten to: {out_dir}")
    if result.ledger.run_manifest.get("run_validity") != "VALID":
        print("\nINVALID_RUN: the run failed the A+B execution rule (see flags). "
              "It is written for inspection but cannot be closed.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
