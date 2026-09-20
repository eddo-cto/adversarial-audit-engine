#!/usr/bin/env python3
"""
bundle_sources.py — fold MANY source documents into ONE audit artifact.

The box audits a single file (the /audit flow is pointed at one artifact and extracts its
`source_text`). Real audits are multi-document: a balance sheet + a company registry extract,
a purchase proposal + the deed + the cadastral plan. Hand-assembling them is error-prone and
loses provenance. This tool makes the bundle a first-class, repeatable step:

  * ONE self-contained markdown artifact the box can be pointed at;
  * a MANIFEST that names each document with a stable id and a content hash — the ids are the
    `evidence_base` the findings payload should declare (so the round-22 evidence-sufficiency
    gate can tell what was actually supplied);
  * each document in its OWN delimited section, so a verbatim quote in `accusation.evidence`
    stays a verbatim substring of `source_text` (the grounding gate keeps working) and its
    provenance is unambiguous.

Record-only and non-authoritative: bundling never adjudicates. It only assembles the input.

Usage:
  bundle_sources.py -o audit_input.md <file1> <file2> ...
  bundle_sources.py -o out.md --id bilancio_2025=bil.pdf --id visura_2026=vis.pdf
  bundle_sources.py <file1> <file2>            # writes ./audit_input.md, prints evidence_base

Text is read directly for .txt/.md/.json/.csv; PDFs are extracted with `pdftotext -layout`
when available, otherwise the file is reported so you can supply its text form. stdlib only.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys

_MARK = "══"  # section rule, visually distinct and unlikely to collide with document text

_TEXT_EXT = {".txt", ".md", ".markdown", ".json", ".csv", ".tsv", ".xml", ".html", ".htm", ".log"}


def _sanitize_id(stem: str) -> str:
    s = re.sub(r"[^0-9A-Za-z]+", "_", stem).strip("_").lower()
    return s or "doc"


def extract_text(path: str) -> str:
    """Best-effort text of a source file. stdlib for text; pdftotext for PDF when present."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        exe = _which("pdftotext")
        if not exe:
            raise RuntimeError(
                f"{path}: PDF given but 'pdftotext' (poppler) is not installed. Convert the PDF "
                f"to text first and pass the .txt, or install poppler-utils.")
        out = subprocess.run([exe, "-layout", path, "-"], capture_output=True, text=True)
        if out.returncode != 0:
            raise RuntimeError(f"{path}: pdftotext failed: {out.stderr.strip()[:200]}")
        return out.stdout
    if ext in _TEXT_EXT or ext == "":
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    # unknown binary: try as text, but be honest if it looks non-textual
    with open(path, "rb") as fh:
        raw = fh.read()
    if b"\x00" in raw[:4096]:
        raise RuntimeError(f"{path}: appears to be binary ({ext}); provide a text/PDF form.")
    return raw.decode("utf-8", errors="replace")


def _which(name: str) -> str | None:
    for d in os.environ.get("PATH", "").split(os.pathsep):
        cand = os.path.join(d, name)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
        if os.name == "nt" and os.path.isfile(cand + ".exe"):
            return cand + ".exe"
    return None


def make_bundle(items: list[tuple[str, str, str]]) -> tuple[str, list[str]]:
    """items = [(doc_id, display_name, text)]. Returns (markdown_bundle, evidence_base_ids).
    Pure: no I/O. Duplicate ids are disambiguated with a numeric suffix."""
    ids: list[str] = []
    seen: dict[str, int] = {}
    resolved: list[tuple[str, str, str]] = []
    for did, name, text in items:
        base = _sanitize_id(did)
        if base in seen:
            seen[base] += 1
            base = f"{base}_{seen[base]}"
        else:
            seen[base] = 1
        ids.append(base)
        resolved.append((base, name, text))

    lines: list[str] = []
    lines.append(f"# Audit bundle — {len(resolved)} documenti")
    lines.append(f"<!-- evidence_base: {', '.join(ids)} -->")
    lines.append("")
    lines.append("## Manifesto delle fonti")
    lines.append("")
    lines.append("| id (evidence_base) | documento | sha256 | caratteri |")
    lines.append("|---|---|---|---|")
    for did, name, text in resolved:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        lines.append(f"| `{did}` | {name} | {digest} | {len(text)} |")
    lines.append("")
    lines.append("> Ogni citazione verbatim proviene dalla sezione del rispettivo documento. "
                 "Dichiarare nel findings payload `evidence_base` con gli id qui sopra e, su ogni "
                 "rilievo che richiede un documento assente, `requires_docs` con l'id mancante.")
    lines.append("")
    for did, name, text in resolved:
        lines.append(f"{_MARK} INIZIO DOCUMENTO [{did}] — {name} {_MARK}")
        lines.append("")
        lines.append(text.rstrip("\n"))
        lines.append("")
        lines.append(f"{_MARK} FINE DOCUMENTO [{did}] {_MARK}")
        lines.append("")
    return "\n".join(lines), ids


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    out_path = "audit_input.md"
    id_map: dict[str, str] = {}
    files: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-o", "--out"):
            out_path = argv[i + 1]; i += 2; continue
        if a == "--id":
            k, _, v = argv[i + 1].partition("=")
            id_map[os.path.abspath(v)] = k
            files.append(v); i += 2; continue
        files.append(a); i += 1
    if not files:
        print("bundle_sources.py: no input files.", file=sys.stderr)
        return 2

    items: list[tuple[str, str, str]] = []
    for f in files:
        try:
            text = extract_text(f)
        except (OSError, RuntimeError) as e:
            print(f"bundle_sources.py: {e}", file=sys.stderr)
            return 2
        did = id_map.get(os.path.abspath(f)) or _sanitize_id(os.path.splitext(os.path.basename(f))[0])
        items.append((did, os.path.basename(f), text))

    bundle, ids = make_bundle(items)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(bundle)
    print(f"bundle: {len(items)} documenti -> {out_path}")
    print(f"evidence_base: {ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
