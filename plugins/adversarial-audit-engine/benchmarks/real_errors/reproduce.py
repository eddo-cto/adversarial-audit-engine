#!/usr/bin/env python3
"""
reproduce.py — recompute the real-error validation from the anonymized per-target
data, and check it against claims.json.

Pure standard library. No install. Run:

    python3 reproduce.py            # print the report, exit 0 if claims hold
    python3 reproduce.py --strict   # same, exit 2 on ANY divergence

WHAT THIS IS. Ground truth = published *Matters Arising* (a formal refutation
written by a third-party domain expert). The lens audited only the ORIGINAL
paper, blind, never the refutation. This is **method calibration**, not detector
performance: the headline is the discipline (near-zero false positives + a
declarable boundary), and the sensitivity number is the honest calibration of a
GENERAL-REASONING auditor on real errors — it is not "how good the product is."

WHAT IT SHOWS.
  1. Specificity — 0 false positives on cross-domain decoys (the transferable,
     method-level virtue: it does not hallucinate).
  2. The boundary — it lands only on defects reconstructible from the text by
     general reasoning; it misses defects needing domain re-derivation or
     external data (its declared out-of-scope class).
  3. Honest calibration — real P-class recall vs the synthetic 88%: the drop is
     signal, and it is why the synthetic estimate is not oversold.

Everything depends only on (class, mechanism, landed) — never on a paper's
identity, which stays in the private sealed registers.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def landed(rows, pred):
    sel = [r for r in rows if pred(r)]
    return sum(1 for r in sel if r["landed"] == "1"), len(sel)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="exit 2 if any recomputed value diverges from claims.json")
    args = ap.parse_args()

    tgt = load("dataset_targets.csv")
    dec = load("dataset_decoys.csv")
    with open(os.path.join(HERE, "claims.json"), encoding="utf-8") as fh:
        claim = json.load(fh)

    problems: list[str] = []

    def check(label, got, want):
        if got != want:
            problems.append(f"  MISMATCH {label}: got {got}, claimed {want}")

    print("=" * 70)
    print("Real-error validation (Matters Arising ground truth)")
    print("  METHOD CALIBRATION — not detector performance")
    print(f"  targets: {len(tgt)}   cross-domain decoys: {len(dec)}")
    print("=" * 70)
    check("n_targets", len(tgt), claim["n_targets"])
    check("n_decoys", len(dec), claim["n_decoys"])

    # 1. specificity — the headline virtue
    fp = sum(1 for r in dec if r["false_positive"] == "1")
    sp = claim["specificity"]
    print("\n1. SPECIFICITY (does not hallucinate) — the transferable virtue")
    print(f"   false positives on cross-domain decoys: {fp}/{len(dec)}")
    check("decoy_false_positives", fp, sp["decoy_false_positives"])

    # 2. the boundary
    gl, gt = landed(tgt, lambda r: r["mechanism"] == "general_reasoning")
    dl, dt = landed(tgt, lambda r: r["mechanism"] == "domain_rederivation")
    el, et = landed(tgt, lambda r: r["mechanism"] == "external_data")
    b = claim["boundary"]
    print("\n2. THE BOUNDARY (lands on reconstructible-by-general-reasoning only)")
    print(f"   general reasoning (arith/contradiction/entailment): {gl}/{gt}")
    print(f"   needs domain re-derivation:                         {dl}/{dt}")
    print(f"   needs external data:                                {el}/{et}")
    check("general_reasoning_landed", gl, b["general_reasoning_landed"])
    check("general_reasoning_total", gt, b["general_reasoning_total"])
    check("domain_rederivation_landed", dl, b["domain_rederivation_landed"])
    check("domain_rederivation_total", dt, b["domain_rederivation_total"])
    check("external_data_landed", el, b["external_data_landed"])
    check("external_data_total", et, b["external_data_total"])

    # 3. honest calibration
    pl, pt = landed(tgt, lambda r: r["target_class"] == "P")
    sc = claim["sensitivity_calibration"]
    syn_l = sc["synthetic_present_verifiable_landed"]
    syn_t = sc["synthetic_present_verifiable_total"]
    print("\n3. HONEST CALIBRATION (synthetic -> real, kept honest)")
    print(f"   real P-class recall:        {pl}/{pt} = {pl/pt:.0%}")
    print(f"   synthetic present-verifiable: {syn_l}/{syn_t} = {syn_l/syn_t:.0%}"
          f"  (benchmarks/calibration)")
    print(f"   the drop {syn_l/syn_t:.0%} -> {pl/pt:.0%} is signal: the synthetic "
          "P defects were simple; the real ones need domain re-derivation.")
    check("real_P_landed", pl, sc["real_P_landed"])
    check("real_P_total", pt, sc["real_P_total"])

    # caveats, stated not hidden
    adj = [r["id"] for r in tgt if r["adjudicator_dependent"] == "1"]
    ext = [r["id"] for r in tgt if r["extraction_confound"] == "1"]
    print("\nCAVEATS (declared, not hidden)")
    print(f"   n = {len(tgt)} — too small for significance; this circumscribes, "
          "does not certify")
    print(f"   adjudicator-dependent target(s): {adj or 'none'} "
          "(class A, near-miss vs landing across two adjudicators)")
    print(f"   extraction-confounded target(s): {ext or 'none'} "
          "(governing equation lost in text extraction; recompute not possible)")
    print("   single model nature — no number reaches VALIDATED without the "
          "external inter-nature axis")

    print("\n" + "=" * 70)
    if problems:
        print("DIVERGENCE from claims.json:")
        print("\n".join(problems))
        print("=" * 70)
        return 2 if args.strict else 1
    print("All values reproduced from the data. OK.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
