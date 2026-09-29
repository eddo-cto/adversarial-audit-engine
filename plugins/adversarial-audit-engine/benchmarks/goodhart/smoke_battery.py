"""
smoke_battery.py — fidelity smoke: can the local model honour the real defense-first contract on general-v3?

Runs a few labelled items (some valid, some invalid) through the FAITHFUL auditor (RealRoleRunner, single role,
no eye) on the local model, and prints per item: gold, the model's raw answer, CLEARED, and whether it matches
the gold. If the model clears the valids and catches the invalids, fidelity is good and we run the full cells.
If it condemns valids (false positives) or clears invalids (escapes), we see it here before spending an hour.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _HERE)

import auditor_engine as AE     # noqa: E402
import engine_audit as EA       # noqa: E402
import harness as H             # noqa: E402
import ollama_client as OC      # noqa: E402

_BATTERY = os.path.join(_HERE, "..", "type1_calibration", "batteries", "general-v3.json")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--host", default=OC.DEFAULT_HOST)
    ap.add_argument("--n-valid", type=int, default=3)
    ap.add_argument("--n-invalid", type=int, default=3)
    ap.add_argument("--raw", action="store_true",
                    help="dump the model's raw answer + parsed result per item (separate judgment vs parse error)")
    args = ap.parse_args(argv)

    items = json.load(open(_BATTERY, encoding="utf-8"))["items"]
    valids = [i for i in items if i["label"] == "valid"][:args.n_valid]
    invalids = [i for i in items if i["label"] == "invalid"][:args.n_invalid]
    sample = valids + invalids

    chat = OC.make_chat(args.model, host=args.host)

    if args.raw:
        # diagnostic: separate JUDGMENT error (model computed wrong) from PARSE error (bad JSON -> defaulted)
        print("Per-item raw model answer vs parse (single verifier role):\n")
        for it in sample:
            ans = chat(EA.build_audit_prompt(it["artifact"], "verifier"))
            obj = EA.parse_audit(ans)
            diag = "PARSE-FAIL (no usable JSON)" if obj is None else f"parsed={obj}"
            print(f"--- {it['id']} gold={it['label']} | {it['artifact'][:70]}")
            print(f"    RAW: {ans.strip()[:300]}")
            print(f"    -> {diag}\n")
        return

    auditor = AE.EngineAuditor(role_runner=EA.RealRoleRunner(chat, internal_identity=f"ollama-local:{args.model}"))
    cell = H.AblationCell("defenses_off", eye=False, axes=False, governor=False)

    print(f"{'id':4} {'gold':8} {'cleared':8} {'ok?':4}  claim")
    ok = 0
    for it in sample:
        cleared = auditor.audit(it, cell)          # single real role, defense-first
        gold_valid = (it["label"] == "valid")
        correct = (cleared == gold_valid)          # valid should clear, invalid should be caught
        ok += correct
        print(f"{it['id']:4} {it['label']:8} {str(cleared):8} {'OK ' if correct else 'XX '}  {it['artifact'][:70]}")
    print(f"\nfidelity: {ok}/{len(sample)} items handled correctly by {args.model} under the real defense-first contract")


if __name__ == "__main__":
    main()
