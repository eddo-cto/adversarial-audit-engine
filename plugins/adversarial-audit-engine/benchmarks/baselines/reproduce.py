#!/usr/bin/env python3
"""
reproduce.py — recompute the baseline positioning from the anonymized data, and
check it against claims.json.

Pure standard library. No install. Run:

    python3 reproduce.py            # print the report, exit 0 if claims hold
    python3 reproduce.py --strict   # same, exit 2 on ANY divergence

WHAT THIS IS. Positioning against open, same-task baselines on the 7 real-error
targets — NOT a leaderboard. It isolates what the engine's DISCIPLINE
(defense-gate, admissibility, declared boundary) adds over an UNDISCIPLINED use of
the same model. Anonymized: no vendor named; only finding counts, landing, and
mechanism class.

  * llm_judge: the same strong model, once with a vanilla "find all the flaws"
    prompt and once under the engine's protocol.
  * statcheck: a deterministic OSS stats-consistency checker (GPL-3.0), narrow.

WHAT IT SHOWS:
  1. discipline does NOT change WHICH targets are caught (landing identical);
  2. it cuts the noise ~5x (fewer findings) — the false-alarm proxy the
     defense-gate suppresses;
  3. the missed targets are exactly the domain-re-derivation class, missed even by
     a 155-finding firehose: the boundary is a property of the task, not discipline.
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    j = load("dataset_llm_judge.csv")
    st = load("dataset_statcheck.csv")
    with open(os.path.join(HERE, "claims.json"), encoding="utf-8") as fh:
        claim = json.load(fh)

    problems: list[str] = []

    def check(label, got, want, tol=0.0):
        ok = abs(got - want) <= tol if tol else got == want
        if not ok:
            problems.append(f"  MISMATCH {label}: got {got}, claimed {want}")

    print("=" * 72)
    print("Baseline positioning — same task, real-error targets (not a leaderboard)")
    print(f"  targets: {len(j)}")
    print("=" * 72)
    check("n_targets", len(j), claim["n_targets"])

    c = claim["llm_judge"]
    sv = sum(int(r["n_vanilla"]) for r in j)
    sd = sum(int(r["n_disciplined"]) for r in j)
    ratios = [int(r["n_vanilla"]) / int(r["n_disciplined"]) for r in j]
    conc = all(r["landing_vanilla"] == r["landing_disciplined"] for r in j)
    lv = sum(int(r["landing_vanilla"]) for r in j)
    ld = sum(int(r["landing_disciplined"]) for r in j)
    dr = [r for r in j if r["mechanism"] == "domain_rederivation"]
    dr_missed = all(r["landing_vanilla"] == "0" and r["landing_disciplined"] == "0"
                    for r in dr)

    print("\n1. DISCIPLINE DOES NOT CHANGE WHICH TARGETS ARE CAUGHT")
    print(f"   landing vanilla {lv}/7  vs  disciplined {ld}/7   identical per-paper: {conc}")
    check("landing_concordance", conc, c["landing_concordance"])
    check("vanilla_landed", lv, c["vanilla_landed"])
    check("disciplined_landed", ld, c["disciplined_landed"])

    print("\n2. IT CUTS THE NOISE (false-alarm proxy)")
    print(f"   findings: vanilla {sv} (mean {sv/7:.1f})  vs  disciplined {sd} (mean {sd/7:.1f})")
    print(f"   over-flagging: overall {sv/sd:.2f}x   per-paper mean {sum(ratios)/len(ratios):.2f}x"
          f"   range [{min(ratios):.1f}x, {max(ratios):.1f}x]")
    check("vanilla_sum", sv, c["vanilla_sum"])
    check("disciplined_sum", sd, c["disciplined_sum"])
    check("overall_ratio", sv / sd, c["overall_over_flagging_ratio"], c["ratio_tol"])
    check("mean_ratio", sum(ratios) / len(ratios), c["per_paper_ratio_mean"], c["mean_tol"])
    check("min_ratio", min(ratios), c["per_paper_ratio_min"], c["range_tol"])
    check("max_ratio", max(ratios), c["per_paper_ratio_max"], c["range_tol"])

    print("\n3. THE BOUNDARY IS THE TASK'S, NOT DISCIPLINE'S")
    print(f"   all domain-re-derivation targets missed by BOTH arms: {dr_missed}")
    check("domain_rederivation_missed_by_both", dr_missed,
          c["domain_rederivation_missed_by_both"])

    s = claim["statcheck"]
    stl = sum(int(r["statcheck_landing"]) for r in st)
    print("\nDETERMINISTIC BASELINE (statcheck, OSS)")
    print(f"   landing {stl}/{len(st)}  (narrow class + format-fragile; class-breadth measure)")
    check("statcheck_landed", stl, s["landed"])

    print("\n" + "=" * 72)
    if problems:
        print("DIVERGENCE from claims.json:")
        print("\n".join(problems))
        print("=" * 72)
        return 2 if args.strict else 1
    print("All baseline-positioning values reproduced from the data. OK.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
