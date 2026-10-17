"""Root support (1.19.0) — is a declared COMMON CAUSE sustained by the cited evidence, or only by the auditor's narrative?

Born from the «imbuto → Y» programme (teoria_Y, phases 1–3): a common cause is the TRUNK of a merge tree of findings,
the part an author can fabricate. On 4 real runs (12 roots) a lexical coherence test found nothing (causes are
abstractions), while a BLIND SEMANTIC JUDGE separated real roots from same-run random groups: support 1.08 vs 0.50,
intruder recognised 7/12 vs chance 0.24, label 'sostenuta' 6/12 vs 0/12 (attribution + intrusion, cf. AIS/ALCE and
word-intrusion in the literature).

Protocol (deterministic; the judge is EXTERNAL, the core only builds the probe and scores):
  1. The payload declares roots WITH members: `deep_causal_roots: [{id, statement, finding_ids}]`.
  2. `build_probe(payload)` builds a blind packet: per root, (a) the root's members' quotes + one INTRUDER quote from a
     non-member, shuffled; (b) a CONTROL item: the same statement over a same-size random group of non-members + an
     intruder. Items are shuffled and relabelled. Everything is seeded from the artefact identity and root ids, so the
     core recomputes the hidden key itself — the key is never in the payload.
  3. An independent judge (eye / separate session) answers per item {support: pieno|parziale|assente, intruder}; the
     flow puts the raw answers in `root_judgments`.
  4. The core scores: root 'sostenuta' iff support in {pieno, parziale} AND intruder recognised; else 'ipotesi'.
     'non_verificabile' if members are missing/unknown; 'non_verificato' if no judgment. If ANY control item scores
     'sostenuta', the judge is LENIENT for this run: every root is downgraded to 'ipotesi' and flagged.
Record-only: verdicts never change. The referto guard (1.19) forbids presenting a non-'sostenuta' root as a conclusion.
"""
from __future__ import annotations

import hashlib
import random

_SUPPORTED = {"pieno", "parziale"}


def _roots(payload) -> list:
    return [r for r in (payload.get("deep_causal_roots") or []) if isinstance(r, dict)]


def _quotes(payload) -> dict:
    out = {}
    for f in payload.get("findings", []) or []:
        fid = str(f.get("id") or "").strip()
        if fid:
            out[fid] = ((f.get("accusation") or {}).get("evidence") or "").strip()[:400]
    return out


def _seed(payload) -> int:
    ident = str(payload.get("artifact_id") or payload.get("artifact_name") or "")
    ids = "|".join(f"{r.get('id')}:{','.join(map(str, r.get('finding_ids') or []))}" for r in _roots(payload))
    return int(hashlib.sha256((ident + "#" + ids).encode("utf-8")).hexdigest()[:12], 16)


def _plan(payload):
    """Deterministic probe + hidden key. Returns (items, key, unverifiable_root_ids)."""
    q = _quotes(payload)
    all_ids = sorted(q)
    rng = random.Random(_seed(payload))
    items, bad = [], []
    for r in _roots(payload):
        rid = str(r.get("id") or "")
        mem = [str(x) for x in (r.get("finding_ids") or [])]
        if len(mem) < 2 or any(m not in q for m in mem):
            bad.append(rid)
            continue
        out = [i for i in all_ids if i not in mem]
        if len(out) < len(mem) + 2:
            bad.append(rid)
            continue
        stmt = str(r.get("statement") or "")
        intr = rng.choice(out)
        items.append({"root": rid, "kind": "root", "members": mem, "intruder": intr, "statement": stmt})
        pool = [i for i in out if i != intr]
        ctrl = rng.sample(pool, len(mem))
        c_intr = rng.choice([i for i in all_ids if i not in ctrl])
        items.append({"root": rid, "kind": "control", "members": ctrl, "intruder": c_intr, "statement": stmt})
    rng.shuffle(items)
    packet, key = [], {}
    for n, it in enumerate(items, 1):
        qid = f"P{n:02d}"
        ids = it["members"] + [it["intruder"]]
        rng.shuffle(ids)
        letters = {fid: chr(65 + j) for j, fid in enumerate(ids)}
        packet.append({"id": qid, "causa_comune_dichiarata": it["statement"],
                       "citazioni": [f"[{letters[fid]}] {q[fid]}" for fid in ids]})
        key[qid] = {"root": it["root"], "kind": it["kind"], "intruder": letters[it["intruder"]]}
    return packet, key, bad


def build_probe(payload) -> list:
    """The BLIND packet to hand to the independent judge (no key, no root/control labels)."""
    return _plan(payload)[0]


def score_roots(payload) -> tuple[list, dict, list]:
    """Returns (root_support records, summary, flag notes). Pure; never touches verdicts."""
    roots = _roots(payload)
    if not roots:
        return [], {}, []
    packet, key, bad = _plan(payload)
    answers = {str(a.get("id")): a for a in (payload.get("root_judgments") or []) if isinstance(a, dict)}
    recs, notes = {}, []
    for r in roots:
        rid = str(r.get("id") or "")
        recs[rid] = {"id": rid, "statement": str(r.get("statement") or ""),
                     "finding_ids": [str(x) for x in (r.get("finding_ids") or [])],
                     "label": "non_verificabile" if rid in bad else "non_verificato",
                     "support": None, "intruder_ok": None}
    lenient = 0
    controls = 0
    for qid, k in key.items():
        a = answers.get(qid)
        if a is None:
            continue
        sup = str(a.get("supporto") or a.get("support") or "").strip().lower()
        intr = str(a.get("intruso") or a.get("intruder") or "").strip().upper()
        ok = intr == k["intruder"]
        sustained = sup in _SUPPORTED and ok
        if k["kind"] == "control":
            controls += 1
            lenient += int(sustained)
        else:
            rec = recs[k["root"]]
            rec.update(support=sup or None, intruder_ok=ok, label="sostenuta" if sustained else "ipotesi")
    if lenient:
        for rec in recs.values():
            if rec["label"] == "sostenuta":
                rec["label"] = "ipotesi"
                rec["downgraded"] = "giudice indulgente"
        notes.append(f"ROOT SUPPORT: judge LENIENT — {lenient}/{controls} control group(s) scored as sustained; every "
                     f"root downgraded to 'ipotesi' for this run (record-only).")
    out = list(recs.values())
    summary = {"n": len(out), "sostenuta": sum(r["label"] == "sostenuta" for r in out),
               "ipotesi": sum(r["label"] == "ipotesi" for r in out),
               "non_verificabile": sum(r["label"] == "non_verificabile" for r in out),
               "non_verificato": sum(r["label"] == "non_verificato" for r in out),
               "controls_scored": controls, "controls_sustained": lenient}
    if summary["non_verificabile"]:
        notes.append(f"ROOT SUPPORT: {summary['non_verificabile']} root(s) without verifiable members "
                     f"(finding_ids missing/unknown) — not checkable, present as hypothesis.")
    if summary["non_verificato"]:
        notes.append(f"ROOT SUPPORT: {summary['non_verificato']} root(s) not yet judged — present as hypothesis "
                     f"(build the probe with run_core.py --root-probe and pass the judge's answers as root_judgments).")
    if summary["sostenuta"]:
        notes.append(f"ROOT SUPPORT: {summary['sostenuta']}/{summary['n']} root(s) sustained by a blind judge "
                     f"(support + intruder, controls clean).")
    return out, summary, notes
