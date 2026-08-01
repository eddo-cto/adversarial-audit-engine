#!/usr/bin/env python3
"""
reproduce.py — recompute the injected-defect calibration headline numbers from
the anonymized per-item data, and check them against claims.json.

Pure standard library. No install. Run:

    python3 reproduce.py            # prints the report, exits 0 if claims hold
    python3 reproduce.py --strict   # same, but exit 2 on ANY divergence

What it verifies (the empirical backing of INVARIANTI_metodo.md §4):
  * present-and-verifiable vs absent detection, one-tailed Fisher exact p
  * reconstructive vs judgment detection, one-tailed Fisher exact p
  * per-operation detection rates
  * false-positive rate + Wilson 95% interval

The lens detects in proportion to what it can reconstruct: it lands on defects
that are PRESENT (a wrong number, an unlicensed claim) and is blind to defects
of ABSENCE (a deleted control, a removed null). That boundary — not a single
accuracy number — is the result, and this script makes it reproducible.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- statistics
def fisher_one_tailed_greater(a: int, b: int, c: int, d: int) -> float:
    """Right-tail Fisher exact for the 2x2 [[a,b],[c,d]] with fixed margins:
    P(X >= a) under the hypergeometric null. Stdlib only."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    hi = min(r1, c1)

    def p(x: int) -> float:
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    return sum(p(x) for x in range(a, hi + 1))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


# ---------------------------------------------------------------- data
def load_rows(name: str) -> list[dict]:
    with open(os.path.join(HERE, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def counts(rows, pred):
    sel = [r for r in rows if pred(r)]
    det = sum(1 for r in sel if r["detected"] == "1")
    return det, len(sel)


# ---------------------------------------------------------------- report
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="exit 2 if any recomputed value diverges from claims.json")
    args = ap.parse_args()

    inj = load_rows("dataset_injections.csv")
    ctl = load_rows("dataset_controls.csv")
    with open(os.path.join(HERE, "claims.json"), encoding="utf-8") as fh:
        claim = json.load(fh)

    problems: list[str] = []

    def check(label, got, want, tol=0):
        ok = abs(got - want) <= tol if tol else got == want
        problems.append("") if ok else problems.append(
            f"  MISMATCH {label}: got {got}, claimed {want}")
        return ok

    print("=" * 70)
    print("Injected-defect calibration — reproduction")
    print(f"  injections: {len(inj)}   controls: {len(ctl)}")
    print("=" * 70)
    check("n_injections", len(inj), claim["n_injections"])
    check("n_controls", len(ctl), claim["n_controls"])

    # present vs absent
    pd_, pt = counts(inj, lambda r: r["mechanistic_class"] == "present")
    ad, at = counts(inj, lambda r: r["mechanistic_class"] == "absent")
    p1 = fisher_one_tailed_greater(pd_, pt - pd_, ad, at - ad)
    pa = claim["present_vs_absent"]
    print(f"\nPRESENT-and-verifiable vs ABSENCE")
    print(f"  present: {pd_}/{pt} = {pd_/pt:.0%}   absent: {ad}/{at} = {ad/at:.0%}")
    print(f"  Fisher one-tailed p = {p1:.4f}   (claimed {pa['fisher_one_tailed_p']})")
    check("present_detected", pd_, pa["present_detected"])
    check("present_total", pt, pa["present_total"])
    check("absent_detected", ad, pa["absent_detected"])
    check("absent_total", at, pa["absent_total"])
    check("present/absent p", p1, pa["fisher_one_tailed_p"], pa["p_tol"])

    # reconstructive vs judgment
    rd, rt = counts(inj, lambda r: r["design_class"] == "reconstructive")
    jd, jt = counts(inj, lambda r: r["design_class"] == "judgment")
    p2 = fisher_one_tailed_greater(rd, rt - rd, jd, jt - jd)
    rj = claim["reconstructive_vs_judgment"]
    print(f"\nRECONSTRUCTIVE vs JUDGMENT")
    print(f"  reconstructive: {rd}/{rt} = {rd/rt:.0%}   judgment: {jd}/{jt} = {jd/jt:.0%}")
    print(f"  Fisher one-tailed p = {p2:.4f}   (claimed {rj['fisher_one_tailed_p']})")
    check("reconstructive_detected", rd, rj["reconstructive_detected"])
    check("reconstructive_total", rt, rj["reconstructive_total"])
    check("judgment_detected", jd, rj["judgment_detected"])
    check("judgment_total", jt, rj["judgment_total"])
    check("recon/judg p", p2, rj["fisher_one_tailed_p"], rj["p_tol"])

    # per operation
    print(f"\nPER OPERATION")
    for op, (cd, ct) in sorted(claim["per_operation"].items()):
        gd, gt = counts(inj, lambda r, o=op: r["operation"] == o)
        print(f"  {op}: {gd}/{gt}   (claimed {cd}/{ct})")
        check(f"{op} detected", gd, cd)
        check(f"{op} total", gt, ct)

    # false positives
    fp = sum(1 for r in ctl if r["false_positive"] == "1")
    lo, hi = wilson(fp, len(ctl))
    fc = claim["false_positives"]
    print(f"\nFALSE POSITIVES")
    print(f"  {fp}/{len(ctl)} = {fp/len(ctl):.1%}   Wilson95 [{lo:.1%}, {hi:.1%}]")
    check("fp", fp, fc["fp"])
    check("fp_n", len(ctl), fc["n"])
    check("wilson_lo", lo, fc["wilson95_lo"], fc["ci_tol"])
    check("wilson_hi", hi, fc["wilson95_hi"], fc["ci_tol"])

    problems = [p for p in problems if p]
    print("\n" + "=" * 70)
    if problems:
        print("DIVERGENCE from claims.json:")
        print("\n".join(problems))
        print("=" * 70)
        return 2 if args.strict else 1
    print("All headline numbers reproduced from the data. OK.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
