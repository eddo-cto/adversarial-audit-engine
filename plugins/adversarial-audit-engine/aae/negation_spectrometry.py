"""negation_spectrometry.py — standard riutilizzabile contro la SOVRA-DEMOLIZIONE
(falsificatory overfitting): un falsificatore potente puo' demolire anche artefatti VALIDI,
gonfiando il Type-I error della falsificazione. Questo modulo lo rende un numero MISURATO.

Due assi ('spettro della negazione'):
  1) DISCRIMINABILITA' (Type-I per-auditor). Calibra un auditor su una CONTROL BATTERY:
     artefatti VALIDI (devono sopravvivere) + INVALIDI (devono morire). Misura:
        FDR = P(demolisce | valido)     -> tasso di falsa-demolizione (Type-I)
        TDR = P(demolisce | invalido)   -> potere
        AUC = separabilita' del punteggio di demolizione (0.5 = negazioni-rumore)
  2) PERSISTENZA tra auditor INDIPENDENTI (componente 'armonica'). Una negazione sollevata
     da k-of-m auditor di vendor diversi e' armonica (stabile); da un solo auditor e'
     alta-frequenza (sospetta di overfit).

TEOREMA (controllo del Type-I di falsificazione). Se m auditor INDIPENDENTI hanno tasso di
falsa-demolizione <= p sui validi, una negazione SPURIA sopravvive a un filtro k-of-m con
probabilita' <= B(k;m,p) = sum_{j>=k} C(m,j) p^j (1-p)^(m-j). Per k=m e' p^m: la persistenza
tra auditor indipendenti sopprime il Type-I ESPONENZIALMENTE.

Standard: AMMETTI una negazione se (discriminabilita' dell'auditor OK) E (persistenza
cross-vendor >= k/m). Riporta il residuo Type-I ASSUNZIONE-FREE (empirical_type1), che
cattura la CORRELAZIONE tra auditor (blind-spot condivisi) che p^m ignora.

Stdlib only (math), niente numpy: piu' pulito per un plugin.
"""
from __future__ import annotations
from math import comb


def calibrate(scores_valid, scores_invalid, threshold: float = 0.5) -> dict:
    """FDR (Type-I), TDR (potere), AUC (Mann-Whitney) del punteggio di demolizione."""
    v = [float(x) for x in scores_valid]; iv = [float(x) for x in scores_invalid]
    FDR = sum(1 for x in v if x >= threshold) / len(v) if v else 0.0
    TDR = sum(1 for x in iv if x >= threshold) / len(iv) if iv else 0.0
    # AUC = P(score_invalid > score_valid) con mezzo-punto sui pari
    wins = 0.0
    for a in iv:
        for b in v:
            wins += 1.0 if a > b else (0.5 if a == b else 0.0)
    AUC = wins / (len(iv) * len(v)) if (iv and v) else 0.5
    return {"FDR": FDR, "TDR": TDR, "AUC": AUC}


def binom_tail(k: int, m: int, p: float) -> float:
    """B(k;m,p) = P(Binom(m,p) >= k): probabilita' di sopravvivenza spuria sotto k-of-m."""
    return float(sum(comb(m, j) * p**j * (1 - p)**(m - j) for j in range(k, m + 1)))


def empirical_type1(valid_demolitions, k: int) -> float:
    """Type-I ASSUNZIONE-FREE: data la matrice (N_valid x m) binaria delle demolizioni dei
    m auditor sui VALIDI, ritorna P(>=k auditor demoliscono un valido). Cattura la
    correlazione tra auditor. Sempre >= p^m; uguale solo sotto vera indipendenza."""
    rows = [list(r) for r in valid_demolitions]
    if not rows:
        return 0.0
    return sum(1 for r in rows if sum(r) >= k) / len(rows)


def admit(neg_by_auditor: dict, auditor_fdr, k: int, max_fdr: float = 0.2) -> dict:
    """neg_by_auditor: {finding_id: vettore binario sugli m auditor (sollevata?)}.
    Ammette un finding se sollevato da >= k auditor con FDR <= max_fdr (solo discriminativi)."""
    m = len(auditor_fdr)
    ok = [i for i in range(m) if auditor_fdr[i] <= max_fdr]
    admitted, discounted = [], []
    for fid, vec in neg_by_auditor.items():
        support = sum(vec[i] for i in ok)
        (admitted if support >= k else discounted).append((fid, support))
    p_max = max([auditor_fdr[i] for i in ok], default=1.0)
    return {"admitted": admitted, "discounted": discounted,
            "type1_bound": binom_tail(k, len(ok) or m, p_max),
            "k": k, "m_effective": len(ok), "p_max": p_max}


def _demo():
    """Verifica numerica del teorema (stdlib random): l'ammissione-spuria empirica combacia
    col bound binomiale, e mostra il trade-off k-of-m."""
    import random
    random.seed(20260630)
    p, m, T = 0.25, 4, 4000
    print("k-of-m | empirica falsa-ammissione | teoria B(k;m,p) | potere")
    for k in range(1, m + 1):
        false_admit = 0; power = 0
        for _ in range(T):
            spur = [1 if random.random() < p else 0 for _ in range(m)]   # negazione spuria
            true = [1 if random.random() < 0.9 else 0 for _ in range(m)]  # negazione vera (potere 0.9)
            false_admit += sum(spur) >= k
            power += sum(true) >= k
        print(f"  {k}/{m}  |  {false_admit/T:6.1%}  |  {binom_tail(k,m,p):6.1%}  |  {power/T:6.1%}")


if __name__ == "__main__":
    _demo()
