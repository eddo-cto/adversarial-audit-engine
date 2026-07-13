# -*- coding: utf-8 -*-
"""
support_geometry.py — layer RIFLESSIVO del motore: legge la GEOMETRIA DEL SUPPORTO
di un corpo di claim già giudicati e ne segnala la FRAGILITÀ.

Origine: prima istanza operativa del "quantale controfattuale a linee parallele"
(esperimento paper-2). La scoperta cablata qui: il ledger PIATTO nasconde che alcuni
claim marcati "chiusi" poggiano su UNA SOLA linea di verifica; la geometria delle
linee indipendenti lo rende visibile. Questo modulo generalizza quel readout.

COSA FA e COSA NON FA (disciplina invariante del progetto):
  - NON emette verdetti, NON valida, NON chiude. Produce una LETTURA della robustezza
    (fragilità = fonte-unica / linee poco ortogonali) da instradare all'OCCHIO UMANO.
  - Compone (non compete) col motore: il motore emette verdetti/astensioni per artefatto;
    questo layer legge la geometria dell'INSIEME dei claim sopravvissuti. È lo stesso
    impegno epistemico (accumulo per falsificazioni-fallite, indipendenza k-di-m), reso
    geometrico: il C3 (bot < k < top) è l'ombra di questa struttura a una soglia.

Regola d'oro anti-Goodhart (come usage_ledger):
  Il flag "fragile" NON può diventare un TARGET del gate del motore. Descrive la
  geometria; non decide. Se diventasse target, si ottimizzerebbe la geometria invece
  della sostanza — il fallimento che il 2° paper descrive.

Riserva dichiarata (dall'audit del motore, non nascosta):
  l'ortogonalità è qui istanziata con JACCARD (cardinalità). La forma residuale
  (metrica di Lawvere) della definizione generale NON è ancora istanziata: vedi
  `orthogonality(..., form=)`. Chiusura all'occhio umano.

Deterministico, stdlib only. Nessun LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Callable, Iterable


# --------------------------------------------------------------------------- #
#  Base controfattuale (down-set dell'ordine di presupposizione)              #
# --------------------------------------------------------------------------- #
def _transitive_closure(order):
    o = set(order)
    changed = True
    while changed:
        changed = False
        for (a, b) in list(o):
            for (c, d) in list(o):
                if b == c and (a, d) not in o and a != d:
                    o.add((a, d)); changed = True
    return o


def counterfactual_base(claims, order=None):
    """Frame dei down-set dell'ordine di presupposizione (x<y: confermare y
    presuppone x). Senza ordine -> powerset (booleano). Con ordine -> non-booleano."""
    claims = list(claims)
    lt = _transitive_closure(order or set())
    below = {y: {x for (x, yy) in lt if yy == y} for y in claims}
    B = []
    for r in range(len(claims) + 1):
        for s in combinations(claims, r):
            S = frozenset(s)
            if all(below.get(y, set()) <= S for y in S):
                B.append(S)
    return B


def is_boolean(B, unit):
    return all(any((u | v) == unit and not (u & v) for v in B) for u in B)


# --------------------------------------------------------------------------- #
#  Nuclei di taratura (una linea di verifica = un nucleo aperto o_u)          #
# --------------------------------------------------------------------------- #
def heyting_imp(B, u, a):
    out = frozenset()
    for c in B:
        if (c & u) <= a:
            out = out | c
    return out


def open_nucleus(B, u):
    return lambda a: heyting_imp(B, u, a)


def is_nucleus(B, j):
    return (all(a <= j(a) for a in B)
            and all((not (a <= b)) or (j(a) <= j(b)) for a in B for b in B)
            and all(j(j(a)) == j(a) for a in B)
            and all((j(a) & j(b)) <= j(a & b) for a in B for b in B))


# --------------------------------------------------------------------------- #
#  Ortogonalità fra linee                                                     #
# --------------------------------------------------------------------------- #
def jaccard(a, b):
    if not (a | b):
        return 0.0
    return 1.0 - len(a & b) / len(a | b)


def orthogonality(a, b, form="jaccard"):
    """Distanza fra due ground di linee. form='jaccard' (istanza finita corrente).
    form='residual' RISERVATO (metrica di Lawvere, da istanziare — vedi docstring)."""
    if form == "jaccard":
        return jaccard(a, b)
    raise NotImplementedError("forma residuale non ancora istanziata (riserva D2 dichiarata)")


# --------------------------------------------------------------------------- #
#  Lettura per claim + report di fragilità                                    #
# --------------------------------------------------------------------------- #
@dataclass
class ClaimSupport:
    claim: str
    lines: list
    orth_max: float
    severity: str                    # "fragile" (fonte-unica/nessuna) | "debole" | "ok"
    reason: str = ""

    @property
    def fragile(self):
        return self.severity == "fragile"

    @property
    def weak(self):
        return self.severity == "debole"


@dataclass
class SupportGeometry:
    base_size: int
    boolean: bool
    nuclei_ok: dict
    per_claim: list = field(default_factory=list)

    def fragility_report(self):
        """Claim FRAGILI = fonte-unica o non sostanziati. Da instradare all'occhio
        umano (NON un verdetto): sono i più a rischio di crollo."""
        return [c for c in self.per_claim if c.fragile]

    def weakness_report(self):
        """Claim DEBOLI = >=2 linee ma poco ortogonali (sostegno non indipendente)."""
        return [c for c in self.per_claim if c.weak]


def analyze(claims, lines, order=None, weak_threshold=0.6, form="jaccard"):
    """Legge la geometria del supporto. `lines`: nome_linea -> set di claim che
    quella linea (fonte di verifica indipendente) ha effettivamente confermato.

    Fragile <=> fonte-unica (una sola linea) OPPURE linee poco ortogonali
    (orth_max < weak_threshold): il claim non ha sostegno indipendente robusto.
    """
    claims = list(claims)
    B = counterfactual_base(claims, order)
    unit = frozenset(claims)
    nuclei_ok = {}
    for name, ground in lines.items():
        g = ground if ground in B else frozenset(x for x in ground if x in unit)
        nuclei_ok[name] = is_nucleus(B, open_nucleus(B, g))

    per = []
    for w in claims:
        sup = [k for k in sorted(lines) if w in lines[k]]
        if len(sup) >= 2:
            omax = max(orthogonality(lines[a], lines[b], form)
                       for a, b in combinations(sup, 2))
        else:
            omax = 0.0
        severity, reason = "ok", ""
        if len(sup) == 0:
            severity, reason = "fragile", "nessuna linea: claim non sostanziato"
        elif len(sup) == 1:
            severity, reason = "fragile", "FONTE UNICA (%s)" % sup[0]
        elif omax < weak_threshold:
            severity, reason = "debole", "linee poco ortogonali (max %.2f < %s)" % (omax, weak_threshold)
        per.append(ClaimSupport(w, sup, omax, severity, reason))

    return SupportGeometry(len(B), is_boolean(B, unit), nuclei_ok, per)


# --------------------------------------------------------------------------- #
#  Smoke __main__ : riproduce il finding della prima istanza operativa        #
#  (il ledger AAE della sessione -> 3 claim a fonte unica: w4, w6, w8)        #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    CLAIMS = ["w1", "w2", "w3", "w4", "w5", "w6", "w7", "w8"]
    ORDER = {("w7", "w2"), ("w7", "w3"), ("w7", "w5"), ("w5", "w6"),
             ("w5", "w8"), ("w2", "w8"), ("w3", "w8")}
    LINES = {
        "L_pip":   frozenset({"w1", "w2", "w3", "w5", "w6", "w7", "w8"}),
        "L_cieca": frozenset({"w5", "w7"}),
        "L_gem":   frozenset({"w3", "w7"}),
        "L_dim":   frozenset({"w1", "w2", "w3", "w4", "w7"}),
        "L_lett":  frozenset({"w7"}),
    }
    sg = analyze(CLAIMS, LINES, ORDER)
    print("base=%d booleana=%s nuclei=%s" % (sg.base_size, sg.boolean, sg.nuclei_ok))
    frag = sg.fragility_report()
    print("claim FRAGILI (%d) - instradati all'occhio umano:" % len(frag))
    for c in frag:
        print("  %s: %s" % (c.claim, c.reason))
    weak = sg.weakness_report()
    print("claim DEBOLI (%d):" % len(weak))
    for c in weak:
        print("  %s: %s" % (c.claim, c.reason))
    assert {c.claim for c in frag} == {"w4", "w6", "w8"}, "fragili attesi w4,w6,w8"
    assert {c.claim for c in weak} == {"w1", "w2"}, "deboli attesi w1,w2"
    assert sg.base_size == 60 and not sg.boolean and all(sg.nuclei_ok.values())
    print("SMOKE OK: 3 fonte-unica (w4,w6,w8) + 2 deboli (w1,w2) = prima istanza operativa.")
