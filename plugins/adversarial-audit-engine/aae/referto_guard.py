"""referto_guard.py — the ledger is the ground truth; the prose may not overstate it.

A real failure (CTU R.G. 284/2025) was NOT in the core but in the NARRATOR: a finding the
core had marked `artefatto_regge` was presented in the client referto as a HIGH-posta exposure
"to presidiare", and a `conteso` (routed-to-expert) finding was written up as a settled defect.
The verdict and the stakes come from the deterministic core; a prose summary can only report
them, never promote them. A prompt asking the narrator to "be faithful" can be ignored — so this
is a deterministic check the narrator MUST pass before a referto ships: it compares a tiny
presentation manifest against the ledger and fails on any overstatement.

Manifest: a list of entries, one per finding the referto presents:
    {"id": "F05", "presented_as": "defect"|"open"|"holds", "presented_posta": "high"|"medium"|"low"}

Rules (violations are returned as human-readable strings; empty list == consistent):
  1. presented_posta may not exceed the finding's ledger posta (no stakes inflation).
  2. presented_as="defect" (a standing exposure the reader must act on) is allowed only when the
     ledger verdict is accusa_vince / accusa_ridimensionata / da_leggere. A finding the core says
     `artefatto_regge` (holds) or `conteso`/`pending` (routed to the expert, not settled) may NOT
     be presented as a defect.
  3. every manifest id must exist in the ledger (no invented findings).
  4. (1.18) a finding the core marks as resting only on the auditor's own defense (`defense_holds`) or as a
     hold that admits a missing document (UNSETTLED: artefatto_regge + requires_docs absent from
     evidence_base) may NOT be presented as "holds" (solid) — only as "open" (to verify). RN95 A/B pilot:
     the biggest risks (leases, roof) held on "the expert declares the limit" defenses.
  5. (1.18) those same findings may not be silently omitted: each must appear in the manifest.
  6. (1.19) a common cause (root) may be presented as a CONCLUSION only if the ledger labels it 'sostenuta' (blind judge:
     support + intruder, controls clean). Manifest entry: {"root_id": "R1", "presented_as": "conclusion"|"hypothesis"}.
"""
from __future__ import annotations

_POSTA_RANK = {"low": 0, "medium": 1, "high": 2}

# ledger verdict (enum value) -> the presentation framings it may carry
_ALLOWED_AS = {
    "accusa_vince": {"defect", "open", "holds"},
    "accusa_ridimensionata": {"defect", "open", "holds"},
    "da_leggere": {"defect", "open", "holds"},
    "conteso": {"open", "holds"},        # routed to expert — NOT a settled defect
    "pending": {"open", "holds"},
    "artefatto_regge": {"holds", "open"},  # it HOLDS — never a defect
}


def _ledger_index(ledger) -> dict:
    """Accept a Ledger object, a list of findings, or a list/dict of finding dicts."""
    findings = getattr(ledger, "findings", ledger)
    if isinstance(findings, dict):
        findings = findings.get("findings", [])
    out = {}
    for f in findings:
        if isinstance(f, dict):
            fid = f.get("id")
            verdict = f.get("verdict")
            posta = f.get("posta")
        else:  # Finding object
            fid = f.id
            verdict = f.verdict.value if hasattr(f.verdict, "value") else f.verdict
            posta = f.posta.value if hasattr(f.posta, "value") else f.posta
        if fid:
            out[fid] = (str(verdict), str(posta))
    return out


def _must_be_open(ledger) -> dict:
    """{id: reason} for findings that may only be presented as 'open' (1.18)."""
    if isinstance(ledger, dict):
        findings = ledger.get("findings", [])
        dh = ledger.get("defense_holds", []) or []
        base = ledger.get("evidence_base", []) or []
    else:
        findings = getattr(ledger, "findings", ledger) or []
        dh = getattr(ledger, "defense_holds", []) or []
        base = getattr(ledger, "evidence_base", []) or []
    base = {str(b).strip().lower() for b in base if str(b).strip()}
    dh = {str(x) for x in dh}
    out = {}
    for f in findings if isinstance(findings, list) else []:
        g = (lambda k: f.get(k)) if isinstance(f, dict) else (lambda k: getattr(f, k, None))
        fid = g("id")
        if not fid:
            continue
        verdict = g("verdict"); verdict = getattr(verdict, "value", verdict)
        state = g("action_state"); state = getattr(state, "value", state)
        if str(verdict) != "artefatto_regge" or str(state) == "deliberately_discarded":
            continue
        label = str(fid) if not str(fid).endswith("-?") else str(g("element") or fid)[:40]
        if label in dh or str(fid) in dh:
            out[fid] = "held ONLY by the auditor's own defense (DEFENSE LEVER)"
            continue
        missing = [d for d in (g("requires_docs") or []) if str(d).strip().lower() not in base]
        if missing:
            out[fid] = "held but UNSETTLED (missing: " + ", ".join(map(str, missing)) + ")"
    return out


def check_referto_consistency(ledger, manifest: list[dict]) -> list[str]:
    """Return a list of overstatement violations (empty == the referto matches the ledger)."""
    idx = _ledger_index(ledger)
    violations: list[str] = []
    must_open = _must_be_open(ledger)
    presented = {e.get("id") for e in (manifest or [])}
    for fid, why in must_open.items():
        if fid not in presented:
            violations.append(f"{fid}: {why} — omitted from the referto; it must be presented as 'open'")
    roots = {}
    _rs = ledger.get("root_support", []) if isinstance(ledger, dict) else getattr(ledger, "root_support", [])
    for r in _rs or []:
        roots[str(r.get("id"))] = r.get("label")
    for entry in manifest or []:
        if "root_id" in entry:
            rid = str(entry.get("root_id"))
            if rid not in roots:
                violations.append(f"root {rid}: presented but absent from the ledger's root_support")
            elif str(entry.get("presented_as", "hypothesis")).lower() == "conclusion" and roots[rid] != "sostenuta":
                violations.append(f"root {rid}: presented as a conclusion but labelled '{roots[rid]}' — "
                                  f"present it as a hypothesis of common cause")
            continue
        fid = entry.get("id")
        if fid not in idx:
            violations.append(f"{fid}: presented but absent from the ledger (invented finding)")
            continue
        verdict, posta = idx[fid]
        pres_posta = str(entry.get("presented_posta", posta)).lower()
        pres_as = str(entry.get("presented_as", "open")).lower()
        if _POSTA_RANK.get(pres_posta, 0) > _POSTA_RANK.get(posta, 0):
            violations.append(
                f"{fid}: presented at posta '{pres_posta}' but the ledger says '{posta}' "
                f"(stakes inflated)")
        allowed = _ALLOWED_AS.get(verdict, {"holds", "open"})
        if pres_as not in allowed:
            violations.append(
                f"{fid}: presented as '{pres_as}' but the ledger verdict is '{verdict}' "
                f"(allowed: {', '.join(sorted(allowed))}) — the narrator overstated the ledger")
        if fid in must_open and pres_as == "holds":
            violations.append(
                f"{fid}: presented as 'holds' (solid) but it is {must_open[fid]} — present it as 'open'")
    return violations
