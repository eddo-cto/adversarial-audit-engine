#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analyze_2x2.py — pre-registered analysis for the capability×independence 2x2 (§6 strengthening).

Implements the FROZEN analysis of PREREG_empirical_strengthening.md, effect-size-first,
standard library only (no numpy/scipy — same discipline as the rest of the engine):

  * per-cell recovery per mechanism class, with run-to-run spread;
  * the two pre-registered contrasts:
      - IND effect on ED at fixed CAP  (H1, independence axis);
      - CAP effect on DR at fixed IND  (H2, capability axis);
    plus the two CROSS-effects (IND on DR, CAP on ED) that must be near-null;
  * a two-sided PERMUTATION test for each contrast (permute the factor label within class);
  * a bootstrap CI (resampling targets) for each contrast;
  * the frozen DECISION RULE -> {DISSOCIATION_CONFIRMED, SINGLE_AXIS, NULL, INCONCLUSIVE_SPECIFICITY}.

This file is written BEFORE the data exist; `--selftest` runs it on synthetic data that
instantiate (i) a clean dissociation and (ii) a single-axis confound, and checks the verdict
each time — so the machinery is validated independently of any real result.

Input schema (landings CSV, one row per target×run):
    target_id,class,CAP,IND,run_idx,land
      class ∈ {GR,ED,DR}   CAP ∈ {low,high}   IND ∈ {low,high}   land ∈ {0,1}
Decoys CSV (one row per decoy×cell×run):
    decoy_id,CAP,IND,run_idx,false_positive

Usage:
    python3 analyze_2x2.py landings.csv decoys.csv
    python3 analyze_2x2.py --selftest
