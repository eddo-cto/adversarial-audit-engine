# Runbook — calibrazione Type-I con batteria estesa general-v3

Obiettivo: stringere il bound Type-I (falsa demolizione) dell'auditor da 0% [0–14%] (n=24, general-v2)
a 0% [0–7%] (n=48, general-v3). L'auditor è `anthropic:claude-sonnet-5` (quello del box cloud).

## File già pronti (in questa cartella)
- `batteries/general-v3.json` — 48 validi + 12 invalidi (24 nuovi controlli validi auto-verificati).
- `blind_general-v3.md` — **il file cieco: SOLO questo va dato all'auditor** (ID neutri A01–A60).
- `_key_general-v3.json` — **chiave privata: NON darla mai all'auditor**.
- `score_blind.py` — de-anonimizza il risultato con la chiave e calibra in un colpo.

## Passi nel box (Claude Code, auditor cieco)
1. Apri Claude Code in questa cartella. Dai all'auditor **solo** il contenuto di `blind_general-v3.md`
   (è auto-contenuto: gli chiede di giudicare i 60 artefatti e scrivere `blind_result_general-v3.json`).
   Nessun altro file, nessuna ricerca: giudizio a vista, difesa più forte prima di condannare.
2. A fine run deve esistere `blind_result_general-v3.json` (lista di `{"id":"A##","condemned":bool}`, 60 voci).
3. **Scoring + calibrazione** (una riga):
   ```
   python3 score_blind.py anthropic:claude-sonnet-5 blind_result_general-v3.json _key_general-v3.json "%AAE_CALIBRATION%" general-v3
   ```
   (Se `%AAE_CALIBRATION%` non è impostata, ometti quel parametro: scrive nel `_calibration.jsonl` locale.)
   Stampa la riga di citazione e appende il record allo store.
4. Al prossimo `/audit`, la Type-I citata diventa quella di general-v3 (il core prende il record più
   recente per identità auditor). Verifica che il summary mostri `n=48`.

## Onestà del metodo
- I 24 nuovi controlli **validi** sono affermazioni corrette ma "esca" (sembrano sbagliate): un falso
  positivo qui = l'auditor condanna una cosa giusta. Sono tutti verificati per calcolo prima di entrare
  in batteria (uno, miglia→km, è stato scartato perché fragile in virgola mobile).
- Il bound è a 0 falsi: 0/48 → 7,4%. Per <5% servono ~72 validi (un'altra tornata: general-v4).
- Nessuna calibrazione è "validazione": misura un tasso su una batteria finita; la certezza cresce con N.
