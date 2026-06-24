"""
legal_oracle.py — on-demand, fidelity-only legal reference oracle.

Extends the engine's "controllable" slice to EXTERNAL norms: given a citation in an
act, it verifies (a) the cited article exists in the official text and (b) what the
act CLAIMS about it is faithful to that text (verbatim grounding). It NEVER
interprets and NEVER quotes a norm from model memory.

Anti-hallucination, by construction:
  - the norm text comes ONLY from an injected `fetcher` (an official source such as
    Normattiva, wired on the user's machine). No fetcher / failed fetch -> status
    "unverified" (never an assertion).
  - fidelity is checked with the deterministic grounding gate (verbatim substring).
  - interpretation ("does it apply? is the qualification correct?") is OUT OF SCOPE
    -> routed to the human expert.

Stdlib only. The deterministic parts cannot themselves hallucinate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from .grounding import is_grounded, normalize

# law reference: L./legge/D.Lgs./D.P.R./DPR/D.L./R.D. n. NNN/AAAA   +  Codice Civile
_LAW = re.compile(
    r"(?P<law>(?:legge|l\.|d\.?\s?lgs\.?|d\.?\s?p\.?\s?r\.?|dpr|d\.?\s?l\.?|r\.?\s?d\.?)\s*"
    r"n?\.?\s*\d+\s*[/ ]\s*\d{2,4})", re.I)
_CC = re.compile(r"\b(?:art(?:icolo)?\.?\s*\d+(?:[- ]?(?:bis|ter|quater|quinquies))?)\s*"
                 r"(?:del\s+)?(?:c\.?\s?c\.?|codice\s+civile|cod\.?\s?civ\.?)", re.I)
_ART = re.compile(r"art(?:icolo)?\.?\s*(?P<num>\d+(?:[- ]?(?:bis|ter|quater|quinquies))?)", re.I)
_COMMA = re.compile(r"comm[ai]\s*(?P<nums>\d+(?:\s*,\s*\d+)*(?:\s*e\s*\d+)?)", re.I)


@dataclass
class Citation:
    raw: str
    article: Optional[str] = None
    commas: list[str] = field(default_factory=list)
    law: Optional[str] = None


@dataclass
class VerificationResult:
    citation: str
    status: str                 # "verified" | "unverified" | "no_source"
    exists: Optional[bool] = None     # the cited article is present in the source
    faithful: Optional[bool] = None   # the act's claim is verbatim-grounded in source
    source_ref: Optional[str] = None
    note: str = ""


def extract_citations(text: str) -> list[Citation]:
    """Deterministic best-effort extraction of legal references from an act."""
    out: list[Citation] = []
    seen = set()
    # Codice Civile references (art. N c.c.)
    for m in _CC.finditer(text):
        raw = re.sub(r"\s+", " ", m.group(0)).strip()
        if raw.lower() in seen:
            continue
        seen.add(raw.lower())
        am = _ART.search(raw)
        out.append(Citation(raw=raw, article=am.group("num") if am else None, law="c.c."))
    # law references, with nearby article/comma (look back up to ~80 chars)
    for m in _LAW.finditer(text):
        law = re.sub(r"\s+", " ", m.group("law")).strip()
        window = text[max(0, m.start() - 90):m.end()]
        am = _ART.search(window)
        cm = _COMMA.search(window)
        raw = re.sub(r"\s+", " ", window[window.lower().find("art") if "art" in window.lower() else 0:]).strip()
        key = (law.lower(), am.group("num").lower() if am else None)
        if key in seen:
            continue
        seen.add(key)
        commas = []
        if cm:
            commas = re.findall(r"\d+", cm.group("nums"))
        out.append(Citation(raw=raw[:120], article=am.group("num") if am else None,
                            commas=commas, law=law))
    return out


def _article_present(norm_text: str, article: Optional[str]) -> Optional[bool]:
    if not article:
        return None
    n = normalize(norm_text)
    a = re.sub(r"[- ]", "", article.lower())
    # accept "art. N", "articolo N", "art.N"
    pat = re.compile(r"art(?:icolo)?\.?\s*" + re.escape(article.lower().replace(" ", "")).replace("\\", ""))
    return bool(re.search(r"art(?:icolo)?\.?\s*" + re.escape(article.lower()), n)) or (("art " + a) in n.replace(".", " "))


class LegalOracle:
    """fetcher: Callable[[Citation], Optional[str]] returning the OFFICIAL norm text
    (version vigente at the act's date), or None if it cannot be retrieved.
    On the user's machine wire it to Normattiva; offline pass a stub."""

    def __init__(self, fetcher: Optional[Callable[[Citation], Optional[str]]] = None):
        self.fetcher = fetcher

    def verify(self, citation: Citation, claimed_text: str = "") -> VerificationResult:
        if self.fetcher is None:
            return VerificationResult(citation.raw, "no_source",
                                      note="nessun fetcher ufficiale collegato: nessuna asserzione dalla memoria")
        norm = None
        try:
            norm = self.fetcher(citation)
        except Exception as e:  # network/parse failure
            return VerificationResult(citation.raw, "unverified",
                                      note=f"recupero norma fallito: {e}; nessuna asserzione dalla memoria")
        if not norm:
            return VerificationResult(citation.raw, "unverified",
                                      note="norma non recuperata dalla fonte ufficiale; nessuna asserzione")
        exists = _article_present(norm, citation.article)
        faithful = is_grounded(claimed_text, norm) if claimed_text else None
        note = "verifica di sola FEDELTA'/esistenza; l'interpretazione resta all'esperto"
        return VerificationResult(citation.raw, "verified", exists=exists,
                                  faithful=faithful, source_ref="fonte ufficiale", note=note)
