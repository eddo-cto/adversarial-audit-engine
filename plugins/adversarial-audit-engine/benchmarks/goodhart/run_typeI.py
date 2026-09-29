"""
run_typeI.py — the Type-I control run (live). The mandatory companion to the H1 escape run.

A low escape means nothing on its own: an auditor that condemns EVERYTHING has escape 0 and false-positive 1.
This runner feeds the EngineAuditor a MIX of true (gold VALID) and false (gold INVALID) arith claims, and
reports, per pressure:
  - escape        = among gold==INVALID, fraction CLEARED  (should be LOW if the defences work)
  - false_positive = among gold==VALID,   fraction CONDEMNED (must ALSO be LOW, else the low escape is a fraud)
Only LOW escape AND LOW false-positive together = genuine competence.

Usage (from plugins/adversarial-audit-engine/):
  python benchmarks/goodhart/run_typeI.py --model qwen2.5:7b --eye-model llama3.1:8b --cell defenses_on \
         --pressures 4,8 --k 15 --seeds 3 --p-valid 0.5 --out benchmarks/goodhart/typeI_on.json
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", ".."))          # aae (plugin root)
sys.path.insert(0, _HERE)

import analysis as A            # noqa: E402
import auditor_engine as AE     # noqa: E402
import forger as F              # noqa: E402
import gold_mechanical as G     # noqa: E402
import harness as H             # noqa: E402
import ollama_client as OC      # noqa: E402
import role_runner as RR        # noqa: E402
from run_pilot import _cell     # noqa: E402  (reuse the preset->cell mapping)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--eye-model", default="")
    ap.add_argument("--cell", default="defenses_on")
    ap.add_argument("--pressures", default="4,8")
    ap.add_argument("--k", type=int, default=15)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--p-valid", type=float, default=0.5)
    ap.add_argument("--host", default=OC.DEFAULT_HOST)
    ap.add_argument("--out", default=os.path.join(_HERE, "typeI_out.json"))
    args = ap.parse_args(argv)

    pressures = [int(x) for x in args.pressures.split(",") if x.strip() != ""]
    cell = _cell(args.cell)
    gold = G.MechanicalGold()
    chat = OC.make_chat(args.model, host=args.host)
    eye = RR.make_eye(OC.make_chat(args.eye_model, host=args.host)) if args.eye_model else None
    auditor = AE.EngineAuditor(role_runner=RR.RoleRunner(chat, internal_identity=f"ollama-local:{args.model}"),
                               eye=eye, eye_identity=f"ollama-local:{args.eye_model or 'none'}")

    per_p = {p: {"escape": [], "fp": []} for p in pressures}
    for seed in range(args.seeds):
        recs = H.run_cell(F.MixedArithForger(seed=seed, p_valid=args.p_valid), gold, auditor, cell,
                          pressure_levels=pressures, k=args.k)
        line = []
        for p in pressures:
            sub = [r for r in recs if r.get("pressure") == p]
            er = A.escape_rate(sub)["rate"]
            fp = A.false_positive_rate(sub)["rate"]
            per_p[p]["escape"].append(er); per_p[p]["fp"].append(fp)
            line.append(f"P{p} esc={er:.2f} fp={fp:.2f}")
        print(f"seed {seed}: " + "  ".join(line))

    def agg(vals):
        vals = [v for v in vals if v == v]   # drop NaN
        return {"mean": (statistics.mean(vals) if vals else float("nan")),
                "stdev": (statistics.stdev(vals) if len(vals) > 1 else 0.0)}
    curve = {p: {"escape": agg(per_p[p]["escape"]), "false_positive": agg(per_p[p]["fp"])} for p in pressures}
    result = {"model": args.model, "eye_model": args.eye_model, "cell": args.cell, "p_valid": args.p_valid,
              "pressures": pressures, "k": args.k, "seeds": args.seeds, "curve": curve}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print("\n=== escape (want LOW) + false-positive (want LOW) ===")
    for p in pressures:
        c = curve[p]
        print(f"  P{p}: escape {c['escape']['mean']:.3f} (±{c['escape']['stdev']:.3f})   "
              f"false-positive {c['false_positive']['mean']:.3f} (±{c['false_positive']['stdev']:.3f})")
    print(f"written: {args.out}")
    print("Read: LOW escape + LOW false-positive = genuine competence; HIGH false-positive = the eye just "
          "condemns everything and the low escape is a fraud.")


if __name__ == "__main__":
    main()
