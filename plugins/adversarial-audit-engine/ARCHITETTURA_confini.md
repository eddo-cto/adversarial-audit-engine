# Plugin Claude Code — architettura dei confini (ibrido, non monolite)

Il plugin realizza il verdetto dell'analisi: **Claude Code come guscio di orchestrazione + tool + distribuzione**, **Python `aae` come nucleo deterministico**, **un vendor diverso per l'occhio indipendente**. "Tutto-Claude-Code" è respinto perché bloccherebbe l'indipendenza al livello 1 (singolo vendor) — il limite che il governor segnala in ogni round.

## I tre confini

### 1. Claude Code (orchestrazione + tool + distribuzione)
- **Ruoli = agent-definition** (`agents/*.md`): oracle, verifier, propagator, governor, external-auditor. Spawnati dal comando `/audit`.
- **Esecuzione reale**: bash/node (il verifier *esegue* il codice — è ciò che ha colto crash mancati da audit a sola lettura).
- **Ricerca**: web/MCP (l'oracolo).
- **Distribuzione**: plugin/marketplace; `/audit` come entry point.
- **Enforcement leggero**: hook `Stop` → `scripts/governor_check.py`.

### 2. Python `aae` (disciplina deterministica) — NON reimplementare come prompt
- Schema del ledger, **macchina a stati dei verdetti**, **defense-gate**, **gate di copertura**, deduplica, metriche, **rilevatore deterministico del governor**.
- Invocato come tool/script: `scripts/run_core.py` (gate+verdetti+metriche sui finding raccolti) e `scripts/governor_check.py` (verdetto di affidabilità).
- Motivo: la verifica ostile ha bocciato il prompt-engineering a favore del software-engineering. I gate restano **codice**, non istruzioni a un agente che potrebbe aggirarle.

### 3. Cross-vendor (indipendenza reale) — il punto che Claude Code da solo non dà
- `external-auditor` e/o `governor` vanno eseguiti su un **modello di vendor diverso** (OpenAI/Gemini/locale), via un **MCP server** o uno script-tool che chiama l'altra API e implementa l'interfaccia `LLMClient` di `aae`.
- Solo così il livello d'indipendenza sale da 1 (stessa istanza Claude) a 3 (vendor diverso) — l'unica leva interna che il governor riconosce.
- L'`external-auditor` dichiara il proprio modello/vendor nell'output; il governor assegna il livello e declassa l'affidabilità se è ancora Claude.

## Regola d'oro imposta dal codice
Nessun "VALIDATO" su base interna. Stato massimo: `EXTERNAL_REVIEW_PENDING` / `RELIABLE_WITH_RESERVATIONS`. L'hook `Stop` lo ricorda a ogni chiusura e instrada il residuo all'occhio umano. Ricorsione: meta¹ + umano, **niente meta²**.

## Cosa resta model-agnostic (per i test reali su altri LLM)
Il nucleo `aae` non dipende da Claude: gira identico dietro qualsiasi `LLMClient`. Il plugin è il *canale Claude Code*; lo stesso nucleo può essere orchestrato altrove. Per i test reali cross-modello, bastano gli adapter per-vendor + l'assegnazione di modelli diversi ai ruoli critici.

```
plugin/
  .claude-plugin/plugin.json     manifest
  commands/audit.md              /audit — orchestratore
  agents/                        ruoli (oracle, verifier, propagator, governor, external-auditor)
  hooks/hooks.json               Stop -> governor_check
  scripts/
    governor_check.py            enforcement deterministico (mirror di aae.meta_epistemic)
    run_core.py                  (da agganciare a aae: gate+verdetti+metriche)   [stub]
  ../aae/                        il nucleo deterministico Python (5 layer)
```
