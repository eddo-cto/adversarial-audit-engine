"""
normattiva_fetcher.py — official-source fetchers for the legal oracle.

The legal oracle is anti-hallucination *by construction*: it only ever asserts
something about a norm if a fetcher returns the official text; on any failure it
abstains. This module provides two fetchers with that contract:

  - LocalCorpusFetcher: reads norm text from a directory YOU control. This is the
    most trustworthy and fully deterministic source — no network, no scraping, no
    surprise. Recommended default.
  - NormattivaFetcher: best-effort live retrieval from Normattiva via the official
    URN permalink, date-aware (tempus regit actum). Normattiva is session/cookie
    protected and may block automated access; on ANY failure it returns None and
    the oracle abstains. Validate it on your own machine.

Both return Optional[str]; returning None is the safe, honest outcome.

Stdlib only.
"""
from __future__ import annotations

import os
import re
import urllib.request
from datetime import date
from typing import Optional

from .legal_oracle import Citation

# --- map our citation "law" labels to NIR URN types --------------------------
_NIR_TYPE = {
    "legge": "legge",
    "l.": "legge",
    "d.lgs": "decreto.legislativo",
    "dlgs": "decreto.legislativo",
    "d.p.r": "decreto.del.presidente.della.repubblica",
    "dpr": "decreto.del.presidente.della.repubblica",
    "d.l": "decreto.legge",
    "dl": "decreto.legge",
    "r.d": "regio.decreto",
    "rd": "regio.decreto",
}
# the codici are specific historical acts:
_CODICE_URN = {
    "c.c.": "regio.decreto:1942-03-16;262",        # Codice Civile
    "c.p.": "regio.decreto:1930-10-19;1398",       # Codice Penale
}


def _law_key(law: Optional[str]) -> Optional[str]:
    if not law:
        return None
    k = re.sub(r"\s+", "", law.lower())
    k = k.replace("decretolegislativo", "d.lgs").replace("decretolegge", "d.l")
    for cand in ("d.lgs", "dlgs", "d.p.r", "dpr", "d.l", "dl", "r.d", "rd", "legge", "l."):
        if k.startswith(cand):
            return cand
    return None


def _num_year(law: Optional[str]) -> Optional[tuple[str, str]]:
    if not law:
        return None
    m = re.search(r"(\d+)\s*[/ ]\s*(\d{2,4})", law)
    if not m:
        return None
    num, yr = m.group(1), m.group(2)
    if len(yr) == 2:                      # 98 -> 1998 / 22 -> 2022 (heuristic)
        yr = ("19" + yr) if int(yr) > 30 else ("20" + yr)
    return num, yr


def build_urn(citation: Citation) -> Optional[str]:
    """Construct the NIR URN for a citation, or None if it can't be built.
    Article is appended as a fragment (~artN); commas are not part of the URN."""
    law = (citation.law or "").lower()
    base = None
    if law in _CODICE_URN or law.replace(" ", "") in _CODICE_URN:
        base = "urn:nir:stato:" + _CODICE_URN[law if law in _CODICE_URN else law.replace(" ", "")]
    else:
        key = _law_key(citation.law)
        ny = _num_year(citation.law)
        if not key or not ny:
            return None
        base = f"urn:nir:stato:{_NIR_TYPE[key]}:{ny[1]};{ny[0]}"
    if citation.article:
        art = re.sub(r"[ .]", "", citation.article.lower())
        base += f"~art{art}"
    return base


class LocalCorpusFetcher:
    """Reads norm text from a local directory you control.

    Layout (flexible): one .txt per norm, named by URN-ish or free key. The
    fetcher matches by law-number-year (and ignores the article fragment, since
    the article presence/fidelity is checked downstream against the full text).
    Returns None if no file matches → oracle abstains.
    """

    def __init__(self, directory: str):
        self.directory = directory
        self._index: dict[str, str] = {}
        self._build_index()

    def _build_index(self) -> None:
        if not os.path.isdir(self.directory):
            return
        for fn in os.listdir(self.directory):
            if not fn.lower().endswith((".txt", ".md")):
                continue
            key = re.sub(r"[^0-9a-z]+", "", os.path.splitext(fn)[0].lower())
            self._index[key] = os.path.join(self.directory, fn)

    def __call__(self, citation: Citation) -> Optional[str]:
        ny = _num_year(citation.law)
        cands = []
        if ny:
            cands += [f"{ny[0]}{ny[1]}", f"{ny[1]}{ny[0]}"]
        law = re.sub(r"[^0-9a-z]+", "", (citation.law or "").lower())
        if law:
            cands.append(law)
        for key, path in self._index.items():
            if any(c and c in key for c in cands):
                try:
                    with open(path, encoding="utf-8", errors="ignore") as fh:
                        return fh.read()
                except OSError:
                    return None
        return None


class NormattivaFetcher:
    """Best-effort live fetch from Normattiva via the official URN permalink,
    date-aware. On ANY failure returns None (oracle abstains).

    Validate on your machine: Normattiva is session/cookie protected and the HTML
    structure changes; treat a None as 'could not verify', never as 'false'.
    """

    PERMALINK = "https://www.normattiva.it/uri-res/N2Ls?{urn}"

    def __init__(self, vigente_al: Optional[date] = None, timeout: float = 15.0,
                 user_agent: str = "Mozilla/5.0 (legal-oracle research)"):
        self.vigente_al = vigente_al           # tempus regit actum: norm version at this date
        self.timeout = timeout
        self.user_agent = user_agent

    def __call__(self, citation: Citation) -> Optional[str]:
        urn = build_urn(citation)
        if not urn:
            return None
        if self.vigente_al:
            urn += f"!vig={self.vigente_al.isoformat()}"
        url = self.PERMALINK.format(urn=urn)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return None                         # abstain on any network/parse error
        text = self._extract_text(html)
        return text or None

    @staticmethod
    def _extract_text(html: str) -> str:
        # strip scripts/styles, then tags; conservative — if it yields too little,
        # the caller treats it as 'not retrieved' (None) rather than asserting.
        html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
        html = re.sub(r"(?is)<br\s*/?>", "\n", html)
        text = re.sub(r"(?s)<[^>]+>", " ", html)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()
