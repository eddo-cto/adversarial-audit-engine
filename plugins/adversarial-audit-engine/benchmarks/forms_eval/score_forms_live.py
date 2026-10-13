#!/usr/bin/env python3
"""score_forms_live.py — scoring of the LIVE forms test (FORMS_RN95_*): canary recall/presentation + lever indicators.

Arms: F0_1..3 (engine 1.18, standard spec) and F1_1..3 (spec adds the F1 absolution rule: a hold needs a quoted rebuttal).
Offline-derived forms on the F0 runs: F2 (F1 rule only on HIGH posta) and F3 (aggregation over the 3 F0 runs, m=1).
Canaries are detected by fixed regexes (below, pre-registered); their gold is in the SEALED key, read only with --key.

Usage: python score_forms_live.py <FORMS_RN95_dir> [--key CANARY_KEY.json]
"""
import argparse, glob, json, os, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import forms_replay as FR  # noqa: E402

CANARY_RX = {   # pre-registered detectors on element + accusation text (+ evidence)
    "C1": [r"395[.]?344"],
    "C2": [r"\b70 ?%"],
    "C3": [r"12/03/2019", r"registrat\w* .{0,60}anterior", r"opponibil\w* .{0,80}(registrat|2019)"],
    "C4": [r"fibrocemento", r"amianto"],
}


def canary_status(led, pres):
    st = {}
    for c, pats in CANARY_RX.items():
        hit = []
        for f in led.findings:
            if f.id not in pres:
                continue
            text = FR._norm(" ".join([f.element or "", f.accusation.text or "", f.accusation.evidence or ""]))
            if any(re.search(p, text, re.I) for p in pats):
                hit.append(pres[f.id])
        st[c] = "absent" if not hit else ("defect" if "defect" in hit else ("open" if "open" in hit else "solid"))
    return st


def levers(led):
    live = [f for f in led.findings if f.action_state.value != "deliberately_discarded"]
    n = max(len(live), 1)
    return {"n": len(live),
            "high_share": round(sum(f.posta.value == "high" for f in live) / n, 2),
            "trivial_share": round(sum(f.cost_to_fix.value == "trivial" for f in live) / n, 2),
            "requires_docs": sum(1 for f in live if f.requires_docs),
            "routing_delta": len(led.routing_delta or []),
            "defense_holds": len(led.defense_holds or []),
            "held": sum(f.verdict.value == "artefatto_regge" for f in live),
            "condemn": sum(f.verdict.value in ("accusa_vince", "accusa_ridimensionata") for f in live),
            "state": led.completion_state}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--key")
    a = ap.parse_args(argv)
    gold = None
    if a.key:
        k = json.load(open(a.key, encoding="utf-8"))
        gold = {c: ("defect" if v["gold"].startswith("defect") else "non-solid") for c, v in k.items() if c.startswith("C")}
    rows = {}
    for arm_dir in sorted(glob.glob(os.path.join(a.root, "F*_*"))):
        fj = os.path.join(arm_dir, "findings.json")
        if not os.path.exists(fj):
            continue
        d = json.load(open(fj, encoding="utf-8")); src = d.get("source_text", "")
        os.environ.pop("AAE_EXTERNAL_ATTESTED_IDENTITY", None)
        led = FR.discipline(d).ledger
        arm = os.path.basename(arm_dir)
        forms = ["F0"] if arm.startswith("F1") else ["F0", "F2"]  # F1 arms are already 'F1 behaviour'
        for form in forms:
            pres = FR.present(led, src, form)
            label = arm if form == "F0" else arm.replace("F0", "F2")
            rows[label] = {"canary": canary_status(led, pres), "load": sum(v != "solid" for v in pres.values()),
                           **levers(led)}
    # F3: aggregate the F0 arms (non-solid if non-solid in >= 1 run)
    f0 = [r for k, r in rows.items() if k.startswith("F0_")]
    if f0:
        agg = {}
        for c in CANARY_RX:
            vals = [r["canary"][c] for r in f0]
            agg[c] = "defect" if "defect" in vals else ("open" if "open" in vals else ("solid" if "solid" in vals else "absent"))
        rows["F3_agg(F0x%d)" % len(f0)] = {"canary": agg, "load": sum(r["load"] for r in f0)}
    for k, r in rows.items():
        line = f"{k:16s} canary={r['canary']} load={r['load']}"
        if gold:
            det = sum(r["canary"][c] != "absent" for c in gold) / len(gold)
            ok = sum((r["canary"][c] in ("defect", "open")) if g == "non-solid" else (r["canary"][c] == "defect")
                     for c, g in gold.items()) / len(gold)
            line += f" | detect={det:.2f} correct_presentation={ok:.2f}"
        extra = {x: r[x] for x in ("high_share", "trivial_share", "requires_docs", "routing_delta", "defense_holds",
                                   "held", "condemn", "state") if x in r}
        print(line, extra)
    json.dump(rows, open(os.path.join(a.root, "score_forms.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
