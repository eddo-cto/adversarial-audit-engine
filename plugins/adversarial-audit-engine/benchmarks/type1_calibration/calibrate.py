#!/usr/bin/env python3
"""calibrate.py — turn a battery-scoring result into a calibration record.

The auditor (the same LLM/agent that runs /audit) audits every item in battery.json and records, per
item, whether it DEMOLISHED it (condemned = asserted a real defect). That produces an outcomes file:

    [{"id": "V1", "label": "valid", "condemned": 0}, {"id": "I1", "label": "invalid", "condemned": 1}, ...]

This script turns that into a calibration record (FDR / Type-I with a 95% Wilson interval, TDR, AUC) and
appends it to the calibration store the run cites via AAE_CALIBRATION.

Usage:
    calibrate.py <auditor_identity> <outcomes.json> [store.jsonl] [battery_id]

Honesty: the Type-I estimate is only as certain as the battery is large. The record always carries the
confidence interval; with 6 valid controls it is wide. Grow the battery for a tighter bound.
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from aae import type1_calibration as t1  # noqa: E402


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(__doc__)
        return 2
    identity, outcomes_path = argv[0], argv[1]
    store = argv[2] if len(argv) > 2 else os.path.join(os.path.dirname(__file__), "_calibration.jsonl")
    battery_id = argv[3] if len(argv) > 3 else "general-v1"
    with open(outcomes_path, encoding="utf-8") as fh:
        outcomes = json.load(fh)
    rec = t1.make_record(identity, battery_id, outcomes)
    t1.append_calibration(rec, store)
    print(t1.cite(rec))
    print(f"\nwritten to: {store}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
