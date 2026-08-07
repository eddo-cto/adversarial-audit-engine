# Invarianti di metodo — emendamento (admissibility + dichiarazione di classe)

> **Abstract (EN).** Three method invariants, hardened empirically. (1) **Admissibility:**
> a finding may be STRUCTURAL only if it exhibits a *reconstruction, from the artifact's own
> stated inputs, that fails to reproduce the artifact's own output*; everything else is FLAG.
> (2) **Class declaration:** every finding declares whether it rests on *reconstruction* (strong)
> or *judgement* (weak), and domain-specific re-derivation is declared out of reach unless the
> engine is given compute to execute it. (3) **Intention gate, scoped by normative nature:** first classify the
> artifact as *self-normed* (personal tool, internal doc) or *externally-normed* (legal appraisal,
> clinical study, filing, accountable to law/method/regulation regardless of the author's will). For
> self-normed artifacts, grade against the *declared intention* + internal correctness; for
> externally-normed ones, grade against the **external authority** (the declared intention is evidence,
> and a self-serving intention aggravates rather than excuses). The gate never immunizes a violation of
> an external standard. The "falsification lens" is a **derived profile** of the engine, not a new layer.

Questo documento estende gli invarianti già imposti dal nucleo (`aae/gates.py`, `aae/grounding.py`,
defense-gate, macchina a stati dei verdetti) senza aggiungere un layer. Vale la regola del **freno**:
il motore acquista *facoltà* raramente, *regole* e *profili* spesso.

---

## 1. Admissibility — la regola di ricostruzione fallita

**STRUTTURALE** è ammesso **solo** se il reperto esibisce una **ricostruzione, dagli input dichiarati
dall'artefatto stesso, che non riproduce l'output dell'artefatto stesso**. La ricostruzione va mostrata.
Ogni altro reperto — per quanto plausibile — è **FLAG**.

Perché è un invariante e non un accorgimento: converte *"l'auditor ha trovato qualcosa"* (non
falsificabile, sorgente di falsi positivi) in *"la ricostruzione non torna"* (verificabile da chiunque,
inclusa una natura diversa). È la disciplina che, nel grounding gate, già impedisce di condannare su una
citazione inesistente; qui la si estende dall'**esistenza della citazione** alla **riproduzione
dell'inferenza**.

Enforcement: il gate dei verdetti declassa a FLAG ogni reperto marcato STRUTTURALE che non porta con sé
la ricostruzione fallita.

## 2. Dichiarazione di classe e di competenza

Ogni reperto dichiara la propria **classe**:

- **Ricostruttivo (forte):** un numero/totale/tasso/denominatore/statistica che non riconcilia; una
  contraddizione interna fra due cose dichiarate (testo↔tabella↔figura); un entailment definitorio.
  Qui la ricomputazione è quasi forzata e il segnale è robusto.
- **Di giudizio (debole):** over-claim rispetto al disegno, controllo mancante, proxy vs criterio
  esterno. Ammissibili come FLAG, non come STRUTTURALE.
- **Fuori portata — re-derivazione di dominio:** difetti *presenti nel testo* ma rilevabili solo
  ri-eseguendo un modello (integrare equazioni, ricomputare una grandezza fisica con un modello di
  dominio, riconoscere la patologia di una formula specialistica). **Vanno dichiarati fuori portata**,
  non spacciati per copertura, **finché il motore non riceve compute per eseguirli** (il passaggio "al
  codice"). Un "non trovato" qui è un **falso nullo**, non un'assoluzione.

## 2-bis. Intention gate — graduare contro l'intenzione dichiarata, non contro una norma non adottata

Prima di graduare, il motore deve **estrarre e citare l'intenzione dichiarata dell'artefatto** (scopo,
profilo d'uso, filosofia di design, invarianti auto-dichiarati) e valutare ogni apparente difetto
**contro quella intenzione**, oltre che contro le norme generiche. Un reperto sopravvive **solo se
viola gli obiettivi che l'artefatto si è dato** — o la correttezza tout court — **non** una norma che
l'artefatto non ha mai adottato.

Perché è un invariante e non una cortesia: senza di esso il motore produce un failure mode **distinto
dall'allucinazione** — un **falso positivo di cornice / normativo**. Il fatto osservato è reale e
riproducibile (es. "questo modulo ha 2870 righe", "non c'è un package"); ciò che è non-grounded è la
**premessa normativa implicita** ("*quindi* è un difetto", perché il sistema "dovrebbe" essere
modulare / packaged / DRY / con CI). La **regola di admissibility (§1) NON lo intercetta**: la
ricostruzione del *fatto* torna; a essere sbagliato è il *giudizio*. È più insidioso dell'allucinazione,
perché è confidentemente errato in un modo che il proprietario del dominio percepisce all'istante come
"non hai capito cosa sia".

**Enforcement:** in testa a ogni corsa, un blocco "Intenzione dichiarata" con citazioni alla fonte.
Ogni reperto porta un verdetto rispetto a essa: *viola un obiettivo proprio dell'artefatto* (sopravvive,
spesso si rafforza) · *attacca una scelta deliberata e documentata* (ritirato/declassato) · *valido solo
sotto un obiettivo non adottato* (neutro/condizionale, con la condizione dichiarata).

### Distinzione di natura — a MONTE dell'intention gate (non negoziabile)
L'intention gate **non è universale**: è il caso speciale degli artefatti **auto-normati**. Prima di
applicarlo, il motore classifica la **natura normativa** dell'artefatto, e la classe sceglie il criterio:

- **Auto-normato** (strumento personale, documento interno, opera, prototipo): nessuna autorità esterna
  a cui l'artefatto sia tenuto a rispondere. Criterio = **intenzione dichiarata + correttezza interna**.
  Qui l'intention gate si applica pieno. *(Es. PFP: nessuno impone a un tool personale di essere un
  microservizio.)*
- **Etero-normato** (perizia legale, studio clinico, dichiarazione fiscale, bilancio, progetto
  ingegneristico): l'artefatto è **soggetto a un'autorità esterna** — la legge, il metodo scientifico,
  il regolamento, la fisica, i principi contabili, l'imparzialità professionale — **indipendente dalla
  volontà dell'autore**. Criterio = **congruenza con quell'autorità**. L'intenzione dichiarata è
  **prova**, non metro; e un'intenzione che confligge con la norma esterna (es. una perizia intesa a
  favorire una parte) è **essa stessa un reperto**, aggravante, non un'esimente.
