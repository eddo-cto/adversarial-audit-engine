"""
grounding.py — deterministic anti-hallucination gate (Round-3 hardened).

Guarantee (deterministic, strong): a condemning finding's quote must EXIST
verbatim in the source. No fabrication can condemn.

NOT a guarantee (fundamentally semantic): faithful MEANING. A real substring can
be quote-mined out of a negated/exception context. We cannot solve this with a
string matcher, so the honest design is: a CONSERVATIVE, sentence-scope context
check that, when in doubt, BLOCKS condemnation and routes to the human. It
over-flags (some legitimate findings go to NEEDS_READING) — the safe direction,
consistent with "only the human validates meaning."

Round-3 fixes vs the naive version:
  - zero-width / format chars stripped (were silent recall killers);
  - negation/exception check moved from a 16-char window to the WHOLE containing
    SENTENCE, with an expanded marker set, catching negation-gap / trailing
    negation / exception markers that evaded the window.

Stdlib only.
"""
from __future__ import annotations

import re
import unicodedata

_GROUNDED_BASES = {"reading", "execution", "domain_knowledge"}
_MIN_QUOTE_CHARS = 12

_NEG_MARKERS = (
    " non ", " non e' ", " non è ", " ne' ", " né ", " senza ", " salvo ",
    " fatto salvo ", " ad esclusione ", " tranne ", " escluso ", " esclusa ",
    " esclusi ", " escluse ", " divieto ", " vietat", " in nessun caso ",
    " in alcun caso ", " a meno che ", " fatta eccezione ", " purche ",
    " preclus", " inammissibil", " illegittim", " nullo ", " decade ", " salvo che ",
)
_ZERO_WIDTH = {0x200b: None, 0x200c: None, 0x200d: None, 0x2060: None,
               0xfeff: None, 0x00ad: None}

DEFAULT_BOILERPLATE = (
    "la presente copia informatica, destinata unicamente alla pubblicazione sull'albo pretorio on line",
    "e' conforme al documento originale ai sensi del d.lgs. n. 82/2005",
    "il corrispondente documento digitalmente firmato e' conservato negli archivi",
)


def normalize(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_ZERO_WIDTH)
    s = "".join(ch for ch in s if ch >= " " or ch in "\n\t")
    s = (s.replace("’", "'").replace("‘", "'")
           .replace("“", '"').replace("”", '"')
           .replace("–", "-").replace("—", "-").replace(" ", " "))
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_grounded(quote: str, source: str) -> bool:
    q = normalize(quote)
    if len(q) < _MIN_QUOTE_CHARS:
        return False
    return q in normalize(source)


def _strip_boiler(text: str, bp) -> str:
    for b in bp:
        text = text.replace(b, " ")
    return re.sub(r"\s+", " ", text).strip()


def is_grounded_fuzzy(quote: str, source: str, boilerplate=DEFAULT_BOILERPLATE) -> bool:
    q = _strip_boiler(normalize(quote), boilerplate)
    src = _strip_boiler(normalize(source), boilerplate)
    if len(q) < _MIN_QUOTE_CHARS:
        return False
    return q in src


def _containing_sentence(src_norm: str, quote_norm: str) -> str:
    idx = src_norm.find(quote_norm)
    if idx < 0:
        return ""
    left = src_norm.rfind(". ", 0, idx)
    start = 0 if left < 0 else left + 2
    right = src_norm.find(". ", idx + len(quote_norm))
    end = len(src_norm) if right < 0 else right
    return src_norm[max(start, idx - 220):min(end, idx + len(quote_norm) + 220)]


def negation_context_risk(quote: str, source: str) -> bool:
    qn = normalize(quote)
    src = normalize(source)
    if len(qn) < _MIN_QUOTE_CHARS or qn not in src:
        return False
    sent = " " + _containing_sentence(src, qn) + " "
    quote_pad = " " + qn + " "
    for m in _NEG_MARKERS:
        if m in sent and m not in quote_pad:
            return True
    return False


def classify(quote: str, source: str) -> str:
    if is_grounded(quote, source):
        return "negation_risk" if negation_context_risk(quote, source) else "strict"
    if is_grounded_fuzzy(quote, source):
        return "fuzzy"
    return "absent"


def enforce_grounding(findings: list, source_text: str,
                      source_trust: str = "high") -> list[str]:
    """source_trust ('high'|'medium'|'low'): reliability of `source_text`. When the
    source came from OCR (medium/low), even a STRICT verbatim match is NOT allowed to
    back a condemnation -- the source itself is uncertain (a misread glyph could fake
    or break a match). Such findings are routed to human verify. OCR trust contract."""
    from .schema import Verdict
    notes: list[str] = []
    CONDEMNING = (Verdict.ARTIFACT_DEFECTIVE, Verdict.REDUCED, Verdict.PENDING)
    reasons = {
        "negation_risk": "GROUNDING: la frase-fonte contiene una negazione/eccezione che la citazione omette -> possibile fuori-contesto",
        "fuzzy": "GROUNDING: presente solo in forma non-verbatim (impaginazione) -> verificare a mano",
        "absent": "GROUNDING: quote non trovata verbatim nella fonte -> possibile allucinazione",
        "ocr_source": "GROUNDING: fonte da OCR (testo non certo) -> nessuna condanna su match verbatim; verifica umana",
    }
    ocr_source = source_trust not in ("high", None)
    for f in findings:
        base = getattr(f.accusation, "base", None)
        base_val = base.value if hasattr(base, "value") else base
        if base_val not in _GROUNDED_BASES:
            continue
        quote = getattr(f, "quote", None) or getattr(f.accusation, "evidence", "") or ""
        label = classify(quote, source_text)
        if label == "strict" and not ocr_source:
            continue
        reason_key = "ocr_source" if (label == "strict" and ocr_source) else label
        if f.verdict in CONDEMNING:
            f.verdict = Verdict.NEEDS_READING
        f.declared_limit = ((f.declared_limit + " | ") if f.declared_limit else "") + reasons[reason_key]
        notes.append(f"{f.id}: {reason_key} -> NEEDS_READING")
    return notes
