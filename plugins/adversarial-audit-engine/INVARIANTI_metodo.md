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
- **Errori reali** (via *Matters Arising*, verità a terra = confutazione formale di un esperto): il
  confine tiene sul reale — i bersagli che richiedono **re-derivazione di dominio** vengono mancati
  (fondamento di §2, "fuori portata"). Un blind-landing sulla causa reale di un ritiro conferma il lato
  "ricostruttivo".
- **Indipendenza di natura** (conferma empirica della scala d'indipendenza già imposta dal motore):
  su un'altra famiglia di modello, **il confine è riprodotto** (stesso pattern presente/assente: P=1/4,
  atterraggio solo sul difetto di contraddizione interna) e **la specificità sopravvive**
  (nessuna allucinazione: i reperti strutturali della natura diversa sono catture reali di incoerenza,
  etichettate come tali). Il pregio forte — non allucinare — **non è un prior condiviso**: è una
  proprietà del compito. Questo è il motivo per cui la scala d'indipendenza resta un invariante e non
  una precauzione.

## 5. Cosa NON cambia

- **Riga rossa**: mai consulenza; flag, mai accuse.
- **Nessun VALIDATO su base interna**: stato massimo `EXTERNAL_REVIEW_PENDING`; chiusura solo con
  occhio umano esterno. La re-derivazione di dominio e le run inter-natura *rafforzano* questa regola,
  non la sostituiscono.
- **Freno**: risposta proporzionata; niente layer nuovi per ciò che una regola o un profilo risolvono.
