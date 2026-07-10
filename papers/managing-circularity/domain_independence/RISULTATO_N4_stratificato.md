# N4 — dose-risposta STRATIFICATA per anni-nel-sistema — 2026-07-09
Chiude il confound nominato dal revisore v11: "il n. di sottomettitori è un proxy del TEMPO, non una
causa della risoluzione?". Test discriminante: a parità di esposizione, più canali risolvono di più?

## Metodo
Stesso file `submission_summary.txt.gz`. Coorte: born-VUS, **peer-only** (mai expert panel), ≥3
sottomissioni datate (N=166.009). Età-nel-sistema = anni dalla prima sottomissione datata allo
snapshot (2026). Stratifico età × n. sottomettitori distinti. "Risolta" = maggioranza ultime-3 = DEF.
Script: `n4_stratificato.awk`. Deterministico, nessun voto LLM.

## Risultato — tasso di risoluzione (%)
| anni nel sistema | 3–4 sottom. | 5–9 sottom. | 10+ sottom. |
|---|---|---|---|
| 0–2  | 6,4 % (n=10.493)  | 16,3 % (n=589)    | 50,0 % (n=2)     |
| 3–5  | 6,3 % (n=46.654)  | 12,8 % (n=8.508)  | 25,4 % (n=177)   |
| 6–9  | 19,6 % (n=51.079) | 29,5 % (n=20.283) | 35,7 % (n=1.963) |
| 10+  | 27,0 % (n=12.119) | 39,7 % (n=10.877) | 58,2 % (n=3.265) |

## Lettura
- **Entro OGNI stascia d'età** il tasso sale col n. di sottomettitori (monotòno; la cella 0–2×10+ è
  n=2, senza peso). ⇒ a parità di esposizione, più canali indipendenti risolvono di più.
- Il tempo conta anch'esso (sale lungo le colonne), come atteso; ma l'effetto-accumulo è presente
  **dentro** il tempo fissato ⇒ il conteggio dei sottomettitori NON stava solo leggendo l'orologio.
- **Conclusione**: l'accumulo fa lavoro causale (per quanto uno stratified control possa mostrarlo).
  L'alternativa "è solo tempo trascorso" è **falsificata** dalla tabella. Tesi Parte III sostenuta.

## Limiti residui (onesti)
La stratificazione NON è randomizzazione; la trattabilità della variante può ancora correlare col n.
di sottomettitori dentro uno strato. Ma l'alternativa specifica del revisore (solo esposizione) cade.