"""
from __future__ import annotations
import csv, itertools, random, statistics, sys
from collections import defaultdict

CLASSES = ("GR", "ED", "DR")
N_PERM = 10000
N_BOOT = 5000
ALPHA = 0.05
SEED = 20260808


# ----------------------------- data model -----------------------------------

def _rows_no_comments(path):
    """DictReader over the file, skipping blank lines and '#'-comment lines."""
    with open(path, newline="", encoding="utf-8") as fh:
        lines = [ln for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
    return list(csv.DictReader(lines))


def _read_landings(path):
    return [{"target": r["target_id"], "class": r["class"].strip().upper(),
             "CAP": r["CAP"].strip().lower(), "IND": r["IND"].strip().lower(),
             "run": int(r["run_idx"]), "land": int(r["land"])}
            for r in _rows_no_comments(path)]


def _read_decoys(path):
    return [{"CAP": r["CAP"].strip().lower(), "IND": r["IND"].strip().lower(),
             "fp": int(r["false_positive"])}
            for r in _rows_no_comments(path)]


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


# ----------------------- recovery, contrasts --------------------------------

def recovery(rows, *, cls=None, CAP=None, IND=None):
    """Mean landing over the selected slice (targets × runs)."""
    sel = [r["land"] for r in rows
           if (cls is None or r["class"] == cls)
           and (CAP is None or r["CAP"] == CAP)
           and (IND is None or r["IND"] == IND)]
    return _mean(sel)


def contrast_ind_on(rows, cls, cap):
    """IND+ minus IND- on `cls`, holding CAP=cap fixed."""
    return recovery(rows, cls=cls, CAP=cap, IND="high") - recovery(rows, cls=cls, CAP=cap, IND="low")


def contrast_cap_on(rows, cls, ind):
    """CAP+ minus CAP- on `cls`, holding IND=ind fixed."""
    return recovery(rows, cls=cls, IND=ind, CAP="high") - recovery(rows, cls=cls, IND=ind, CAP="low")


def pooled_ind_on(rows, cls):
    return _mean([contrast_ind_on(rows, cls, c) for c in ("low", "high")])


def pooled_cap_on(rows, cls):
    return _mean([contrast_cap_on(rows, cls, i) for i in ("low", "high")])


# --------------------------- permutation test -------------------------------

def _perm_p(rows, cls, factor, observed, rng):
    """Two-sided permutation p: shuffle `factor` labels within `cls`, recompute pooled contrast.

    The pooled contrast averages the factor effect over the OTHER factor's two levels, exactly as
    pooled_ind_on / pooled_cap_on do on the observed data.
    """
    sub = [dict(r) for r in rows if r["class"] == cls]
    labels = [r[factor] for r in sub]
    hits = 0
    for _ in range(N_PERM):
        rng.shuffle(labels)
        for r, l in zip(sub, labels):
            r[factor] = l
        if factor == "IND":
            stat = _mean([recovery(sub, CAP=o, IND="high") - recovery(sub, CAP=o, IND="low")
                          for o in ("low", "high")])
        else:
            stat = _mean([recovery(sub, IND=o, CAP="high") - recovery(sub, IND=o, CAP="low")
                          for o in ("low", "high")])
        if abs(stat) >= abs(observed) - 1e-12:
            hits += 1
    return (hits + 1) / (N_PERM + 1)


# ------------------------------ bootstrap -----------------------------------

def _bootstrap_ci(rows, cls, factor, rng):
    """Percentile CI for the pooled contrast, resampling TARGETS (the unit of independence)."""
    by_target = defaultdict(list)
    for r in rows:
        if r["class"] == cls:
            by_target[r["target"]].append(r)
    targets = list(by_target)
    if len(targets) < 2:
        return (float("nan"), float("nan"))
    stats = []
    for _ in range(N_BOOT):
        boot = []
        for _ in targets:
            boot.extend(by_target[rng.choice(targets)])
        stats.append(pooled_ind_on(boot, cls) if factor == "IND" else pooled_cap_on(boot, cls))
    stats.sort()
    lo = stats[int((ALPHA / 2) * len(stats))]
    hi = stats[int((1 - ALPHA / 2) * len(stats)) - 1]
    return (lo, hi)


# ------------------------------- verdict ------------------------------------

def analyze(landings, decoys):
    rng = random.Random(SEED)
    out = {"per_cell": {}, "contrasts": {}, "specificity": {}}

    for cls, cap, ind in itertools.product(CLASSES, ("low", "high"), ("low", "high")):
        out["per_cell"][f"{cls}|CAP={cap}|IND={ind}"] = round(recovery(
            landings, cls=cls, CAP=cap, IND=ind), 4)

    # primary + cross contrasts
    prim_ind_ED = pooled_ind_on(landings, "ED")     # H1 primary
    prim_cap_DR = pooled_cap_on(landings, "DR")     # H2 primary
    cross_ind_DR = pooled_ind_on(landings, "DR")    # must be ~0
    cross_cap_ED = pooled_cap_on(landings, "ED")    # must be ~0

    out["contrasts"] = {
        "H1_IND_on_ED": {"est": round(prim_ind_ED, 4),
                         "ci": [round(x, 4) for x in _bootstrap_ci(landings, "ED", "IND", rng)],
                         "perm_p": round(_perm_p(landings, "ED", "IND", prim_ind_ED, rng), 4)},
        "H2_CAP_on_DR": {"est": round(prim_cap_DR, 4),
                         "ci": [round(x, 4) for x in _bootstrap_ci(landings, "DR", "CAP", rng)],
                         "perm_p": round(_perm_p(landings, "DR", "CAP", prim_cap_DR, rng), 4)},
        "cross_IND_on_DR": {"est": round(cross_ind_DR, 4)},
        "cross_CAP_on_ED": {"est": round(cross_cap_ED, 4)},
    }

    fp_rate = _mean([d["fp"] for d in decoys]) if decoys else 0.0
    out["specificity"] = {"decoy_fp_rate": round(fp_rate, 4), "ok": fp_rate <= 0.02}

    # run-to-run spread (a primary effect must exceed it)
    def run_spread(cls):
        by_run = defaultdict(list)
        for r in landings:
            if r["class"] == cls:
                by_run[r["run"]].append(r["land"])
        per = [_mean(v) for v in by_run.values()]
        return statistics.pstdev(per) if len(per) > 1 else 0.0
    out["run_spread"] = {"ED": round(run_spread("ED"), 4), "DR": round(run_spread("DR"), 4)}

    # ---- frozen decision rule (PREREG §6) ----
    c = out["contrasts"]
    ci1, ci2 = c["H1_IND_on_ED"]["ci"], c["H2_CAP_on_DR"]["ci"]
    h1 = ci1[0] > 0 and prim_ind_ED > out["run_spread"]["ED"]
    h2 = ci2[0] > 0 and prim_cap_DR > out["run_spread"]["DR"]
    cross_null = (abs(cross_ind_DR) < prim_cap_DR) and (abs(cross_cap_ED) < prim_ind_ED)
    if not out["specificity"]["ok"]:
        verdict = "INCONCLUSIVE_SPECIFICITY"
    elif h1 and h2 and cross_null:
        verdict = "DISSOCIATION_CONFIRMED"
    elif (cross_ind_DR >= prim_cap_DR) or (cross_cap_ED >= prim_ind_ED):
        verdict = "SINGLE_AXIS"
    else:
        verdict = "NULL"
    out["verdict"] = verdict
    return out


# ------------------------------- selftest -----------------------------------

def _synthesize(kind, rng, per_class=6, k=4):
    """Generate landings for a known ground truth.
    kind='dissociation': IND lifts ED only; CAP lifts DR only.
    kind='single_axis' : one factor (say IND) lifts BOTH ED and DR."""
    rows, decoys = [], []
    def p_land(cls, cap, ind):
        if cls == "GR":
            return 0.95
        if kind == "dissociation":
            if cls == "ED":
                return {"low": 0.1, "high": 0.85}[ind]
            if cls == "DR":
                return {"low": 0.1, "high": 0.85}[cap]
        else:  # single_axis: IND drives everything
            if cls in ("ED", "DR"):
                return {"low": 0.1, "high": 0.85}[ind]
        return 0.1
    tid = 0
    for cls in CLASSES:
        for _ in range(per_class):
            tid += 1
            for cap, ind in itertools.product(("low", "high"), ("low", "high")):
                for run in range(k):
                    rows.append({"target": f"T{tid}", "class": cls, "CAP": cap, "IND": ind,
                                 "run": run, "land": 1 if rng.random() < p_land(cls, cap, ind) else 0})
    for j in range(per_class):
        for cap, ind in itertools.product(("low", "high"), ("low", "high")):
            for run in range(k):
                decoys.append({"CAP": cap, "IND": ind, "fp": 1 if rng.random() < 0.005 else 0})
    return rows, decoys


def selftest():
    rng = random.Random(SEED)
    ok = True
    for kind, expected in (("dissociation", "DISSOCIATION_CONFIRMED"),
                           ("single_axis", "SINGLE_AXIS")):
        rows, dec = _synthesize(kind, rng)
        res = analyze(rows, dec)
        got = res["verdict"]
        flag = "OK" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"[selftest] ground-truth={kind:12s} -> verdict={got:26s} expected={expected:26s} {flag}")
        print(f"           H1(IND->ED)={res['contrasts']['H1_IND_on_ED']['est']:+.2f} "
              f"ci={res['contrasts']['H1_IND_on_ED']['ci']} p={res['contrasts']['H1_IND_on_ED']['perm_p']} | "
              f"H2(CAP->DR)={res['contrasts']['H2_CAP_on_DR']['est']:+.2f} "
              f"ci={res['contrasts']['H2_CAP_on_DR']['ci']} p={res['contrasts']['H2_CAP_on_DR']['perm_p']}")
        print(f"           cross IND->DR={res['contrasts']['cross_IND_on_DR']['est']:+.2f} "
              f"CAP->ED={res['contrasts']['cross_CAP_on_ED']['est']:+.2f} "
              f"decoy_fp={res['specificity']['decoy_fp_rate']}")
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv):
    if len(argv) == 2 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 3:
        print(__doc__); return 2
    res = analyze(_read_landings(argv[1]), _read_decoys(argv[2]))
    import json
    print(json.dumps(res, indent=2))
    print("\nVERDICT:", res["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
