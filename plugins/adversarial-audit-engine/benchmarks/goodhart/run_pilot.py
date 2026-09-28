"""
run_pilot.py — the Goodhart mini-pilot runner (live). Wires the whole loop over Ollama.

One ablation cell x pressure levels x seeds, engine-auditor (roles on a local Ollama model) vs the mechanical
gold, deterministic forger. Writes the escape curve + per-seed variance to JSON so N can be re-tuned before
the full run. This is the ONLY script that needs a running `ollama serve`.

Usage (from plugins/adversarial-audit-engine/):
  python benchmarks/goodhart/run_pilot.py --model qwen2.5:7b --cell defenses_off \
         --pressures 0,1,2,4,8 --k 30 --seeds 3 --out benchmarks/goodhart/pilot_out.json

The forger is mechanical (no model). The auditor's roles run on --model. Keep --cell defenses_off for the
first plumbing/floor pilot; add cross_vendor later with an actual second-vendor eye.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", ".."))          # aae (plugin root)
sys.path.insert(0, _HERE)                                    # sibling goodhart modules

import analysis as A            # noqa: E402
import auditor_engine as AE     # noqa: E402
import forger as F              # noqa: E402
import gold_mechanical as G     # noqa: E402
import harness as H             # noqa: E402
import ollama_client as OC      # noqa: E402
import role_runner as RR        # noqa: E402

_CELLS = {c.name: c for c in H.DEFAULT_CELLS} if hasattr(H, "DEFAULT_CELLS") else {}


def _cell(name: str):
    if name in _CELLS:
        return _CELLS[name]
    presets = {
        "defenses_off": dict(eye=False, axes=False, governor=False),
        "defenses_on":  dict(eye=True, axes=True, governor=True),
        "cross_vendor": dict(eye=True, axes=True, governor=True, eye_mode="cross_vendor"),
        "cross_seed":   dict(eye=True, axes=True, governor=True, eye_mode="cross_seed"),
    }
    return H.AblationCell(name, **presets.get(name, presets["defenses_off"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Ollama model for the auditor roles, e.g. qwen2.5:7b")
    ap.add_argument("--eye-model", default="", help="different-vendor model for the eye, e.g. llama3.1:8b; empty = no eye")
    ap.add_argument("--cell", default="defenses_off")
    ap.add_argument("--pressures", default="0,1,2,4,8")
    ap.add_argument("--k", type=int, default=30)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--host", default=OC.DEFAULT_HOST)
    ap.add_argument("--out", default=os.path.join(_HERE, "pilot_out.json"))
    args = ap.parse_args(argv)

    pressures = [int(x) for x in args.pressures.split(",") if x.strip() != ""]
    cell = _cell(args.cell)
    gold = G.MechanicalGold()
    chat = OC.make_chat(args.model, host=args.host)
    eye = None
    if args.eye_model:
        eye = RR.make_eye(OC.make_chat(args.eye_model, host=args.host))    # a REAL different-vendor eye
    auditor = AE.EngineAuditor(role_runner=RR.RoleRunner(chat, internal_identity=f"ollama-local:{args.model}"),
                               eye=eye, eye_identity=f"ollama-local:{args.eye_model or 'none'}")

    per_pressure = {p: [] for p in pressures}     # pooled escape rate across seeds
    per_seed_at_max = []                          # escape at max pressure, one per seed (variance estimate)
    for seed in range(args.seeds):
        recs = H.run_cell(F.MechanicalArithForger(seed=seed), gold, auditor, cell,
                          pressure_levels=pressures, k=args.k)
        by_p = {}
        for p in pressures:
            sub = [r for r in recs if r.get("pressure") == p]
            er = A.escape_rate(sub)
            per_pressure[p].append(er["rate"])
            by_p[p] = er["rate"]
        per_seed_at_max.append(by_p[pressures[-1]])
        print(f"seed {seed}: " + "  ".join(f"P{p}={by_p[p]:.2f}" for p in pressures))

    curve = {p: {"mean": statistics.mean(v), "stdev": (statistics.stdev(v) if len(v) > 1 else 0.0)}
             for p, v in per_pressure.items()}
    var_at_max = statistics.stdev(per_seed_at_max) if len(per_seed_at_max) > 1 else 0.0
    result = {"model": args.model, "cell": args.cell, "pressures": pressures, "k": args.k,
              "seeds": args.seeds, "curve": curve, "escape_at_max_per_seed": per_seed_at_max,
              "stdev_at_max": var_at_max}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print("\n=== escape curve (mean across seeds) ===")
    for p in pressures:
        print(f"  P{p}: {curve[p]['mean']:.3f}  (±{curve[p]['stdev']:.3f})")
    print(f"stdev at max pressure across seeds: {var_at_max:.3f}  -> use to re-tune N")
    print(f"written: {args.out}")


if __name__ == "__main__":
    main()
