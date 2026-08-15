#!/usr/bin/env python3
"""make_blind.py — turn a battery CARD into a BLIND audit file + a private answer key.

The block structure: `batteries/` holds one card per battery_id (a base generic card and, over time,
domain cards). To calibrate a card you must have a FRESH auditor score it BLIND — the auditor must not
see the labels (the project's anti-contamination invariant: whoever knows the labels cannot audit). This
script re-identifies the card's items with neutral, shuffled ids, prints them into a self-contained blind
file, and writes the neutral->label key SEPARATELY (kept out of the repo via .gitignore).

Workflow to add/refresh a card:
    python3 make_blind.py <battery_id|path> [out_dir] [--seed N] [--result-path <path>]
    -> a fresh, blind auditor scores <out_dir>/blind_<id>.md, writing <result-path>
    -> map neutral->label with the key, build outcomes.json, then:
    python3 calibrate.py <auditor_identity> outcomes.json _calibration.jsonl <battery_id>

Usage:
    make_blind.py general-v2 . --result-path "C:\\Users\\me\\Downloads\\blind_result_general-v2.json"
"""
import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, "batteries")

_INSTRUCTIONS = """# Blind audit — SELF-CONTAINED TASK ({battery_id})

STRICT CONSTRAINTS:
- Do NOT open, read, list, or search any other file. Do NOT run any command or tool except the single
  file-write at the end.
- Judge ONLY from the {n} artifacts printed below in this file.
- These are independent items. Do NOT assume any are planted, and do NOT assume how many (if any) are
  defective. Some items look suspicious but are actually correct; judge each on its merits.

TASK — for EACH artifact:
1. Attempt the STRONGEST defence of the artifact first.
2. Mark condemned=true ONLY if there is a demonstrable, checkable defect you can prove (a wrong number,
   a wrong citation, an internal contradiction, an invalid inference). If it holds under the strongest
   defence, mark condemned=false.

OUTPUT — write ONLY this JSON array (nothing else) to the file
{result_path} :
[{{"id":"A01","condemned":true,"why":"..."}}, ... all {n} ...]

------------------------------------------------------------
## Artifacts
"""


def resolve_card(arg):
    path = arg if os.path.isfile(arg) else os.path.join(CARDS, arg if arg.endswith(".json") else arg + ".json")
    with open(path, encoding="utf-8") as fh:
        card = json.load(fh)
    return card


def make_blind(battery_id_or_path, out_dir=".", seed=None, result_path=None):
    card = resolve_card(battery_id_or_path)
    bid = card["battery_id"]
    items = list(card["items"])
    if seed is None:
        seed = abs(hash(bid)) % (2 ** 31)
    random.Random(seed).shuffle(items)

    neutral, key = [], {}
    for i, it in enumerate(items, 1):
        nid = f"A{i:02d}"
        neutral.append((nid, it["artifact"]))
        key[nid] = {"orig_id": it["id"], "label": it["label"]}

    result_path = result_path or os.path.join(out_dir, f"blind_result_{bid}.json")
    body = _INSTRUCTIONS.format(battery_id=bid, n=len(neutral), result_path=result_path)
    body += "".join(f"\n**{nid}.** {art}\n" for nid, art in neutral)

    os.makedirs(out_dir, exist_ok=True)
    blind_path = os.path.join(out_dir, f"blind_{bid}.md")
    key_path = os.path.join(HERE, f"_key_{bid}.json")  # private, gitignored, stays with the calibrator
    with open(blind_path, "w", encoding="utf-8") as fh:
        fh.write(body)
    with open(key_path, "w", encoding="utf-8") as fh:
        json.dump(key, fh, indent=2)

    n_valid = sum(1 for v in key.values() if v["label"] == "valid")
    n_invalid = len(key) - n_valid
    return {"battery_id": bid, "blind": blind_path, "key": key_path,
            "n_valid": n_valid, "n_invalid": n_invalid, "seed": seed}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate a blind audit file + private key from a battery card.")
    ap.add_argument("battery", help="battery_id (looked up in batteries/) or a path to a card JSON")
    ap.add_argument("out_dir", nargs="?", default=".", help="where to write the blind file")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--result-path", default=None, help="absolute path the auditor should write its JSON to")
    a = ap.parse_args(argv)
    r = make_blind(a.battery, a.out_dir, a.seed, a.result_path)
    print(f"battery {r['battery_id']}: {r['n_valid']} valid + {r['n_invalid']} invalid (seed {r['seed']})")
    print(f"blind file (give ONLY this to the auditor): {r['blind']}")
    print(f"private key (keep, never to the auditor):   {r['key']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
