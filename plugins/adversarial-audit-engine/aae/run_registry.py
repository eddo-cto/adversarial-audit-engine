"""
run_registry.py — the single longitudinal run registry (round 21, record-only).

Each `_runs.jsonl` written by the core lives inside its own run's out_dir and is
never aggregated: answering "how many runs, with what verdicts, at what
independence, over time" meant a find(1) sweep across scattered folders, and the
property that matters most — the independence actually achieved and the vendor of
the eye — was not even recorded. This module fixes both:

  * ONE known location (AAE_REGISTRY, else AAE_HOME/RUN_REGISTRY.jsonl, else
    ~/.aae/RUN_REGISTRY.jsonl), append-only, one line per completed run.
  * independence_level, eye_vendor, and the governor verdict are FIRST-CLASS
    recorded fields — the independence of a run becomes queryable, not
    reconstructed by hand.

Record-only and non-authoritative: the registry NEVER adjudicates and NEVER
gates. It is a downstream index of what the deterministic core already decided.
Writing it can never break an audit — every write is best-effort (see append()).
"""
from __future__ import annotations

import datetime
import json
import os
from typing import Any


def registry_path() -> str:
    """The single, stable location of the registry. Explicit AAE_REGISTRY wins;
    otherwise it sits under AAE_HOME (a stable per-box home), else ~/.aae."""
    explicit = os.environ.get("AAE_REGISTRY")
    if explicit:
        return explicit
    home = os.environ.get("AAE_HOME") or os.path.join(os.path.expanduser("~"), ".aae")
    return os.path.join(home, "RUN_REGISTRY.jsonl")


def _vendor(identity: str) -> str:
    """The nature of an identity is the token before the first ':' — "meta:llama3.1"
    -> "meta". Empty when no eye was attested."""
    if not identity:
        return ""
    return identity.split(":", 1)[0].strip().lower()


def _calibration(flags: list[str]) -> str:
    """Type-I calibration state, read off the flags the core already set."""
    for f in flags or ():
        if "NOT CALIBRATED" in f.upper():
            return "NOT_CALIBRATED"
    return "calibrated"


def record_from_ledger(ledger: Any, rec: Any, *, ledger_path: str = "",
                       box: str | None = None) -> dict:
    """Build the one-line registry record from an already-adjudicated ledger and its
    RunRecord (verdict/metric summary). Pure: derives, never decides."""
    created = float(getattr(ledger, "created_at", 0.0) or 0.0)
    iso = datetime.datetime.fromtimestamp(
        created, datetime.timezone.utc).isoformat() if created else ""
    digest = getattr(ledger, "content_digest", "") or ""
    eye = getattr(ledger, "external_attested_identity", "") or ""
    manifest = getattr(ledger, "run_manifest", {}) or {}
    return {
        "run_id": f"{int(created)}-{digest[:12]}" if created or digest else "",
        "timestamp": iso,
        "box": (box if box is not None else os.environ.get("AAE_BOX", "")),
        "artifact": getattr(ledger, "artifact_name", ""),
        "run_validity": manifest.get("run_validity", ""),
        "verdicts": dict(getattr(rec, "verdicts", {}) or {}),
        "independence_level": int(getattr(ledger, "independence_level", 0) or 0),
        "eye_vendor": _vendor(eye),
        "eye_identity": eye,
        "internal_identity": getattr(ledger, "internal_identity", "") or "",
        "governor_completion": getattr(ledger, "completion_state", "") or "",
        "calibration": _calibration(getattr(ledger, "flags", []) or []),
        "content_digest": digest,
        "ledger_path": ledger_path,
    }


def append(record: dict, path: str | None = None) -> str | None:
    """Append one record to the registry. Best-effort: any failure (permissions, a
    read-only mount, a disk error) is swallowed so registry bookkeeping can NEVER
    break an audit. Returns the path written, or None on failure."""
    try:
        path = path or registry_path()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path
    except Exception:
        return None


def load(path: str | None = None) -> list[dict]:
    """Read every accrued registry record. Skips malformed lines rather than raising."""
    path = path or registry_path()
    out: list[dict] = []
    if not os.path.exists(path):
        return out
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return out
    return out


def render(path: str | None = None) -> str:
    """A descriptive portfolio panel over the registry — one row per run, plus honest
    roll-ups (independence distribution, cross-vendor count, calibration). No single
    score; abstention is never dressed up as success."""
    path = path or registry_path()
    runs = load(path)
    if not runs:
        return f"Nessun run registry in {path} (nessuna run ancora registrata)."

    lines = [f"RUN REGISTRY — {len(runs)} run — {path}", ""]
    lines.append(f"{'timestamp':20}  {'ind':>3}  {'gov. completion':22}  "
                 f"{'eye vendor':12}  {'valid':7}  verdetti")
    lines.append("-" * 96)
    ind_dist: dict[int, int] = {}
    cross_vendor = 0
    not_calibrated = 0
    for r in runs:
        ind = int(r.get("independence_level", 0) or 0)
        ind_dist[ind] = ind_dist.get(ind, 0) + 1
        if ind >= 3:
            cross_vendor += 1
        if r.get("calibration") == "NOT_CALIBRATED":
            not_calibrated += 1
        v = r.get("verdicts", {}) or {}
        vtxt = ", ".join(f"{k}={val}" for k, val in sorted(v.items())) or "—"
        ts = (r.get("timestamp", "") or "")[:19]
        lines.append(f"{ts:20}  {ind:>3}  {(r.get('governor_completion','') or '—')[:22]:22}  "
                     f"{(r.get('eye_vendor','') or '—')[:12]:12}  "
                     f"{(r.get('run_validity','') or '—')[:7]:7}  {vtxt}")
    lines.append("-" * 96)
    dist = ", ".join(f"L{k}={ind_dist[k]}" for k in sorted(ind_dist))
    lines.append(f"indipendenza: {dist}  |  cross-vendor (>=L3): {cross_vendor}/{len(runs)}"
                 f"  |  Type-I non calibrati: {not_calibrated}/{len(runs)}")
    lines.append("Record-only: il registry indicizza, non valida. La chiusura resta all'occhio umano.")
    return "\n".join(lines)
