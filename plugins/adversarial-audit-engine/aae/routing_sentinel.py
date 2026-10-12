"""Routing sentinel (1.16.0) — expose the self-declared levers that keep a finding out of condemnation.

The verdict is a pure function of fields the AUDITOR declares. Two of them route a finding away from a
condemnation without any content check:

  * `requires_docs` naming a document absent from `evidence_base`  -> NEEDS_EXPERT (evidence-sufficiency gate)
  * `source_grade > 1` while a primary is reachable                  -> NEEDS_READING (source-grade gate)

Both gates are right to exist. But an auditor that knows the map (or simply optimises for "never be caught
overstating") can use them as a free exit: attach a document the claim AS STATED does not need, or grade a
primary fact as secondary, and the run shows zero condemnations. Found on a real run (Rimini R.G.E. 95/2025):
removing those declarations turned 0 condemnations into 5, three of them decidable from the bundle alone.

This module does NOT judge whether a routing was warranted — that needs the content, i.e. a human. It
recomputes each finding's verdict WITHOUT those two levers (keeping every content gate: defense, competence,
grounding) and records the findings whose condemnation was avoided ONLY by a self-declared lever. Record-only:
no verdict is changed. Pure, stdlib-only, deterministic.
"""
from __future__ import annotations

import copy

from .schema import Verdict, DefectClass

_CONDEMN = (Verdict.ARTIFACT_DEFECTIVE, Verdict.REDUCED)


def _counterfactual(f, *, primary_reachable: bool, source_text: str):
    """Verdict of `f` with the routing levers removed but every content gate kept."""
    cf = copy.deepcopy(f)
    cf.requires_docs = []
    try:
        if primary_reachable and int(getattr(cf, "source_grade", 1) or 1) > 1:
            cf.source_grade = 1
    except (TypeError, ValueError):
        cf.source_grade = 1
    v = cf.adjudicate()
    if v not in _CONDEMN:
        return v
    # competence gate is a CONTENT gate (no cited norm) -> keep it
    declared = (cf.defect_class == DefectClass.NORMATIVE or bool(getattr(cf, "rests_on_authority", False)))
    if declared and not (getattr(cf, "authority_cited", None) or "").strip():
        return Verdict.NEEDS_EXPERT
    # grounding is a CONTENT gate (quote not verbatim) -> keep it
    if source_text:
        from .grounding import classify, _GROUNDED_BASES
        base = getattr(cf.accusation, "base", None)
        base_val = base.value if hasattr(base, "value") else base
        if base_val in _GROUNDED_BASES:
            quote = getattr(cf, "quote", None) or getattr(cf.accusation, "evidence", "") or ""
            if classify(quote, source_text) != "strict":
                return Verdict.NEEDS_READING
    return v


def routing_sentinel(ledger, *, primary_reachable: bool = True, source_text: str = "") -> list[str]:
    """Fill `ledger.routing_delta` and return flag notes. Never changes a verdict."""
    base = {str(d).strip().lower() for d in (getattr(ledger, "evidence_base", []) or []) if str(d).strip()}
    delta: list[dict] = []
    for f in ledger.findings:
        if f.verdict in _CONDEMN or f.verdict == Verdict.ARTIFACT_HOLDS:
            continue
        levers = []
        missing = [str(d).strip() for d in (getattr(f, "requires_docs", []) or [])
                   if str(d).strip() and str(d).strip().lower() not in base]
        if missing:
            levers.append("requires_docs=" + "+".join(missing))
        try:
            grade = int(getattr(f, "source_grade", 1) or 1)
        except (TypeError, ValueError):
            grade = 1
        if primary_reachable and grade > 1:
            levers.append(f"source_grade={grade}")
        if not levers:
            continue
        cf = _counterfactual(f, primary_reachable=primary_reachable, source_text=source_text)
        if cf in _CONDEMN:
            fid = str(f.id or "")
            label = fid if fid and not fid.endswith("-?") else (str(f.element or fid)[:40] or "?")
            delta.append({"id": fid, "label": label, "verdict": f.verdict.value,
                          "counterfactual": cf.value, "levers": levers})
    ledger.routing_delta = delta
    # 1.17 defense lever (record-only): HIGH-posta findings held ONLY by the auditor's own defense — without
    # `defense.present` they would condemn. Not a judgement: the list of defenses a human should read first.
    dh = []
    for f in ledger.findings:
        if f.verdict != Verdict.ARTIFACT_HOLDS or getattr(f.posta, "value", f.posta) != "high":
            continue
        if f.action_state.value == "deliberately_discarded":
            continue
        cf = copy.deepcopy(f)
        cf.defense.present = False
        cf.requires_docs = []
        v = _counterfactual(cf, primary_reachable=primary_reachable, source_text=source_text)
        if v in _CONDEMN:
            fid = str(f.id or "")
            dh.append(fid if fid and not fid.endswith("-?") else (str(f.element or fid)[:40] or "?"))
    ledger.defense_holds = dh
    notes = []
    if dh:
        notes.append(f"DEFENSE LEVER: {len(dh)} rilievo/i ad ALTA posta regge/reggono SOLO per la difesa scritta "
                     f"dall'auditor — {'; '.join(dh)}. Record-only: l'umano legga per prime queste difese "
                     f"(un limite dichiarato non è una confutazione).")
    if not delta:
        return notes
    items = "; ".join(f"{d['label']} ({', '.join(d['levers'])}: {d['verdict']} → senza: {d['counterfactual']})"
                      for d in delta)
    return notes + [f"ROUTING SENTINEL: {len(delta)} condanna/e evitata/e SOLO da instradamento auto-dichiarato — "
            f"{items}. Record-only: verificare che ciascun documento/grado sia necessario al rilievo COSÌ "
            f"COM'È FORMULATO (non solo a risolverlo)."]
