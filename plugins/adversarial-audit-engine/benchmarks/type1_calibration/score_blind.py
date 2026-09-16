"""score_blind.py — un-blind an auditor's blind result with the private key and calibrate in one step.

Fills the gap between make_blind (neutral ids) and calibrate (needs labelled outcomes): the blind
auditor writes blind_result_<id>.json with neutral ids and condemned flags; this maps them back via
the private key, builds the labelled outcomes, computes the record and appends it to the store.

Usage:
    python3 score_blind.py <auditor_identity> <blind_result.json> <_key_<id>.json> [store] [battery_id]
Example:
    python3 score_blind.py anthropic:claude-sonnet-5 blind_result_general-v3.json _key_general-v3.json \\
            _calibration.jsonl general-v3
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))  # plugin root, for `aae`
from aae import type1_calibration as t1  # noqa: E402


def load_outcomes(result_path: str, key_path: str) -> list:
    result = json.load(open(result_path, encoding="utf-8"))
    key = json.load(open(key_path, encoding="utf-8"))
    cond = {r["id"]: (1 if r.get("condemned") else 0) for r in result}
    missing = [nid for nid in key if nid not in cond]
    if missing:
        raise SystemExit(f"blind result is missing {len(missing)} ids (e.g. {missing[:5]}): "
                         "the auditor must judge every item.")
    return [{"id": meta["orig_id"], "label": meta["label"], "condemned": cond[nid]}
            for nid, meta in key.items()]


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 3:
        print(__doc__)
        return 2
    identity, result_path, key_path = argv[0], argv[1], argv[2]
    store = argv[3] if len(argv) > 3 else os.path.join(HERE, "_calibration.jsonl")
    battery_id = argv[4] if len(argv) > 4 else "general-v3"
    outcomes = load_outcomes(result_path, key_path)
    rec = t1.make_record(identity, battery_id, outcomes)
    t1.append_calibration(rec, store)
    print(t1.cite(rec))
    print(f"\nwritten to: {store}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
