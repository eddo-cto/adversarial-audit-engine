# N4 — controllo del confound di popolazione (gene fisso) via computer use — 2026-07-09
Il revisore ha giustamente riaperto N4: le faccette per review-status confrontano popolazioni diverse.
Controllo tenendo FISSO il gene (popolazione più omogenea), via UI ClinVar. Frazione VUS(=k)/tot:

| gene | 1★ single | 2★ multiple concordi | 3★ expert panel |
|------|---|---|---|
| BRCA1 | 32,9% (1578/4794) | 35,6% (820/2303) | **0,6%** (19/3404) |
| MLH1  | 42,0% (1225/2915) | 41,2% (897/2179) | **2,7%** (19/702) |

## Esito (nuancé, onesto)
1. **1★→2★ PIATTO dentro il gene** (BRCA1 33%→36%, MLH1 42%→41%): la discesa 60,9%→44,6% della
   popolazione intera **era in gran parte confound di popolazione** — l'accumulo di più sottomettitori
   *peer* NON risolve k. Il revisore aveva ragione.
2. **3★ expert panel: CROLLO che regge dentro il gene** (0,6% / 2,7%, ~15–50× più basso): la
   risoluzione di k **non** viene dall'accumulo di canali peer, ma da un **livello di aggiudicazione
   indipendente e di autorità superiore** (expert panel: ENIGMA per BRCA1, InSiGHT per MLH1). NON è
   artefatto di popolazione (l'expert panel copre anche le varianti difficili).

## Perché è più interessante del claim ingenuo
Risuona con la tesi stessa del paper: k si chiude non per accumulo tra pari, ma per l'**occhio esterno
indipendente e autorevole** — l'analogo empirico della "chiusura affidata all'occhio esterno".
Caveat: due geni (illustrativo, non esaustivo); il test pieno resta longitudinale (stesse varianti nel
tempo), non ottenibile qui. Fonte: UI ClinVar, filtri Review status × gene. Riproducibile.
