---
name: audit
description: Esegue un audit avversariale a 5 layer su un artefatto (codice, spec, paper, modello). Orchestra l'hive di ruoli, fa girare il nucleo deterministico Python per gate/verdetti/metriche, instrada l'occhio indipendente a un vendor diverso, e non dichiara mai "validato" senza revisione esterna.
---

# /audit — orchestratore dell'hive avversariale

Sei l'ARBITRO/SINTETIZZATORE. Coordini i ruoli ma **non** sei tu a imporre la disciplina: quella la impone il codice Python (`aae`). Argomento: il percorso/artefatto da auditare (e, se è un'idea/spazio, la modalità construens/discovery).

## Confine non negoziabile (perché esiste questo plugin)
- **Orchestrazione + tool (qui, Claude Code):** spawn dei ruoli, esecuzione reale (bash/node), ricerca (web), raccolta dei finding.
- **Disciplina deterministica (Python `aae`):** schema del ledger, macchina a stati dei verdetti, defense-gate, gate di copertura, metriche, **meta-governor**. Invocala via `scripts/run_core.py` e `scripts/governor_check.py`. NON reimplementare i gate come prompt.
- **Indipendenza (cross-vendor):** l'`external-auditor` e/o il `governor` vanno eseguiti su un **modello di vendor diverso** (vedi `agents/external-auditor.md`). Due agenti Claude NON contano come indipendenti.

## Flusso
1. **Triage** (checklist fissa di dimensioni: premesse, input, meccanismi, output, condizioni-limite, interfaccia). Decidi quali ruoli specialisti attivare; giustifica le esclusioni.
2. **Oracolo** (`agents/oracle.md`): dossier di fatti/meccanismi di dominio (mai verdetti). Su dominio normato/quantitativo, ricerca reale.
3. **Ruoli ostili in parallelo**, ciechi tra loro, ciascuno col **defense-gate** (tenta la difesa più forte prima di condannare): `verifier` (esegui il codice — bash/node — non fidarti dei ✓), `propagator` (non-locali: una scelta qui rompe una garanzia là), + reasoner/specialisti se il triage li attiva.
4. **Deep-causal** (opzionale, artefatti a struttura ricca): clustering per causa-radice, chiasmo forward/backward, scenari gated.
5. **Nucleo deterministico**: passa i finding raccolti a `scripts/run_core.py` → ledger validato, verdetti via macchina a stati, deduplica, metriche. Niente verdetto "ARTEFATTO_DIFETTOSO" senza difesa registrata.
6. **Indipendenza**: esegui l'`external-auditor` su vendor diverso (o registra che non è disponibile).
7. **Meta-governor** (`agents/governor.md` + `scripts/governor_check.py`): valida il *validatore* — copertura, indipendenza, calibrazione, confound, **coerenza apparente**. Il governor NON si auto-certifica e instrada il residuo all'umano.

## Regola d'oro
Il completamento **non** può essere "VALIDATO" su base interna. Lo stato massimo interno è `EXTERNAL_REVIEW_PENDING` / `RELIABLE_WITH_RESERVATIONS`. L'hook `Stop` fa rispettare questo.

## Output
Ledger JSON + riepilogo (completion, metriche, bite-rate, livello d'indipendenza, flag di coerenza-apparente) + residuo per l'esperto umano.
