# Arm 3 (STRESS TEST) — NVD/CVE (cybersecurity) — 2026-07-08
Dominio scelto per METTERE ALLA PROVA la domain-independence (massimamente lontano da fisica/genetica).
Dati reali NVD API 2.0 (aperta), campione da finestre 2024–25. Deterministico. n=116 CVE unici.

## Struttura presente (la tesi NON si rompe)
- Ordinale di stato del verdetto: Analyzed 34 · Modified 52 · Deferred 28 · **Rejected 2**.
  = maturazione + tier di rifiuto (⊥) e "deferred" (contestato/sospeso ~ k).
- Canali indipendenti: NVD (Primary) vs CNA/CISA-ADP (Secondary). Su 116 CVE: 79 con Primary,
  78 con Secondary, **43 con ENTRAMBI**.
- Disaccordo REGISTRABILE su tutta la popolazione con doppio scorer (no bias di follow-up).

## Il numero che sorprende (e rifinisce la tesi)
**Disaccordo di severità tra scorer indipendenti: 24/43 = 55,8%.** In cybersecurity due valutatori
indipendenti divergono nella MAGGIORANZA dei casi — molto più che in ClinVar (19,8%) e degli esopianeti
(quasi-concordanza sulla classe positiva).

## Lettura (stress test: esito nuancé, non fallimento)
- La STRUTTURA è domain-independent: canali indipendenti + verdetto graduato + tier d'astensione/rifiuto
  + disaccordo registrato ricorrono anche qui.
- Ma il TASSO DI CONVERGENZA è domain-DEPENDENT: esopianeti (alta concordanza) → ClinVar (20%) →
  NVD (56% disaccordo). Cioè: *la forma dell'accumulo è universale, il grado di convergenza no.*
  Questo non falsifica il paper — lo rifinisce: alcuni domini sono strutturalmente più "contesi",
  e lì l'affidabilità-per-accumulo satura più lentamente / resta più spesso in k.

## Limiti onesti (dichiarati)
- n=43 con doppio scorer: stima con intervallo ampio; è un primo valore, non definitivo (fetch
  limitati da rate-limit NVD + cap di salvataggio).
- Confronto severità può incrociare VERSIONI CVSS diverse (v3.1 Primary vs v4.0 Secondary): scale
  diverse ⇒ parte del 56% può essere artefatto di versione. Un'analisi pulita confronta stessa-versione.
- baseSeverity categorico: conta anche divergenze adiacenti (HIGH vs CRITICAL) come disaccordo.
Fonte: https://services.nvd.nist.gov/rest/json/cves/2.0 (aperta, riproducibile).

## AGGIORNAMENTO N3 (chiusura richiesta dal revisore) — same-version + n maggiore
Ri-eseguito su 174 CVE unici. Confronto Primary vs Secondary ristretto alla STESSA versione CVSS (v3.1):
disaccordo 39/65 = **60,0%**, essenzialmente identico all'any-version (24/43 = 55,8%). ⇒ il ~56-60%
**NON è un artefatto cross-versione**. n=65 resta modesto (braccio più debole dei tre), ma il concern
principale del revisore è chiuso.
