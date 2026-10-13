#!/usr/bin/env python3
"""match_audit.py — validity check of the factor matcher: which findings each pre-registered factor matched, per run.
Writes match_audit.csv for a human spot-check BEFORE trusting M1-M3 (a too-broad regex inflates 'open')."""
import csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import forms_replay as FR
root = sys.argv[1]
factors = {k: v for k, v in json.load(open(os.path.join(HERE, "factors_rn95.json"), encoding="utf-8")).items()
           if not k.startswith("_")}
rows = []
for name, led, src in FR.load_runs(root):
    pres = FR.present(led, src, "F0")
    for f in led.findings:
        if f.id not in pres:
            continue
        text = FR._norm((f.element or "") + " " + (f.accusation.text or ""))
        hits = [k for k, pats in factors.items() if any(re.search(p, text, re.I) for p in pats)]
        rows.append([name, f.id, f.posta.value, f.verdict.value, pres[f.id], "|".join(hits) or "-", text[:160]])
out = os.path.join(HERE, "match_audit.csv")
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["run", "id", "posta", "verdict", "F0", "factors", "text"]); w.writerows(rows)
multi = sum(1 for r in rows if "|" in r[5]); none = sum(1 for r in rows if r[5] == "-")
print(f"findings={len(rows)} multi-factor={multi} unmatched={none} -> {out}")
