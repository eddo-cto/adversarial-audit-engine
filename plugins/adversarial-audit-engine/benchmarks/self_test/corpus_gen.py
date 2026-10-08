"""
corpus_gen.py — deterministic seeded corpus with INJECTED defects for the G self-test (1.12).

Builds labelled cases in the engine's real domains (financial / auction / credential), each with defects at
EXACT byte spans (so match.py can locate them), plus ~20% no-defect cases for the false-positive rate.
Synthetic/public text only — NEVER client data. stdlib only; deterministic for a given seed.

A case: {id, domain, label, source_text, defects:[{defect_id, defect_class, span:[s,e], severity, verbatim}]}.
The build tracks byte offsets as it concatenates segments, so span is exact by construction (asserted).
"""
from __future__ import annotations

import hashlib
import json
import random

# templates: (domain, prefix, DEFECT verbatim, defect_class, severity, suffix, CLEAN verbatim replacing the defect)
# the clean variant turns the same template into a no-defect case (true statement in place of the false one).
_TEMPLATES = [
    ("financial", "Relazione Q4. ", "il totale è 45 kg mentre 12+17+26 fa 55", "numeric", 3,
     ". Nessun altro rilievo.", "il totale è 55 kg, pari a 12+17+26"),
    ("financial", "Sintesi: ", "i ricavi salgono da 80 a 100, un aumento del 30%", "numeric", 2,
     ". Fine sezione.", "i ricavi salgono da 80 a 100, un aumento del 25%"),
    ("auction", "Avviso lotto 7. ", "si richiama la perizia del CTU non presente agli atti", "non_local_conceptual_documented", 3,
     ". Segue descrizione.", "si richiama la perizia del CTU allegata agli atti"),
    ("auction", "Dati catastali. ", "l'immobile è al foglio 17 particella 42 mentre la scheda riporta foglio 73", "lookup", 2,
     ". Rendita invariata.", "l'immobile è al foglio 73 particella 42 come la scheda"),
    ("auction", "Perizia §8. ", "la superficie commerciale 21,88 mq non concorda con la netta 15,05 mq", "numeric", 2,
     ". Stima conforme.", "la superficie commerciale 17,30 mq concorda con la netta 15,05 mq"),
    ("credential", "Scheda fornitore. ", "il partner dichiara lo status Gold certificato mai rilasciato", "credential", 3,
     ". Referenze allegate.", "il partner dichiara lo status Gold certificato e verificato alla fonte"),
    ("credential", "Reputazione. ", "l'agenzia vanta il premio Best Agency 2024 inesistente", "credential", 2,
     ". Recensioni online.", "l'agenzia riporta recensioni verificate sui portali"),
]


def _build(domain, prefix, defect_vb, dclass, sev, suffix, clean_vb, defective: bool, idx: int) -> dict:
    body = defect_vb if defective else clean_vb
    source = prefix + body + suffix
    case = {"id": f"{domain[:3].upper()}{idx:03d}", "domain": domain,
            "label": "defective" if defective else "clean", "source_text": source, "defects": []}
    if defective:
        start = len(prefix)
        end = start + len(defect_vb)
        assert source[start:end] == defect_vb, "span mismatch"   # exact by construction
        case["defects"].append({"defect_id": f"{case['id']}-d1", "defect_class": dclass,
                                "span": [start, end], "severity": sev, "verbatim": defect_vb})
    return case


def generate(n: int = 40, p_clean: float = 0.2, seed: int = 20260711) -> list[dict]:
    rng = random.Random(seed)
    cases = []
    for i in range(n):
        tmpl = _TEMPLATES[rng.randrange(len(_TEMPLATES))]
        defective = rng.random() >= p_clean
        cases.append(_build(*tmpl, defective=defective, idx=i))
    return cases


def manifest(cases: list[dict]) -> dict:
    blob = json.dumps(cases, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {"n_cases": len(cases),
            "n_defective": sum(1 for c in cases if c["label"] == "defective"),
            "n_clean": sum(1 for c in cases if c["label"] == "clean"),
            "sha256": hashlib.sha256(blob).hexdigest()}


def split(cases: list[dict], holdout_frac: float = 0.4, seed: int = 20260711) -> dict:
    """Stratified-by-domain split into dev / holdout, by CASE. Returns {dev:[ids], holdout:[ids], hash}."""
    rng = random.Random(seed)
    by_dom: dict[str, list[str]] = {}
    for c in cases:
        by_dom.setdefault(c["domain"], []).append(c["id"])
    dev, hold = [], []
    for dom, ids in sorted(by_dom.items()):
        ids = sorted(ids); rng.shuffle(ids)
        k = round(len(ids) * holdout_frac)
        hold += ids[:k]; dev += ids[k:]
    return {"dev": sorted(dev), "holdout": sorted(hold),
            "holdout_frac": holdout_frac, "sha256": manifest(cases)["sha256"]}