- **Misto** (es. un paper scientifico: dichiara un intento di test d'ipotesi, ma è vincolato alla
  legge metodologica — validità statistica, no p-hacking): graduare contro **entrambi**; dove
  confliggono, **prevale la norma esterna**.

**Carve-out.** L'intention gate **non scusa mai** la violazione di uno standard autoritativo esterno.
Un'intenzione auto-servente **non immunizza** un artefatto etero-normato — lo aggrava. Questo impedisce
che l'intention gate diventi una scappatoia e lo tiene coerente con la **riga rossa** (per
perizie/appalti: flag di incongruenza con la legge, mai accusa) e con l'oracolo legale del motore.

**Origine empirica.** Emerso da un audit reale di una codebase in cui il motore, graduando contro norme
generiche di ingegneria del software (packaging, DRY, decomposizione in microservizi), aveva marcato
come "difetti" scelte di **semplicità deliberate e documentate** dal proprietario. La correzione ha
**ritirato 8 reperti su 24** e rafforzato quelli che violavano davvero gli obiettivi propri
dell'artefatto (un buco nel gate anti-allucinazione, soglie contro un invariante di trasparenza
auto-dichiarato). Da notare la meccanica: il gap è stato rivelato dal **push-back di un occhio esterno**
di identità diversa — cioè la **scala d'indipendenza che funziona come previsto**, non una precauzione.

## 3. La lente di falsificazione è un profilo, non un layer

