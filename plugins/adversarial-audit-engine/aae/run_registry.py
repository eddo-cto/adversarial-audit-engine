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


def _axes_from_cells(cells: Any) -> list[str]:
    """Normalize whatever the ledger recorded as covered taxonomy cells (a dict of
    cell->status, a list, or a set) into a sorted list of axis names."""
    if not cells:
        return []
    try:
        it = cells.keys() if isinstance(cells, dict) else cells
        return sorted({str(c) for c in it if c})
    except TypeError:
        return []


def _axes_covered(ledger: Any) -> list[str]:
    """The taxonomy cells (orthogonal axes) actually touched by this run. Prefer the
    ledger's own covered_cells; fall back to the cells cited by the findings. This is
    what makes the diachronic 'orthogonal axes' view queryable per run."""
    cc = getattr(ledger, "covered_cells", None)
    axes = _axes_from_cells(cc)
    if axes:
        return axes
    cells = set()
    for f in getattr(ledger, "findings", []) or []:
        tc = getattr(f, "taxonomy_cell", None)
        if tc:
            cells.add(str(tc))
    return sorted(cells)


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
        "artifact_id": (getattr(ledger, "artifact_id", "")
                        or manifest.get("artifact_id", "") or ""),
        "run_validity": manifest.get("run_validity", ""),
        "verdicts": dict(getattr(rec, "verdicts", {}) or {}),
        "axes_covered": _axes_covered(ledger),
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


# ---------------------------------------------------------------------------
# Consolidation: back-fill the single registry from ledgers written before it
# existed (or in scattered per-run folders). Record-only, idempotent, dedup by
# run_id — re-running consolidate() never double-counts a run.
# ---------------------------------------------------------------------------

def record_from_ledger_dict(d: dict, *, ledger_path: str = "", box: str = "") -> dict:
    """Build a registry record from a serialized ledger (a `*.ledger.json` dict),
    for consolidating runs that predate the live registry. Mirrors record_from_ledger
    but reads plain JSON keys; verdicts are counted from the findings themselves."""
    created = float(d.get("created_at", 0.0) or 0.0)
    iso = datetime.datetime.fromtimestamp(
        created, datetime.timezone.utc).isoformat() if created else ""
    digest = d.get("content_digest", "") or ""
    eye = d.get("external_attested_identity", "") or ""
    manifest = d.get("run_manifest", {}) or {}
    verdicts: dict[str, int] = {}
    for f in d.get("findings", []) or []:
        vv = f.get("verdict")
        if vv:
            verdicts[vv] = verdicts.get(vv, 0) + 1
    return {
        "run_id": f"{int(created)}-{digest[:12]}" if created or digest else "",
        "timestamp": iso,
        "box": box,
        "artifact": d.get("artifact_name", ""),
        "artifact_id": d.get("artifact_id", "") or manifest.get("artifact_id", "") or "",
        "run_validity": manifest.get("run_validity", ""),
        "verdicts": verdicts,
        "axes_covered": _axes_from_cells(d.get("covered_cells")) or sorted(
            {f.get("taxonomy_cell") for f in d.get("findings", []) or [] if f.get("taxonomy_cell")}),
        "independence_level": int(d.get("independence_level", 0) or 0),
        "eye_vendor": _vendor(eye),
        "eye_identity": eye,
        "internal_identity": d.get("internal_identity", "") or "",
        "governor_completion": d.get("completion_state", "") or "",
        "calibration": _calibration(d.get("flags", []) or []),
        "content_digest": digest,
        "ledger_path": ledger_path,
    }


def _iter_ledger_files(roots: list[str]):
    for root in roots:
        if os.path.isfile(root) and root.endswith(".ledger.json"):
            yield root
            continue
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                if name.endswith(".ledger.json"):
                    yield os.path.join(dirpath, name)


