# Pre-registrazione — banco esopianeti (affidabilità per accumulo di domini indipendenti)
Congelata 2026-07-08. Deterministico, nessun voto LLM. Fonte aperta e riproducibile:
NASA Exoplanet Archive, servizio TAP (HTTP puro → CSV). Query = artefatti permanenti.

## 0. Perché questo testbed
Sostituisce il pilota-nomi (n=7, dati non puliti) con un dominio dove i tre criteri del
finding precedente sono NATURALMENTE soddisfatti: domini (i) indipendenti per provenienza,
(ii) precisi, (iii) informativi sulla verità — su dati aperti, alto N, fetch deterministico.

## 1. Unità e verdetto C3
- Unità = un Kepler Object of Interest (KOI): la claim "questo segnale di transito è un pianeta".
- Verdetto C3 = koi_disposition: {FALSE POSITIVE ⊥ < CANDIDATE k < CONFIRMED ⊤}.
  Dati reali (tavolo `cumulative`): FP 4839 · CANDIDATE 1978 (=k) · CONFIRMED 2747.
- Riscontro monotòno già osservato: koi_score medio 0.038 / 0.80 / 0.96 sui tre tier.

## 2. Domini INDIPENDENTI (le linee d'accumulo) — quattro test di falsificazione distinti
Ognuno è un cross-check fisico diverso che può FALSIFICARE la claim (survivor gate):
- koi_fpflag_nt  = Not-Transit-Like (forma curva di luce / strumentale)
- koi_fpflag_ss  = Stellar eclipse / secondario significativo (binaria a eclisse)
- koi_fpflag_co  = Centroid Offset (sorgente contaminante — astrometrico)
- koi_fpflag_ec  = Ephemeris match / contaminazione (match periodo-epoca con altra sorgente)
Quinto segnale continuo: koi_score (vetting probabilistico indipendente).
Dominio a PROVENIENZA fisicamente diversa (per l'anti-tautologia): conferma con METODO
indipendente dal transito (radial velocity / imaging), dal tavolo `ps` (discoverymethod).

## 3. Modello d'accumulo (mappa sul paper)
Ogni dominio → C3: PASS (nessuna falsificazione) vs FAIL (falsifica → ⊥) vs astensione (k).
Accumulo = join sul lato conferma (max) e pavimento sul lato falsificazione (un FAIL indipendente
abbatte). Affidabilità = SOPRAVVIVENZA a N tentativi indipendenti di falsificazione.
Asse diacronico = accumulo di linee indipendenti (non tempo di calendario). Profilo = come il
verdetto satura all'aggiunta di domini.

## 4. Ipotesi pre-registrate (falsificabili)
- H1 (accumulo→affidabilità): n. di domini PASS traccia monotonamente la disposizione.
  Falsificata se i PASS non separano CONFIRMED da FALSE POSITIVE.
- H2 (survivor/floor): ≥1 flag indipendente FAIL ⇒ tasso di FALSE POSITIVE molto alto
  (una falsificazione indipendente uccide). Duale del join.
- H3 (indipendenza): i quattro flag sono genuinamente indipendenti — bassa correlazione a
  coppie tra gli esiti diagnostici. Se alta → non è accumulo di linee indipendenti (allarme).
- H4 (profilo oltre il join): koi_score continuo distingue traiettorie DENTRO lo strato
  CANDIDATE(k) che il tier finale confonde — collega la distanza d'interleaving del 1° paper.

## 5. ANTI-TAUTOLOGIA (punto portante, dichiarato)
Rischio: disposition e flag nascono da pipeline di vetting (parzialmente) condivise ⇒
"i flag predicono la disposizione" potrebbe essere in parte definitorio.
Mitigazione pre-registrata:
- Test PORTANTE = predire la CONFERMA con METODO INDIPENDENTE (radial velocity/imaging), che è
  provenienza diversa dal transito, usando SOLO i domini transito. Rompe la circolarità.
- Il test interno (vs disposition) è DESCRITTIVO; quello esterno (vs metodo indipendente) è
  quello su cui si regge la tesi. Riportare entrambi, distinti.

## 6. Scoring e statistica
Deterministico, a regole (mai LLM). Quantizzazione in C3, accumulo, confronto con disposition
e con conferma-esterna. Effetti + test di permutazione. Tutto da CSV TAP salvati (riproducibili).

## 7. Criterio di fallimento del metodo
Se l'accumulo di domini indipendenti NON separa i tier meglio di un singolo dominio, OPPURE i
quattro flag sono fortemente correlati (non indipendenti), la tesi FALLISCE su questo testbed.
Esito negativo = risultato, non da nascondere.

## 8. Query TAP (riproducibili) — esempi già verificati
- disposizione: select koi_disposition,count(*) from cumulative group by koi_disposition
- score/tier:   select koi_disposition,avg(koi_score),count(*) from cumulative group by koi_disposition
- metodi:       select discoverymethod,count(*) from ps where default_flag=1 group by discoverymethod
Endpoint: https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=...&format=csv
