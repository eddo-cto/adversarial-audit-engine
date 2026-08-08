#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pull_candidates.py — reproducible candidate pull for the §6 sealed-target set (keeper tool).

Queries the Crossref REST API with a FROZEN, pre-specified filter and writes a candidate CSV of
*pointers* — correction/retraction records and the original paper each points to. It reads only
metadata (titles, DOIs, dates); it does NOT read or classify the defect. Eligibility screening
(text-reconstructible, single mechanism, class GR/ED/DR) and sealing are the KEEPER's job, per
PREREG_empirical_strengthening.md and the contamination invariant.

Honest limitation (measured 2026-08-08): the `update-type:correction` feed is dominated by
`Author Correction` / `Publisher Correction` / trivial errata (affiliations, figures, typos) — weak
ground truth. This tool therefore (a) DROPS author/publisher corrections, and (b) supports the higher
quality frames explicitly:
    --frame retraction   : update-type:retraction (screen out misconduct via the keeper's reason check)
    --frame matters      : bibliographic 'Matters Arising' (third-party challenges; noisier query)
    --frame correction   : the raw corrections feed (low yield; kept for completeness)
Crossref does NOT expose the *reason* (error vs misconduct); that is in the Retraction Watch DB
(download separately and filter Reason for 'Error' while excluding misconduct tags). See SOURCING_PLAN.md.

Usage:
    python3 pull_candidates.py --frame retraction --from 2024-06-01 --until 2026-08-01 --rows 200 \
        --mailto you@example.org --out candidates.csv
    python3 pull_candidates.py --selftest
"""
from __future__ import annotations
import argparse, csv, json, sys, urllib.parse, urllib.request

API = "https://api.crossref.org/works"
DROP_TITLE_PREFIXES = ("author correction", "publisher correction")  # self/production, not substantive

FRAMES = {
    "retraction":  {"filter_extra": "update-type:retraction"},
    "correction":  {"filter_extra": "update-type:correction"},
    "matters":     {"query.bibliographic": "Matters Arising"},
}


def _title(item):
    t = item.get("title") or [""]
    return (t[0] if t else "").strip()


def _keep(item):
    tl = _title(item).lower()
    return tl and not any(tl.startswith(p) for p in DROP_TITLE_PREFIXES)


def _original_doi(item):
    for u in item.get("update-to", []) or []:
        d = u.get("DOI")
        if d:
            return d
    return ""


def _rows_to_records(items):
    out = []
    for it in items:
        if not _keep(it):
            continue
        ct = it.get("container-title") or [""]
        pub = it.get("published", {}).get("date-parts", [[""]])[0]
        out.append({
            "correction_doi": it.get("DOI", ""),
            "correction_title": _title(it),
            "journal": ct[0] if ct else "",
            "date": "-".join(str(x) for x in pub if x != ""),
            "original_doi": _original_doi(it),
            "original_url": f"https://doi.org/{_original_doi(it)}" if _original_doi(it) else "",
            "screen_status": "",   # keeper fills: eligible / reject / sealed
            "class_GR_ED_DR": "",  # keeper fills after reading the correction
        })
    return out


def _build_url(frame, dfrom, duntil, rows, mailto, cursor):
    filt = [f"from-pub-date:{dfrom}", f"until-pub-date:{duntil}"]
    params = {"rows": str(rows), "mailto": mailto, "cursor": cursor,
              "select": "DOI,title,container-title,published,update-to"}
    fr = FRAMES[frame]
    if "filter_extra" in fr:
        filt.insert(0, fr["filter_extra"])
    if "query.bibliographic" in fr:
        params["query.bibliographic"] = fr["query.bibliographic"]
    params["filter"] = ",".join(filt)
    return API + "?" + urllib.parse.urlencode(params)


def pull(frame, dfrom, duntil, rows, mailto, out):
    seen, records, cursor = 0, [], "*"
    while seen < rows:
        url = _build_url(frame, dfrom, duntil, min(rows - seen, 100), mailto, cursor)
        req = urllib.request.Request(url, headers={"User-Agent": f"aae-candidate-puller (mailto:{mailto})"})
        with urllib.request.urlopen(req, timeout=60) as r:
            msg = json.loads(r.read().decode("utf-8"))["message"]
        items = msg.get("items", [])
        if not items:
            break
        records.extend(_rows_to_records(items))
        seen += len(items)
        cursor = msg.get("next-cursor")
        if not cursor:
            break
    cols = ["correction_doi", "correction_title", "journal", "date",
            "original_doi", "original_url", "screen_status", "class_GR_ED_DR"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader(); w.writerows(records)
    print(f"wrote {out}: {len(records)} candidate pointers (after dropping author/publisher corrections)")
    print("NEXT: the KEEPER screens each for a text-reconstructible, single-mechanism defect, then seals "
          "(locus, mechanism, class). Do NOT feed sealed labels into any auditor run.")
    return 0


def selftest():
    fixture = [
        {"DOI": "10/x1", "title": ["Author Correction: trivial"], "container-title": ["J"],
         "published": {"date-parts": [[2025, 1, 1]]}, "update-to": [{"DOI": "10/orig1"}]},
        {"DOI": "10/x2", "title": ["Matters Arising: Claim Y is not supported by the data"],
         "container-title": ["Nature"], "published": {"date-parts": [[2025, 2, 2]]},
         "update-to": [{"DOI": "10/orig2"}]},
        {"DOI": "10/x3", "title": ["Publisher Correction: figure swap"], "container-title": ["J"],
         "published": {"date-parts": [[2025, 3, 3]]}, "update-to": []},
    ]
    recs = _rows_to_records(fixture)
    ok = (len(recs) == 1 and recs[0]["correction_doi"] == "10/x2"
          and recs[0]["original_doi"] == "10/orig2")
    print("[selftest] kept:", [r["correction_doi"] for r in recs])
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser(description="Reproducible Crossref candidate pull (keeper tool).")
    ap.add_argument("--frame", choices=list(FRAMES), default="retraction")
    ap.add_argument("--from", dest="dfrom", default="2024-06-01")
    ap.add_argument("--until", dest="duntil", default="2026-08-01")
    ap.add_argument("--rows", type=int, default=200)
    ap.add_argument("--mailto", default="you@example.org")
    ap.add_argument("--out", default="candidates.csv")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv[1:])
    if a.selftest:
        return selftest()
    return pull(a.frame, a.dfrom, a.duntil, a.rows, a.mailto, a.out)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
