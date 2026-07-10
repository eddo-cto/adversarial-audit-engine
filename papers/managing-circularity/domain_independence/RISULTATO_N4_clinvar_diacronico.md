# N4 chiuso — ClinVar review_status × verdetto (via UI facets, computer use) — 2026-07-09
Ottenuto guidando la UI web di ClinVar (le faccette danno l'incrocio corretto; il campo significatività
NON si aggancia in eutils). NIENTE file bulk. Solo struttura; mai interpretazione clinica.

## Risoluzione dell'astensione all'accumularsi di concordanza indipendente
| review status (accumulo canali indip.) | tot germline | VUS (=k) | P+LP |
|---|---|---|---|
| 1★ single submitter | 3.290.338 | **60,9%** | 7,4% |
| 2★ multiple submitters, no conflicts | 662.778 | **44,6%** | 18,7% |
| 3★ reviewed by expert panel | 22.128 | **17,6%** | 57,0% |

La frazione d'astensione (VUS=k) **cala monotonicamente 60,9% → 44,6% → 17,6%** e il verdetto definito
(P+LP) cresce 7,4% → 18,7% → 57,0% man mano che si accumula concordanza tra canali indipendenti /
revisione. È l'analogo genetico dell'accumulo→CONFIRMED degli esopianeti: **l'accumulo di linee
indipendenti risolve k in ⊤/⊥.** Chiude la lettura diacronica che N4 chiedeva.

## Caveat onesti
- I tier mescolano "più concordanza indipendente" con "tipo di revisione" (expert panel = autorità
  diversa) e con popolazioni di varianti diverse (l'expert-panel è un sottoinsieme curato). Il calo
  monotono di VUS è quindi indicativo del fenomeno, non un esperimento controllato a popolazione fissa.
- VUS è categoria pulita (singola); le celle combinate (Benign/Likely benign) nelle faccette si
  sovrappongono, quindi P+LP è approssimato. Le frazioni VUS sono robuste.
- Fonte: UI ClinVar (faccette Germline classification sotto filtro Review status). Riproducibile.