La "lente" (protocollo fisso di classi d'attacco A–N applicato a paper pubblicati) è
un'**istanziazione congelata** di destruens + admissibility + defense-gate, configurata per un tipo di
bersaglio. Resta un **profilo/preset derivato**, tenuto a distanza di braccio dal nucleo:
- fondendola come layer si duplicherebbe il destruens (violazione del freno);
- diluendola nel motore generale perderebbe la calibrazione (bassi falsi positivi, confine dichiarato)
  che vale solo perché è **stretta**.

## 4. Backing empirico (perché questi invarianti, non a memoria)

Due bracci di validazione, con verità a terra costruita e reale.

- **Calibrazione a difetti innestati** (crossover appaiato, aggiudicazione cieca con civette): la lente
  rileva **in proporzione al residuo ricostruibile**. Difetti *presenti-e-verificabili* vs difetti
  d'*assenza*: **14/16 vs 2/8, Fisher una coda p = 0,0047**. Falsi positivi su controlli a verità a
  terra: **1/42 = 2,4%** (Wilson IC 95% 0,4–12,3%). È il fondamento empirico di §1 e §2.
  **Verificabile con un comando:** `python benchmarks/calibration/reproduce.py` ricalcola ogni cifra
  dal dataset per-item anonimizzato (in CI a ogni push); provenienza e nota di anonimizzazione — gli
  innesti sono *sintetici*, le identità dei paper restano nei registri sigillati privati — in
  `benchmarks/calibration/README.md`.
- **Errori reali** (via *Matters Arising*, verità a terra = confutazione formale di un esperto esterno):
  il confine **regge sul reale**, ed è più stretto di "presente/assente". Su 7 bersagli reali (audit
  ciechi sul solo originale, aggiudicazione separata, ri-aggiudicata in cieco): **0 falsi positivi su 7
  civette** cross-dominio (la specificità è il pregio forte, e transfer); la lente atterra **solo** sui
  difetti ricostruibili col **ragionamento generale** (aritmetica, contraddizione interna, entailment) —
  **1/1** — e **manca** quelli che richiedono **re-derivazione di dominio** (**0/3**) o dati esterni,
  la classe "fuori portata" di §2. Un blind-landing sulla causa reale di un **ritiro** (contraddizione
  Figura-vs-Tabella) conferma il lato ricostruttivo. La sensibilità reale di classe P è **1/4 = 25%**
  contro l'88% sintetico: il **crollo è il segnale** — è ciò che tiene onesta la stima sintetica, non
  la performance di un "detector". *n=7, nessuna significatività, nessun VALIDATED senza asse
  inter-natura esterno.* **Verificabile:** `python benchmarks/real_errors/reproduce.py` (in CI);
  provenienza e cornice — è **calibrazione di metodo**, non un foglio di accuratezza di prodotto — in
  `benchmarks/real_errors/README.md`.
- **Indipendenza di natura** — il test che il motore **non può fare su se stesso** (tutte le sue istanze
  condividono natura). Gli **stessi 7 bersagli reali** sono stati auditati in cieco da **tre nature** (la
  natura del motore + due modelli di vendor diverso), con **aggiudicazione da istanza fresca cieca**
  (coppie rimappate + civette cross-dominio, nessun accesso ai risultati precedenti). Le tre predizioni
  si confermano: (1) **il confine è nature-independent** — sui 4 bersagli P le tre nature danno il pattern
  di landing **identico** (atterrano solo sul difetto ricostruibile col ragionamento generale, 1/1;
  mancano tutti e 3 quelli di re-derivazione di dominio, 0/3); (2) **la natura diversa aggiunge** reperti
  reali che la natura del motore mancava (A-class 0→2→3, ρ<1, guadagno non saturo); (3) **la specificità
  sopravvive** — **0 falsi positivi su civette per ogni natura**, inclusa l'aggiudicatrice cieca. Il pregio
  forte — non allucinare — **non è un prior condiviso**: è una proprietà del compito. Porta il risultato
  reale dal livello 1-2 (natura sola) verso il **livello 3** (vendor diverso); la chiusura resta al
  livello 4 (occhio umano esterno). **Verificabile:** `python benchmarks/inter_nature/reproduce.py` (in
  CI); provenienza in `benchmarks/inter_nature/README.md`. Questo è il motivo per cui la scala
  d'indipendenza resta un invariante e non una precauzione.
- **Posizionamento vs baseline** (stesso compito, sui 7 bersagli reali): confronto controllato **stesso
  modello, prompt ingenuo vs disciplinato**. Il landing è **identico** (4/7, stessi bersagli) — la
  disciplina **non dà più catture**; taglia il rumore **~5×** (~88 reperti/paper ingenuo vs ~18 disciplinato,
  range 2,5–8,4×: il proxy dei falsi positivi che il defense-gate sopprime) e aggiunge un **confine
  dichiarato**. I 3 bersagli mancati da entrambi sono quelli di re-derivazione di dominio — mancati perfino
  da un firehose di 155 reperti: il confine è del **compito**, non della disciplina. Baseline deterministico
  (statcheck, OSS): **0/7** (classe disgiunta + fragilità di formato). È il "reliability without validity"
  del 2026 su dato reale. **Verificabile:** `python benchmarks/baselines/reproduce.py` (in CI);
  `benchmarks/baselines/README.md`.

## 5. Cosa NON cambia

- **Riga rossa**: mai consulenza; flag, mai accuse.
- **Nessun VALIDATO su base interna**: stato massimo `EXTERNAL_REVIEW_PENDING`; chiusura solo con
  occhio umano esterno. La re-derivazione di dominio e le run inter-natura *rafforzano* questa regola,
  non la sostituiscono. **Operazionalizzato come regola** (`aae/independence_ledger.py`,
  `build_independence_ledger`): ogni corsa può ora *emettere* il proprio stato d'indipendenza —
  livello raggiunto su tutte le identità partecipanti, se l'accordo è intra- o inter-natura, il tetto di
  verdetto e il caveat ρ. Nessun layer nuovo: rende emettibile ciò che la scala d'indipendenza già
  imponeva, così l'accordo non può essere spacciato per indipendenza. È il buco che il vicinato 2026
  ("reliability without validity") ammette e non emette.
- **Aggiudicazione anti-bias, come garanzia verificabile** (`aae/adjudication_guard.py`,
  `assess_adjudication`): la prassi di aggiudicazione cieca (coppie rimappate, civette cross-dominio,
  istanza fresca) è resa **immunità nominate e testabili** — *self-preference* (l'aggiudicatore non è tra
  gli auditor), *posizione* (la decisione è invariante al riordino dei candidati), *lunghezza* (il SÌ non
  correla con la lunghezza), *chiusura* (solo inter-natura o umano alza il tetto, delegata al ledger, così
  le due regole compongono). Sono i bias che la letteratura LLM-as-judge 2026 nomina (position/length/
  self-preference) e che il multi-agente same-nature **amplifica**: qui una corsa può *certificare* di
  esserne immune, invece di asserirlo. Regola/profilo, nessuna facoltà nuova.
- **Freno**: risposta proporzionata; niente layer nuovi per ciò che una regola o un profilo risolvono.

## 6. Round 9 — indurimento della chiusura (il motore ha auditato se stesso)

Un'istanza indipendente del motore (altro account, natura diversa) auditando la bozza del paper di
sistema ha sostenuto **quattro accuse contro le garanzie di chiusura** del motore stesso — che erano
codice *narrato*, non enforced. Tutte corrette e fissate da test di regressione
(`tests/test_gates_and_verdicts.py`, `tests/test_closure_hardening.py`, `tests/test_benchmarks_guards.py`):

- **F-VENDOR** — `evaluate_completion` faceva `external != internal` (disuguaglianza di stringa), mai un
  check di vendor. Ora è **vendor-aware**: `CROSS_MODEL_REVIEWED` solo a livello 3 (vendor diverso);
  same-vendor → nuovo stato `INTRA_VENDOR_REVIEWED` (livello 2, priori condivisi, non validato).
- **F-HUMAN** — `VALIDATED` era `startswith("human")`, e il payload lo scrive il modello. Ora la
  chiusura umana è **fuori-banda**: richiede `AAE_HUMAN_ATTESTATION` dall'ambiente operatore, che il
  modello non può fabbricare. Rende *vera in codice* la frase "il processo non può auto-validarsi"
  (in linea con la sorveglianza umana effettiva, cfr. AI Act art. 14).
- **F-HOOK** — lo Stop hook `governor_check.py` informava e usciva sempre 0. Ora **legge lo stato
  persistito e declassa** su disco un `VALIDATED` privo di attestazione fuori-banda (secondo lucchetto,
  nell'ambiente operatore). Enforcement senza bloccare la sessione.
- **F-SECTIONS** — la regola "≥2 sezioni per un non-locale" viveva solo in `orchestrator.integrity_report`,
  inerte sul percorso documentato. Ora `run_core` chiama `integrity_report()` e ne emette i problemi come flag.

Nessun layer nuovo: le tre famiglie di gate (defense, coverage, indipendenza/chiusura) restano; la
chiusura passa da *convenzione su stringa* a *codice enforced in due punti* (macchina a stati + hook).
Prima del round 9 "la disciplina è codice" reggeva per due gate su tre; il motore ha trovato il buco in
sé e chiuderlo ha reso la tesi vera su tutte e tre.

## 7. Round 11 — chiusura crittografica (primo audit di natura diversa, livello 3)

Il primo audit di **vendor diverso** (livello 3, non-Anthropic) ha mostrato che le due garanzie di
chiusura che il round-10 aveva solo *dichiarato* come residui (C1, C2) erano ancora convenzioni. Ora
sono **enforced in codice** (`aae/attestation.py`, `gates.py`, `run_core.py`, `governor_check.py`;
test in `test_gates_and_verdicts.py`, `test_closure_hardening.py`):

- **C2 — chiusura umana crittografica.** `VALIDATED` richiede un **HMAC** valido sul digest del ledger
  (`content_digest` su nome-artefatto + reperti) con una chiave operatore fuori-banda (`AAE_HUMAN_KEY`),
  che il modello non possiede. Un token non-firma non valida più nulla; l'hook `Stop` **ri-verifica**
  l'HMAC e declassa qualsiasi `VALIDATED` non firmato. Il modello autore del payload **non può**
  auto-validarsi, punto — non per convenzione ma per crittografia.
- **C1 — indipendenza attestata, non dichiarata.** Il livello 3 (`CROSS_MODEL_REVIEWED`) è accreditato
  **solo** dall'identità che l'adapter ha davvero chiamato (`AAE_EXTERNAL_ATTESTED_IDENTITY`). Un'identità
  di vendor diverso presente solo nel payload è `CROSS_MODEL_CLAIMED` e la sua indipendenza **non è
  accreditata** (livello 1). Chiude il buco `notanthropic:whatever → livello 3`.

Nessun layer nuovo: stessa macchina a stati, due nuovi stati onesti (`CROSS_MODEL_CLAIMED`) e una verifica
crittografica al posto di un controllo di presenza-stringa. È l'indipendenza di natura diversa che, come
previsto dalla scala, ha trovato ciò che gli audit stesso-vendor non vedevano — e stavolta su una
garanzia di chiusura, non solo sul testo del paper.

## 8. Round 12 — standardizzazione, step 1 (dai run di dominio-finanza)

Run reali su dominio etero-normato (finanza) hanno mostrato la fragilità che conta per uscire dal
prototipo: **il nucleo in codice è bypassabile** — una run può *narrare* i gate invece di *eseguirli*,
e allora perde pezzi (oracolo che non chiude il ciclo, metriche non emesse, denominatore ignoto). Primo
passo di standardizzazione, indurito da un prototipo prodotto in parallelo dal motore stesso:

- **Source-grade gate** (`aae/source_grade.py`, §7.1): l'oracolo indifferente al *grado* della fonte non
  è uno scudo anti-falsi-positivi, è un amplificatore (dà a un errore di terzi l'autorità del "fatto
  documentato"). Regola enforced in codice: una condanna (`ARTIFACT_DEFECTIVE`) che poggia su un dato di
  grado > primario, quando un documento primario è reperibile, è declassata a `NEEDS_READING`.
  **Data-driven**: il grado è un campo sul `Finding` (`source_grade`), letto dal payload, non una tabella
  a posteriori. L'operatore può dichiarare `source_primary_reachable=false` (nessuna primaria esiste) e
  il gate si astiene.
- **Flag di auto-strumentazione** (`run_core`, §7.6): una run ad alta posta che non registra **nessuna
  ipotesi scartata** (`action_state=deliberately_discarded`) ha un denominatore generato/scartato ignoto
  → la disciplina sui falsi positivi è *asserita, non misurata*. Il buco silenzioso diventa un flag.

Invariante di metodo che ne discende: **niente layer che una misura mostra inerte, niente run che possa
barare passando per la prosa**. La sequenza dichiarata è *strumenta → misura → pota → rendi obbligatorio
il core minimo*; questo è lo `strumenta`. Il meta-livello che rende il nucleo **non bypassabile** e la
potatura dei layer non portanti sono i passi successivi — da fare dopo aver misurato, non prima.

### Round 13 — manifesto d'esecuzione (step 2: la *misura*)

`aae/run_manifest.py`. Definisce, verso la regola-metodo *"è una run **sse e solo se** (A) il core
minimo è girato **e** (B) ogni altro layer porta un verdetto applicabile/no giustificato"*, il
**contenitore**: per ogni stage dichiarato uno stato `RAN | NOT_APPLICABLE(giustificato) | MISSING`, e
un `run_validity`. Due scelte non negoziabili:

- **Misura, non impone.** `REQUIRED_LAYERS` è lasciato **vuoto** di proposito → `run_validity =
  RECORD_ONLY`. Il minimo va **popolato dalla misura** (quali layer guadagnano il posto tra le classi
  d'artefatto), non assunto dallo sprawl attuale. Congelare un minimo non misurato è l'unico passo falso.
  La logica A+B è scritta ma **dormiente** finché `REQUIRED` non è popolato.
- **I layer emittenti sono misurati dal *dato* (`source_role`), non auto-dichiarati** (`measured=True`):
  sul loro contributo il modello non può mentire. I non-emittenti (oracolo, triage, governor,
  external-auditor) restano dichiarati, ma ora **registrati e contestabili** — è la condizione B resa
  visibile. Rende misurabili anche i layer che non producono findings, il buco che `source_role` da solo
  lasciava cieco.

Prossimo passo (non ancora fatto): far emettere il manifesto a più run reali di **classi diverse**,
leggere il contributo per layer, **poi** popolare `REQUIRED` e accendere la IFF A+B in `run_core`
(il gate non-bypassabile). Solo allora la regola diventa metodo, non prototipo con un vestito da metodo.