def consolidate(roots: list[str], path: str | None = None, box: str = "") -> dict:
    """Sweep `roots` for serialized ledgers and back-fill the single registry with any
    run not already present (dedup by run_id). Idempotent: safe to re-run. Returns a
    small report {scanned, added, skipped, path}. Never raises on a bad ledger file."""
    path = path or registry_path()
    existing = {r.get("run_id") for r in load(path) if r.get("run_id")}
    scanned = added = skipped = 0
    for lp in _iter_ledger_files(roots):
        scanned += 1
        try:
            d = json.load(open(lp, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            skipped += 1
            continue
        rec = record_from_ledger_dict(d, ledger_path=os.path.abspath(lp), box=box)
        rid = rec.get("run_id")
        if not rid or rid in existing:
            skipped += 1
            continue
        if append(rec, path=path) is None:
            skipped += 1
            continue
        existing.add(rid)
        added += 1
    return {"scanned": scanned, "added": added, "skipped": skipped, "path": path}


# ---------------------------------------------------------------------------
# Diachronic cross-vendor SIGNATURE (descriptive, record-only).
#
# NOT a proof of Goodhart mitigation. It reports one observable regularity: when the
# SAME artifact is re-audited at a HIGHER independence level (a different-vendor eye
# entering), how the verdict mix shifts. A measure that were being over-optimized at a
# single vendor would show its condemnations DEFLATE once an orthogonal, cross-vendor
# axis is added. This function surfaces that shift so it can be read — it does not
# certify it, and it carries the caveats that keep it honest.
# ---------------------------------------------------------------------------

_CONDEMN = {"accusa_vince", "accusa_ridimensionata"}
_ABSOLVE = {"artefatto_regge"}
_ABSTAIN = {"da_leggere", "conteso", "pending"}


def _rates(verdicts: dict) -> tuple[int, dict]:
    total = sum(verdicts.values())
    if total == 0:
        return 0, {"condemn": None, "abstain": None, "hold": None}
    c = sum(v for k, v in verdicts.items() if k in _CONDEMN)
    a = sum(v for k, v in verdicts.items() if k in _ABSTAIN)
    h = sum(v for k, v in verdicts.items() if k in _ABSOLVE)
    return total, {"condemn": c / total, "abstain": a / total, "hold": h / total}


def _artifact_key(name: str) -> str:
    """Group L1 and L3 passes of the same artefact: the digest differs between passes
    (findings differ), so we key on a normalized artifact name instead."""
    return "".join(ch.lower() for ch in (name or "") if ch.isalnum())[:48]


def signature(path: str | None = None) -> str:
    """Descriptive panel of the diachronic cross-vendor shift. For every artefact seen
    at >=2 independence levels, report how condemn/abstain rates move from the lowest to
    the highest level, and whether a cross-vendor eye entered. Aggregates the mean shift.
    No single score; abstention is never counted as success; explicit caveats."""
    path = path or registry_path()
    runs = load(path)
    if not runs:
        return f"Nessun run registry in {path}."

    groups: dict[str, list[dict]] = {}
    for r in runs:
        # a stable artifact_id (stamped on the run) pairs passes reliably; the free-text
        # artifact name is the fallback and is fragile — it changes between an L1 and an
        # L3 pass of the "same" artefact, which is exactly why pairing can under-count.
        key = (r.get("artifact_id") or "").strip() or _artifact_key(r.get("artifact", ""))
        groups.setdefault(key, []).append(r)

    paired = []
    for key, recs in groups.items():
        levels = {int(r.get("independence_level", 0) or 0) for r in recs}
        if len(levels) < 2:
            continue
        lo_l, hi_l = min(levels), max(levels)
        lo = [r for r in recs if int(r.get("independence_level", 0) or 0) == lo_l]
        hi = [r for r in recs if int(r.get("independence_level", 0) or 0) == hi_l]
        lo_v: dict[str, int] = {}
        hi_v: dict[str, int] = {}
        for r in lo:
            for k, v in (r.get("verdicts", {}) or {}).items():
                lo_v[k] = lo_v.get(k, 0) + v
        for r in hi:
            for k, v in (r.get("verdicts", {}) or {}).items():
                hi_v[k] = hi_v.get(k, 0) + v
        _, lr = _rates(lo_v)
        _, hr = _rates(hi_v)
        if lr["condemn"] is None or hr["condemn"] is None:
            continue
        eye_hi = next((r.get("eye_vendor", "") for r in hi if r.get("eye_vendor")), "")
        paired.append({
            "artifact": (hi[0].get("artifact", "") or "")[:40],
            "lo_l": lo_l, "hi_l": hi_l,
            "d_condemn": hr["condemn"] - lr["condemn"],
            "d_abstain": hr["abstain"] - lr["abstain"],
            "lo_condemn": lr["condemn"], "hi_condemn": hr["condemn"],
            "cross_vendor": bool(eye_hi),
        })

    lines = [f"DIACHRONIC CROSS-VENDOR SIGNATURE — {path}", ""]
    if not paired:
        lines.append("Nessun artefatto ancora osservato a >=2 livelli di indipendenza:")
        lines.append("la firma richiede coppie L-basso -> L-alto sullo stesso artefatto.")
        lines.append("Causa probabile del sotto-conteggio: l'appaiamento cade sul nome libero")
        lines.append("dell'artefatto, che cambia tra un passaggio L1 e uno L3. Timbrare un")
        lines.append("`artifact_id` stabile su ogni run rende le coppie riconoscibili.")
        lines.append(f"(run totali nel registry: {len(runs)})")
        return "\n".join(lines)

    lines.append(f"{'artefatto':40}  {'liv.':>7}  {'condemn lo->hi':16}  {'d.abstain':>9}  x-vendor")
    lines.append("-" * 92)
    for p in sorted(paired, key=lambda x: x["d_condemn"]):
        lines.append(f"{p['artifact']:40}  {p['lo_l']}->{p['hi_l']:<4}  "
                     f"{p['lo_condemn']:.2f}->{p['hi_condemn']:.2f}      "
                     f"{p['d_abstain']:+.2f}     {'sì' if p['cross_vendor'] else 'no'}")
    n = len(paired)
    mean_dc = sum(p["d_condemn"] for p in paired) / n
    mean_da = sum(p["d_abstain"] for p in paired) / n
    xv = sum(1 for p in paired if p["cross_vendor"])
    deflated = sum(1 for p in paired if p["d_condemn"] < 0)
    lines.append("-" * 92)
    lines.append(f"coppie: {n}  |  con occhio cross-vendor al livello alto: {xv}/{n}")
    lines.append(f"variazione media tasso di condanna (alto-basso): {mean_dc:+.3f}  "
                 f"(negativo = deflazione)")
    lines.append(f"variazione media tasso di astensione: {mean_da:+.3f}")
    lines.append(f"coppie in cui la condanna DEFLAZIONA salendo di indipendenza: {deflated}/{n}")
    lines.append("")
    lines.append("LETTURA ONESTA — questa è una FIRMA descrittiva, non una dimostrazione di")
    lines.append("mitigazione di Goodhart. Mostra che aggiungere un asse ortogonale cross-vendor")
    lines.append("sgonfia la sovra-condanna a vendor singolo; NON prova resistenza-al-gaming perché")
    lines.append("nessun ottimizzatore sta spingendo sulla misura (anello chiuso assente). Serve un")
    lines.append("design avversariale pre-registrato e un n maggiore. L'astensione non è un successo.")
    return "\n".join(lines)
