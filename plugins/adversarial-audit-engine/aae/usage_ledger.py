"""
usage_ledger.py — PERSISTENCE layer for meta-analysis of engine runs.

What it does (and does not):
  Append-only ledger, one JSON line per engine run. It is the raw material for
  run_metrics.Panel (the descriptive, anti-Goodhart calculator). It computes NO
  merit score of its own; it only RECORDS, traceably.

Three purposes, kept separate downstream (same file, different reads):
  1. Improvement telemetry — where the engine abstains/errs too much.
  2. Historical series (dataset) — runs over time as an object of study.
  3. Reflexive meta-level — the engine evaluating its own evaluations.

Reflexive discipline (project invariant):
  This sub-layer IS a self-referential evaluator, so the SAME rule applies: it does
  not self-validate, non-closure is declared, closure belongs to the external human eye.

Golden anti-Goodhart rule:
  No field in this ledger may become a TARGET of the engine's gate. If it did, the
  engine would learn to produce good metrics instead of good audits — exactly the
  failure the paper describes. Telemetry describes; it does not decide.

Deterministic, stdlib only. No LLM.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

# verdict categories: aligned with run_metrics (single source of truth for buckets)
_CONDEMN = {"accusa_vince"}
_ABSOLVE = {"artefatto_regge"}
_ABSTAIN = {"da_leggere", "conteso", "pending"}

# Ledger location. Honour AAE_USAGE_LEDGER so the run-log can live outside the
# package directory (a plugin install dir may be read-only, and mixing run data
# with code is undesirable). Falls back to the in-package path for compatibility.
DEFAULT_PATH = os.environ.get(
    "AAE_USAGE_LEDGER",
    os.path.join(os.path.dirname(__file__), "usage_ledger.jsonl"),
)


@dataclass
class UsageRecord:
    """One engine run reduced to meta-data. NO sensitive domain content."""
    run_id: str
    data: str                                   # ISO-8601 UTC
    dominio: str                                # e.g. "auctions", "building-permits", "self-audit"
    artefatto: str                              # what was audited (label, not content)
    ruoli: list[str] = field(default_factory=list)          # roles activated in the run
    verdetti: dict[str, int] = field(default_factory=dict)  # verdict-value -> count
    n_astensioni: int = 0                       # findings routed to human (ABSTAIN bucket)
    override_umani: int = 0                      # times the human corrected the engine
    grounding_interventi: int = 0               # anti-hallucination downgrades
    note: str = ""

    # --- descriptive derivatives (never a target) ---
    def n_findings(self) -> int:
        return sum(self.verdetti.values())

    def n_condanne(self) -> int:
        return sum(n for k, n in self.verdetti.items() if k in _CONDEMN)

    def n_assoluzioni(self) -> int:
        return sum(n for k, n in self.verdetti.items() if k in _ABSOLVE)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append(rec: UsageRecord, path: str = DEFAULT_PATH) -> None:
    """Append-only. Never rewrites existing lines (same discipline as the append-only stores)."""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")


def load(path: str = DEFAULT_PATH) -> list[UsageRecord]:
    if not os.path.exists(path):
        return []
    out: list[UsageRecord] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(UsageRecord(**json.loads(line)))
    return out


def to_run_records(recs: list[UsageRecord]):
    """Bridge to run_metrics.RunRecord (the existing descriptive calculator)."""
    from .run_metrics import RunRecord
    return [RunRecord(verdicts=dict(r.verdetti),
                      grounding_downgrades=r.grounding_interventi) for r in recs]


def summarize(path: str = DEFAULT_PATH) -> str:
    """Descriptive summary of the historical series. No single score; delegates to run_metrics."""
    recs = load(path)
    if not recs:
        return "usage_ledger empty: no runs recorded."
    from .run_metrics import compute, bias_audit
    panel = compute(to_run_records(recs))
    lines = [
        f"=== usage_ledger: {len(recs)} runs recorded ===",
        "domains: " + ", ".join(sorted({r.dominio for r in recs})),
        f"total human overrides: {sum(r.override_umani for r in recs)}",
        "",
        panel.as_text(),
    ]
    warn = bias_audit(panel)
    if warn:
        lines += ["", "--- bias flags (anti-Goodhart) ---"] + [f"* {w}" for w in warn]
    lines += ["",
              "NB: precision/recall/escape stay n/d without external human ground truth.",
              "This summary DESCRIBES the series; it does not validate the engine (closure = human eye)."]
    return "\n".join(lines)


if __name__ == "__main__":
    print(summarize())
