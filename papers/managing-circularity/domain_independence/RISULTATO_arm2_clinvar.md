# Arm 2 — ClinVar / ACMG (genetica clinica): la struttura ricorre — 2026-07-08
Dati reali NCBI ClinVar via eutils (campo [Review Status] verificato bindare). SOLO struttura
della tassonomia di affidabilità; MAI interpretazione clinica di varianti. Deterministico.

## L'ordinale d'accumulo di concordanza indipendente (review status = gold stars)
| review status | n | lettura |
|---|---|---|
| no assertion criteria (0★) | 142.001 | affidabilità minima |
| criteria, single submitter (1★) | 3.290.338 | 1 canale |
| criteria, multiple submitters, no conflicts (2★) | 662.778 | ≥2 canali indipendenti CONCORDI |
| criteria, CONFLICTING classifications | 163.647 | disaccordo tra canali REGISTRATO |
| reviewed by expert panel (3★) | 22.128 | |
| practice guideline (4★) | 663 | |

## Il risultato pulito (ciò che gli esopianeti non potevano dare)
Tra le varianti con ≥2 sottomettitori indipendenti (826.425), il **tasso di disaccordo registrato
è 163.647/826.425 = 19,8 %**. È una misura del disaccordo tra canali indipendenti **su tutta la
popolazione multi-classificata**, senza il bias di follow-up degli esopianeti (dove i falsi positivi
non ricevevano il secondo canale). Qui il secondo canale (un altro laboratorio) c'è per costruzione
su ogni variante multi-sottomessa → agreement E disagreement misurabili su entrambe le classi.

## Mappa sul paper
- review status = asse di ACCUMULO di concordanza indipendente (0★→4★): affidabilità cresce col
  numero/qualità di canali indipendenti concordi. È la tesi diacronica-per-accumulo, in genetica.
- "conflicting" = classe di DISACCORDO esplicita (l'analogo, ma non selezionato, dei 7 casi-riscatto).
- VUS (uncertain significance) = k (astensione): il verdetto resta aperto quando l'evidenza non chiude.
- Sistema PROGETTATO dall'uomo (ACMG) che *codifica* la struttura del paper → è una conferma che il
  pattern non è un artefatto di un singolo dominio, ma un modo ricorrente di costruire affidabilità
  senza verità unica. Questo è il punto domain-independence.

## Limiti onesti (ceiling di questo arm via eutils)
- Il campo significatività NON si aggancia in eutils (ricade su All Fields) ⇒ l'incrocio pulito
  review_status × verdetto (benign/VUS/pathogenic) richiede il file bulk variant_summary (~200MB),
  non fetchabile qui. Riportati solo i marginali review_status, che bindano puliti.
- "conflicting" è una regola d'aggregazione di ClinVar (soglia sul disaccordo dei sottomettitori):
  classe definita-da-pipeline, ma registra genuina divergenza tra canali indipendenti.
- Lo star-ordinal mescola "numero di canali" e "tipo di revisore" (expert panel = revisione diversa,
  non solo più canali): non è un puro conteggio di linee indipendenti. Dichiarato.

## Fonti (riproducibili)
NCBI eutils esearch, db=clinvar, term="<stato>"[Review Status]. Endpoint:
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
