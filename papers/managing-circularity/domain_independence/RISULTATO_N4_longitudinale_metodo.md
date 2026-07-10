# N4 — Test longitudinale ClinVar: RISULTATO su popolazione intera — 2026-07-09

## Dato e metodo
Fonte: ClinVar `submission_summary.txt.gz` (bulk ufficiale NCBI, aperto), 6.375.497 sottomissioni.
Ogni riga = una sottomissione datata con classificazione, review-status, sottomettitore.
Coorte FISSA per costruzione: le varianti sono tracciate nel tempo mentre laboratori indipendenti
si aggiungono → il confound di popolazione (che aveva affossato l'analisi a-faccette) è azzerato.
Selezione: varianti **nate VUS** (prima sottomissione datata = "Uncertain significance") con **≥3
sottomissioni datate**. N = **169.218** varianti.
"Risolta" = maggioranza delle 3 sottomissioni più recenti è definitiva (P/LP/B/LB). Proxy, non
l'aggregato ufficiale ClinVar (vedi caveat).

## Risultato (deterministico, riproducibile)
| percorso | risolte a DEF |
|---|---|
| con **EXPERT PANEL** nel percorso | 1.704 / 3.209 = **53,1 %** |
| **PEER-ONLY** (mai expert panel)  | 31.015 / 166.009 = **18,7 %** |

**Dose-risposta peer-only** (per n. di sottomettitori distinti):
| sottomettitori | risolte |
|---|---|
| 3–4  | 16.893 / 120.345 = **14,0 %** |
| 5–9  | 11.476 / 40.257  = **28,5 %** |
| 10+  | 2.646 / 5.407    = **48,9 %** |

Tempo medio a risoluzione (peer-only): **7,8 anni**.

## Lettura (separa i due meccanismi sulle STESSE varianti)
1. **L'autorità risolve meglio**: l'ingresso di un expert panel ~triplica il tasso di risoluzione
   rispetto ai soli pari (53% vs 19%). Coerente con la tesi dell'occhio esterno del paper.
2. **Ma l'accumulo NON è piatto**: il tasso peer-only cresce monotòno 14%→28%→49% col numero di
   canali indipendenti. L'accumulo di pari indipendenti risolve k — è la tesi "affidabilità per
   accumulo su canali indipendenti", ora mostrata longitudinalmente a coorte fissa.
3. **Convergenza**: a forte accumulo (10+ pari, 48,9%) il peer-only si avvicina al tasso
   dell'expert panel (53,1%). L'accumulo di molti pari indipendenti *approssima* l'autorità.
4. La risoluzione è **lenta** (~7,8 anni): k persiste a lungo prima di risolversi.

Questo **rifinisce** e corregge il controllo gene-fisso a-faccette (che vedeva 1★→2★ piatto):
quello era un artefatto d'aggregazione fra popolazioni diverse; la coorte fissa rivela l'effetto
accumulo reale.

## Caveat onesti (per il paper, riga rossa: mai interpretazione clinica di varianti)
- "Risolta" è un proxy (maggioranza ultime-3), non l'aggregato ufficiale ClinVar.
- Le varianti con expert panel sono un sottoinsieme selezionato (3.209): i panel si riuniscono su
  varianti già contese/importanti → il 53% NON è una stima causale pulita. FLAG, non conclusione.
- La dose-risposta potrebbe in parte riflettere che varianti più "trattabili" attraggono più
  sottomettitori; la coorte-fissa (tutte nate VUS) controlla il punto di partenza ma non del tutto
  la trattabilità. Il trend monotòno è l'evidenza centrale, dichiarata con questo limite.
- Uso della fonte: solo STRUTTURA della tassonomia di affidabilità (chi/quando/quale livello di
  review), mai interpretazione clinica delle singole varianti.

## Stato residuo N4
Da "bloccato: servono archivi storici" → **CHIUSO in forma piena**: la traiettoria per-variante è
nel record corrente (sottomissioni datate), nessun archivio necessario; misurata su popolazione
intera. Riproducibile: `submission_summary.txt.gz` → cut f1,2,3,7,10 → awk (script in repo).
