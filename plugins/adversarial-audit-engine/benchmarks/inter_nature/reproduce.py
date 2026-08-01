#!/usr/bin/env python3
"""
reproduce.py — recompute the inter-nature check from the anonymized per-target,
per-nature landing data, and check it against claims.json.

Pure standard library. No install. Run:

    python3 reproduce.py            # print the report, exit 0 if claims hold
    python3 reproduce.py --strict   # same, exit 2 on ANY divergence

WHAT THIS IS. The single test the engine cannot run on itself: every instance it
can launch shares one nature, so intra-nature agreement -> 1 proves nothing about
independence. Here the SAME 7 real-error targets (Matters Arising ground truth)
were audited BLIND by three natures — A = the engine's own, B and C = two
different-vendor models — and adjudicated by a fresh blind instance. Anonymized:
no vendor names, no paper identities; only (mechanism, per-nature landing).

WHAT IT CERTIFIES (the three frontier predictions):
  1. the declarable boundary is nature-independent — all natures land only on the
     general-reasoning-reconstructible defect and miss the domain-re-derivation
     ones, identically;
  2. a different nature ADDS real findings the engine's own nature missed (rho<1),
     and the gain is not saturated;
  3. the low-false-positive discipline survives independence — 0 decoy false
     positives for every nature.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NATURES = ("nature_A", "nature_B", "nature_C")


def load(name):
    with open(os.path.join(HERE, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def landed(rows, nat, mechanism):
    sel = [r for r in rows if r["mechanism"] == mechanism]
    return sum(int(r[nat]) for r in sel), len(sel)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="exit 2 if any recomputed value diverges from claims.json")
    args = ap.parse_args()

    land = load("dataset_landings.csv")
    dec = load("dataset_decoys.csv")
    with open(os.path.join(HERE, "claims.json"), encoding="utf-8") as fh:
        claim = json.load(fh)

    problems: list[str] = []

    def check(label, got, want):
        if got != want:
            problems.append(f"  MISMATCH {label}: got {got}, claimed {want}")

    print("=" * 72)
    print("Inter-nature check — the test the engine cannot run on itself")
    print(f"  targets: {len(land)}   natures: {len(NATURES)}")
    print("=" * 72)
    check("n_targets", len(land), claim["n_targets"])

    # 1. boundary reproduces across natures
    b = claim["boundary_reproduces_across_natures"]
    print("\n1. THE BOUNDARY IS NATURE-INDEPENDENT")
    for nat in NATURES:
        gl, gt = landed(land, nat, "general_reasoning")
        dl, dt = landed(land, nat, "domain_rederivation")
        print(f"   {nat}: general-reasoning {gl}/{gt}   domain-re-derivation {dl}/{dt}")
        check(f"{nat} general_reasoning", gl,
              b["general_reasoning_landed_per_nature"][nat])
        check(f"{nat} domain_rederivation", dl,
              b["domain_rederivation_landed_per_nature"][nat])
    P = [r for r in land if r["mechanism"] in ("general_reasoning", "domain_rederivation")]
    vectors = {nat: tuple(r[nat] for r in P) for nat in NATURES}
    identical = len(set(vectors.values())) == 1
    print(f"   P-target landing vectors identical across natures: {identical}")
    check("p_target_vectors_identical", identical, b["p_target_vectors_identical"])

    # 2. different nature adds on A-class
    a = claim["different_nature_adds_on_A_class"]
    print("\n2. A DIFFERENT NATURE ADDS REAL FINDINGS (rho<1)")
    seq = []
    for nat in NATURES:
        el, et = landed(land, nat, "external_data")
        seq.append(el)
        print(f"   {nat}: external-data (A-class) {el}/{et}")
        check(f"{nat} external_data", el, a["external_data_landed_per_nature"][nat])
    monotone = all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))
    print(f"   monotone non-decreasing A<=B<=C: {monotone}  ({'<='.join(map(str, seq))})")
    check("monotone_non_decreasing", monotone, a["monotone_non_decreasing"])

    # 3. specificity survives
    s = claim["specificity_survives"]
    print("\n3. SPECIFICITY SURVIVES INDEPENDENCE (0 decoy false positives)")
    fpmap = {r["nature"]: int(r["decoy_false_positives"]) for r in dec}
    for nat in NATURES:
        n = next(int(r["n_decoys"]) for r in dec if r["nature"] == nat)
        print(f"   {nat}: {fpmap[nat]}/{n} false positives on cross-domain decoys")
        check(f"{nat} decoy_fp", fpmap[nat],
              s["decoy_false_positives_per_nature"][nat])

    print("\n" + "=" * 72)
    if problems:
        print("DIVERGENCE from claims.json:")
        print("\n".join(problems))
        print("=" * 72)
        return 2 if args.strict else 1
    print("All inter-nature claims reproduced from the data. OK.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
