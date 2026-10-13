#!/usr/bin/env python3
"""forms_replay.py — offline comparison of candidate verdict/presentation FORMS on real payloads (no LLM).

Each FORM is a deterministic policy over the core's (1.18) ledger: it decides how every finding would be PRESENTED to
the human (`defect` | `open` | `solid`). Findings are mapped to pre-registered MATERIAL FACTORS of the artefact by a
fixed keyword matcher (factors.json); the human gold (gold.json, filled by the L4 reviewer, NOT by the auditor or by
whoever wrote the forms) says which factors must NOT be presented as solid. Metrics per form:

  M1 material recall  — share of gold-"non-solid" factors that the form presents as non-solid (omissions = 1 - M1)
  M2 false solidity   — share of gold-"non-solid" factors presented as SOLID (the dangerous error)
  M3 false demolition — share of gold-"solid" factors presented as DEFECT
  M4 human load       — mean number of findings the human must read (defect + open) per run
  M5 stability        — std of M1 across runs (lower = more reproducible)

Forms (from LETTERATURA_A/C):
  F0  baseline 1.18: held → solid, unless DEFENSE LEVER or UNSETTLED (→ open)
  F1  whitelist rebuttal: held → solid ONLY if the defense carries a verbatim quote (>=20 chars) grounded in the source
  F2  class-targeted (Hazel): F1 applied only to HIGH-posta findings; others as F0
  F3k aggregation over the k runs of the same artefact: a factor is non-solid if non-solid in >= m runs (base F0 / F1)
Without gold.json only M4/M5-independent descriptives are printed.

Usage: python forms_replay.py <runs_root> [--gold gold.json] [--factors factors.json]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from aae.pipeline import discipline            # noqa: E402
from aae.referto_guard import _must_be_open     # noqa: E402

_QUOTE = re.compile(r"[«\"“']([^«»\"“”']{20,})[»\"”']")
_CONDEMN = {"accusa_vince", "accusa_ridimensionata"}
_ABSTAIN = {"da_leggere", "conteso", "pending"}


def _norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def grounded_rebuttal(f, src) -> bool:
    fact = (f.defense.fact or "") if f.defense else ""
    n = _norm(src)
    return any(len(q.strip()) >= 20 and _norm(q) in n for q in _QUOTE.findall(fact))


def present(ledger, src, form):
    """{finding_id: 'defect'|'open'|'solid'} for the given form."""
    must_open = _must_be_open(ledger)
    out = {}
    for f in ledger.findings:
        if f.action_state.value == "deliberately_discarded":
            continue
        v = f.verdict.value
        if v in _CONDEMN:
            out[f.id] = "defect"
        elif v in _ABSTAIN:
            out[f.id] = "open"
        else:  # artefatto_regge
            if form == "F0":
                out[f.id] = "open" if f.id in must_open else "solid"
            elif form == "F1":
                out[f.id] = "solid" if grounded_rebuttal(f, src) and f.id not in must_open else "open"
            elif form == "F2":
                if f.posta.value == "high":
                    out[f.id] = "solid" if grounded_rebuttal(f, src) and f.id not in must_open else "open"
                else:
                    out[f.id] = "open" if f.id in must_open else "solid"
    return out


def factor_status(ledger, pres, factors):
    """{factor: 'defect'|'open'|'solid'|'absent'}: worst presentation among the findings matched to the factor
    (defect > open > solid). Matching = fixed, pre-registered regexes on element + accusation text."""
    st = {}
    for name, pats in factors.items():
        rx = [re.compile(p, re.I) for p in pats]
        hit = []
        for f in ledger.findings:
            if f.id not in pres:
                continue
            text = _norm((f.element or "") + " " + (f.accusation.text or ""))
            if any(r.search(text) for r in rx):
                hit.append(pres[f.id])
        if not hit:
            st[name] = "absent"
        elif "defect" in hit:
            st[name] = "defect"
        elif "open" in hit:
            st[name] = "open"
        else:
            st[name] = "solid"
    return st


def load_runs(root):
    paths = sorted(glob.glob(os.path.join(root, "20261012_RN-EI-95-2025", "findings.json")) +
                   glob.glob(os.path.join(root, "AB*_RN95_*", "*", "findings.json")))
    runs = []
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        os.environ.pop("AAE_EXTERNAL_ATTESTED_IDENTITY", None)
        led = discipline(d).ledger
        runs.append((os.path.relpath(os.path.dirname(p), root), led, d.get("source_text", "")))
    return runs


def metrics(statuses, loads, gold):
    """statuses: list of {factor: status} (one per run or one aggregate). gold: {factor: 'non-solid'|'solid'}."""
    m1, m2, m3 = [], [], []
    ns = [k for k, v in gold.items() if v == "non-solid"]
    so = [k for k, v in gold.items() if v == "solid"]
    for st in statuses:
        if ns:
            m1.append(sum(st.get(k) in ("defect", "open") for k in ns) / len(ns))
            m2.append(sum(st.get(k) == "solid" for k in ns) / len(ns))
        if so:
            m3.append(sum(st.get(k) == "defect" for k in so) / len(so))
    r = lambda xs: round(statistics.mean(xs), 3) if xs else None
    return {"M1_recall": r(m1), "M2_false_solid": r(m2), "M3_false_demol": r(m3),
            "M4_load": round(statistics.mean(loads), 1) if loads else None,
            "M5_std_M1": round(statistics.pstdev(m1), 3) if len(m1) > 1 else 0.0}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_root")
    ap.add_argument("--factors", default=os.path.join(HERE, "factors_rn95.json"))
    ap.add_argument("--gold", default=os.path.join(HERE, "gold_rn95.json"))
    a = ap.parse_args(argv)
    factors = {k: v for k, v in json.load(open(a.factors, encoding="utf-8")).items() if not k.startswith("_")}
    gold = None
    if os.path.exists(a.gold):
        g = json.load(open(a.gold, encoding="utf-8"))
        gold = {k: v for k, v in g.get("labels", {}).items() if v in ("non-solid", "solid")}
    runs = load_runs(a.runs_root)
    report = {"runs": [r[0] for r in runs], "forms": {}}
    for form in ("F0", "F1", "F2"):
        per_run, loads = [], []
        for name, led, src in runs:
            pres = present(led, src, form)
            loads.append(sum(1 for v in pres.values() if v != "solid"))
            per_run.append(factor_status(led, pres, factors))
        entry = {"per_run_factor_status": dict(zip(report["runs"], per_run)),
                 "absent_rate": round(statistics.mean(sum(v == "absent" for v in s.values()) / len(s)
                                                      for s in per_run), 3)}
        if gold:
            entry["metrics_single_run"] = metrics(per_run, loads, gold)
            for m in (1, 2):   # F3: aggregate over all runs, threshold m
                agg = {}
                for k in factors:
                    c = sum(s[k] in ("defect", "open") for s in per_run)
                    d = sum(s[k] == "defect" for s in per_run)
                    agg[k] = ("defect" if d >= m else "open") if c >= m else \
                             ("solid" if any(s[k] == "solid" for s in per_run) else "absent")
                entry[f"metrics_F3_m{m}_over_{len(per_run)}"] = metrics([agg], [sum(loads)], gold)
        else:
            entry["load_mean"] = round(statistics.mean(loads), 1)
        report["forms"][form] = entry
    out = os.path.join(HERE, "forms_replay_report.json")
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for form, e in report["forms"].items():
        print(form, {k: v for k, v in e.items() if k != "per_run_factor_status"})
    print("written:", out)


if __name__ == "__main__":
    main()
