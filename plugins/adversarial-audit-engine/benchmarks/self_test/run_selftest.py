"""
run_selftest.py — orchestrator of the G self-test release gate (1.12).

Flow: generate the sealed corpus -> run the ENGINE on each case to get findings -> deterministic match ->
aggregate G -> compare to the frozen baseline -> fail (non-zero exit) on regression.

The `auditor` is INJECTED: `auditor(case) -> list[findings]`. In CI/release it is the real engine run
(frontier model through pipeline.discipline); in tests it is a deterministic stub. So this orchestrator is
unit-testable without any LLM, and the live run just supplies the real auditor. The baseline is written on
first run and then frozen (committed like a calibration record); it is never auto-overwritten unless asked.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Callable

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import corpus_gen as C       # noqa: E402
import match as M            # noqa: E402
import metrics_g as G        # noqa: E402
import release_gate as RG    # noqa: E402

_BASELINE = os.path.join(_HERE, "baseline_g.json")


def measure_g(auditor: Callable[[dict], list], n: int = 40, seed: int = 20260711) -> dict:
    """Run the injected auditor over the generated corpus and return the aggregated G."""
    cases = C.generate(n=n, seed=seed)
    results, flags = [], []
    for c in cases:
        findings = auditor(c) or []
        results.append(M.match_case(findings, c["defects"], c["source_text"]))
        flags.append(c["label"] == "clean")
    g = G.aggregate(results, no_defect_flags=flags)
    g["corpus"] = C.manifest(cases)
    return g


def gate_against_baseline(g: dict, baseline_path: str = _BASELINE) -> dict:
    if not os.path.exists(baseline_path):
        return {"passed": True, "reasons": ["no baseline yet — this run would establish it"], "baseline": None}
    base = json.load(open(baseline_path, encoding="utf-8"))
    return RG.evaluate(base, g)


def main(argv=None, auditor: Callable[[dict], list] | None = None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260711)
    ap.add_argument("--baseline", default=_BASELINE)
    ap.add_argument("--update-baseline", action="store_true", help="write the measured G as the new frozen baseline")
    args = ap.parse_args(argv)
    if auditor is None:
        raise SystemExit("run_selftest: supply the real engine auditor (frontier). No default LLM here.")

    g = measure_g(auditor, n=args.n, seed=args.seed)
    print(f"G: severity-recall={g['recall_severity']:.3f}  precision={g.get('precision'):.3f}  "
          f"fp_rate={g['fp_rate']:.3f}  (n={g['n_cases']})")
    if args.update_baseline:
        json.dump(g, open(args.baseline, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"baseline written: {args.baseline}")
        return 0
    verdict = gate_against_baseline(g, args.baseline)
    if verdict["passed"]:
        print("GATE: PASS", "(" + "; ".join(verdict["reasons"]) + ")" if verdict.get("reasons") else "")
        return 0
    print("GATE: FAIL —", "; ".join(verdict["reasons"]))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
