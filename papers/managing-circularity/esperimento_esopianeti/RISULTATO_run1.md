# Risultato run-1 — banco esopianeti (KOI, N=9.563 reali) — 2026-07-08
Dati: NASA Exoplanet Archive, tavolo `cumulative` via TAP (aperto, riproducibile).
Deterministico, nessun LLM. 1 riga corrotta (flag=465) scartata. Query in coda.

## Esiti sulle ipotesi pre-registrate

**H1 — accumulo di falsificazioni indipendenti → disposizione. CONFERMATA (p_perm=0.0000).**
media n_flag: FALSE POSITIVE 1.40 vs non-FP 0.004.

| n. falsificazioni indip. | FP | CAND | CONF | P(FP) |
|---|---|---|---|---|
| 0 | 95 | 1975 | 2729 | 0.020 |
| 1 | 3210 | 3 | 17 | 0.994 |
| 2 | 1042 | 0 | 0 | 1.000 |
| 3 | 489 | 0 | 0 | 1.000 |
| 4 | 3 | 0 | 0 | 1.000 |

**H2 — un solo FAIL indipendente abbatte (survivor gate / pavimento). CONFERMATA.**
P(FALSE POSITIVE | ≥1 falsificazione indipendente) = 4744/4764 = **99.6%**.
P(passa tutti e 4 i check | CONFIRMED) = 2729/2746 = **99.4%**.
→ è esattamente il gate del paper: l'affidabilità è SOPRAVVIVENZA a falsificazioni indipendenti;
una sola linea indipendente che falsifica porta a ⊥.

**H3 — i 4 flag sono linee INDIPENDENTI? IN GRAN PARTE SÌ.**
phi a coppie: nt·ss −0.23, nt·co +0.01, nt·ec +0.06, ss·co +0.15, ss·ec +0.10, **co·ec +0.52**.
5 coppie su 6 quasi-indipendenti (falliscono per ragioni diverse). Unica eccezione onesta:
centroide·ephemeris (co·ec) moderatamente correlati (condividono logica di contaminazione).
→ indipendenza reale, con un accoppiamento dichiarato.

**H4 — il profilo distingue dove il tier confonde. SOSTENUTA.**
Tra i SOPRAVVISSUTI (0 flag, n=4799): CONF 2729 · CAND 1975 · FP 95. I flag di falsificazione
tolgono il 98% dei FP; il residuo CONFIRMED-vs-CANDIDATE(k) è deciso dall'asse di conferma
POSITIVA (koi_score: FP 0.04 · CAND 0.80 · CONF 0.96). Lo strato CANDIDATE(k) copre TUTTO lo
spettro di score → il verdetto finale confonde traiettorie che il profilo separa (interleaving, 1° paper).

## Mappa sul paper (C3 + survivor gate + profilo)
- 4 domini di falsificazione indipendenti = survivor gate; accumulo con PAVIMENTO (un FAIL → ⊥).
- Passare tutti e 4 = necessario ma non sufficiente per ⊤; CANDIDATE = k (sopravvissuto, in attesa
  di conferma positiva). koi_score = asse di accumulo positivo verso ⊤.
- Il profilo (score dentro k) porta informazione oltre il tier finale.

## CAVEAT ANTI-TAUTOLOGIA (dichiarato, non nascosto)
Flag e disposizione provengono dalla stessa pipeline di vetting (Robovetter) ⇒ il test INTERNO
(flag→disposizione) è in parte DEFINITORIO: qui mostra che la tassonomia di affidabilità del
CAMPO *instanzia* la struttura del paper (C3 + survivor gate) su dati reali ad alto N, e ne
quantifica la separazione — ma non è, da solo, prova non-circolare. La parte MENO circolare è H3
(l'indipendenza reciproca dei flag NON è definitoria, e regge 5/6). Il test PORTANTE pre-registrato
resta: predire la conferma con METODO FISICAMENTE INDIPENDENTE (radial velocity/imaging, dal
tavolo `ps`) usando solo i domini-transito. È il prossimo passo.

## Query TAP (riproducibili)
- contingenza: select koi_fpflag_nt,koi_fpflag_ss,koi_fpflag_co,koi_fpflag_ec,koi_disposition,count(*) from cumulative group by (le 5 colonne)
- score:       select koi_disposition,round(koi_score,1),count(*) from cumulative group by koi_disposition,round(koi_score,1)
Endpoint: https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=...&format=csv

---

## RUN-2 — TEST ESTERNO ANTI-TAUTOLOGIA (canale fisicamente indipendente) — 2026-07-08
Verità da canale DIVERSO dal transito: massa da velocità radiale/dinamica (pl_bmassprov='Mass'
nel tavolo `ps`) — è Doppler/gravità, misurata da strumenti e pipeline diversi da Robovetter.
JOIN ADQL cumulative↔ps su kepler_name=pl_name (default_flag=1). Dati reali, riproducibile.

**Risultato:** dei pianeti con massa indipendente confermata (n=249 abbinati; 290 totali 'Mass'):
- disposizione da transito: **249/249 CONFIRMED** (nessuno era stato dato FP/CAND dal transito);
- profilo dei 4 flag di falsificazione da transito:
  - 0 flag (passa tutti e 4): **242 (97.2%)**
  - flag "eclisse secondaria" (ss): 6
  - flag "non-transit-like" (nt): 1

**Lettura (non-circolare):** la massa RV è un OSSERVABILE FISICO diverso dal transito. Che il
97.2% dei pianeti confermati per via indipendente superi anche il survivor-gate del transito è
concordanza tra due canali fisicamente distinti — non definitoria. I **7 discordanti** sono pianeti
che il transito avrebbe declassato (eclisse secondaria / forma) ma che l'RV conferma reali: è
l'ACCUMULO DI DOMINI INDIPENDENTI CHE RISOLVE L'ERRORE DI UN SINGOLO DOMINIO — la tesi del paper,
osservata su dati reali (fisicamente: hot-Jupiter reali possono avere eclisse secondaria; l'RV dirime).

**Limiti onesti (dichiarati):**
- Selezione di follow-up: l'RV si fa preferenzialmente su bersagli già promettenti ⇒ questo test
  misura la CONCORDANZA sulla classe positiva + i casi-riscatto, NON una ROC completa (i FALSE
  POSITIVE non ricevono RV, quindi non testabili per questa via). È un limite dei dati osservativi.
- Copertura join: 249/290 abbinati per nome (41 non abbinati per formati di nome).

**Bilancio dei due run:** il test interno (run-1) mostra che la tassonomia di affidabilità del
campo *instanzia* C3+survivor-gate ad alto N ma è in parte definitorio; il test esterno (run-2)
aggiunge la parte non-circolare: due canali fisici indipendenti concordano al 97%, e dove
divergono è il canale indipendente a correggere il singolo dominio. Più H3 (flag mutuamente
quasi-indipendenti, non definitorio). Nessun risultato gonfiato: limiti di selezione e copertura
messi in chiaro.
