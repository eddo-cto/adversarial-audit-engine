"""
evidence_pairing.py — claim<->evidence retrieval (defeat cue-locality).

Estesia transduction §15-B (the strongest empirical finding of run 2): an auditor's
detection collapses when the disconfirming fact is FAR from the claim. So the engine must
RETRIEVE the candidate relevant/disconfirming passages for each claim and present them
CO-LOCATED, letting the model judge LOCALLY (where it is strong) instead of scanning a long
document. This module does that retrieval deterministically (stdlib): lexical overlap +
key-term match, with a small bonus for passages carrying contradiction/negation markers
(the ones most likely to defeat the claim).

Deterministic, stdlib only. (An embedding-based retriever is the external/optional upgrade.)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_WORD = re.compile(r"[a-zà-ù0-9]+", re.I)
_STOP = {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da", "in",
         "con", "su", "per", "tra", "fra", "e", "o", "che", "del", "della", "dei", "delle",
         "al", "alla", "ai", "agli", "è", "the", "of", "and", "to", "is", "are"}
_CONTRA = (" non ", " né ", " senza ", " salvo ", " tranne ", " smentit", " contest",
           " priv", " difform", " assenza ", " manca", " escluso", " illegittim",
           " nullo ", " decade ", " viceversa ", " invece ", " tuttavia ", " però ")


def _toks(s: str) -> set:
    # prefix-5 stemming: matches inflectional variants (titoli/titolo, edilizi/edilizio,
    # difforme/difformità) that exact-token overlap would miss. Light, language-agnostic.
    return {w.lower()[:5] for w in _WORD.findall(s) if w.lower() not in _STOP and len(w) > 2}


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;:\n])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 0]


@dataclass
class Passage:
    text: str
    score: float
    contradiction_hint: bool


def pair_claim_with_evidence(claim: str, source: str, k: int = 3) -> list[Passage]:
    """Return up to k source passages most relevant to `claim`, contradiction-bearing
    passages boosted (they are the likeliest to defeat the claim). Co-locating these with
    the claim is what lets a downstream auditor judge locally."""
    cset = _toks(claim)
    if not cset:
        return []
    out: list[Passage] = []
    for sent in _sentences(source):
        sset = _toks(sent)
        if not sset:
            continue
        overlap = len(cset & sset)
        if overlap == 0:
            continue
        # Jaccard-ish relevance, normalized to claim size
        rel = overlap / (len(cset) ** 0.5)
        contra = any(m in (" " + sent.lower() + " ") for m in _CONTRA)
        score = rel * (1.6 if contra else 1.0)
        out.append(Passage(sent, round(score, 3), contra))
    out.sort(key=lambda p: p.score, reverse=True)
    return out[:k]


def build_local_prompt_context(claim: str, source: str, k: int = 3) -> str:
    """Render the claim with its co-located evidence — the payload to hand the auditor,
    so the cue is LOCAL. Empty evidence is itself a signal (no support found)."""
    ps = pair_claim_with_evidence(claim, source, k)
    if not ps:
        return (f"AFFERMAZIONE: «{claim}»\nEVIDENZA CO-LOCATA: (nessun passaggio rilevante "
                "trovato nella fonte — assenza di riscontro è essa stessa un segnale).")
    lines = [f"AFFERMAZIONE: «{claim}»", "EVIDENZA CO-LOCATA (passaggi più rilevanti della fonte):"]
    for i, p in enumerate(ps, 1):
        tag = " [possibile smentita]" if p.contradiction_hint else ""
        lines.append(f"  {i}.{tag} «{p.text}»")
    return "\n".join(lines)
