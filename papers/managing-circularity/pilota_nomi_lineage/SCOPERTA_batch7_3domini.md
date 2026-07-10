# Finding — terzo dominio (vernacolo) e il vincolo di precisione del join — 2026-07-04

Aggiunto D3 "vernacolo germanico" (ampiezza di nativizzazione nelle lingue germaniche
continentali + forme contratte) al batch reale di 7 nomi. Confronto 2 vs 3 domini,
accumulo = join su C3, verita' = etimologia DMNES (fonte terza).

## Risultato
| nome | vero-G | morf | attest | vernac | 2dom | 3dom |
|------|:---:|---|---|---|:---:|:---:|
| Theodoric | sì | TOP | TOP | TOP | TOP | TOP |
| Robert | sì | k | TOP | k | TOP | TOP |
| Gerard | sì | k | k | **TOP** | k | **TOP** |
| William | sì | k | k | k | k | k |
| Theodore | no | k | k | BOT | k | k |
| Nicholas | no | BOT | k | **TOP** | k | **TOP** |
| George | no | BOT | k | **TOP** | k | **TOP** |

- **2 domini:** TP=2 FP=0 FN=2 TN=3 — recall germ 2/4, **0 falsi-TOP**.
- **3 domini:** TP=3 FP=2 FN=1 TN=1 — recall germ 3/4, **2 falsi-TOP**.

D3 **recupera Gerard** (recall sale) MA fa passare a TOP **Nicholas e George** (greci),
perche' sono nomi di santi popolarissimi, foneticamente nativizzati in area germanica
(Claus/Klaas, Görg/Georg). Sotto il **join monotono**, il falso-TOP di UN dominio impreciso
propaga: la precisione crolla da 0 a 2 errori.

## Perche' e' un finding che RAFFORZA il paper (non lo indebolisce)
Il modello del paper e' accumulo-**join** con pavimento monotono (l'affidabilita' non scende).
Questo batch mostra empiricamente il **lato duale**: il join propaga anche i falsi-positivi.
Corollario di design, verificato su dati reali:

> Sotto accumulo-join i domini devono essere ad **ALTA PRECISIONE** (survivor-gate: TOP solo
> con evidenza forte, altrimenti ASTENERSI a k). Il recall si guadagna sommando **molti domini
> precisi**, non uno largo. Un dominio "ampiezza di nativizzazione" misura POPOLARITA' in area
> germanica, non ORIGINE: viola la disciplina del survivor-gate (committe TOP su evidenza debole).

E' esattamente la ragione per cui il paper insiste su indipendenza-per-provenienza e gate
conservativi. Il vernacolo-ampiezza NON e' un buon dominio; un vernacolo-**origine** lo sarebbe
(TOP solo su riflesso germanico ereditato PRIMA della diffusione come nome di santo; altrimenti k).

## Disposizione (cosa fare, senza contaminare)
1. Ridisegnare D3 come survivor-gate ad alta precisione: fire TOP solo se esiste una forma
   vernacolare germanica ATTESTATA PRECOCEMENTE (es. pre-1150) con divergenza forte dal lemma
   (Dietrich<Theodoric): cattura Theodoric/Gerard, NON Claus/Görg (nativizzati tardi). Validare
   su held-out, non sui 7 che l'hanno rivelato.
2. Per i non-germanici serve un rilevatore ATTIVO greco/latino (porta a BOT, non solo k).
3. La serie lunga n=60-80 serve a misurare la CURVA precisione/recall all'aumentare dei domini,
   non un singolo caso. Questo batch (n=7) e' il pilota che fissa il vincolo di design.

Provenienza: banco_batch_reale.py + morfologia.py + parser_dmnes.py + vernacolare.py su
dmnes_pages/*.txt (pagine grezze dmnes.org ediz. 2023). Deterministico, nessun punteggio a mano.

---

## AGGIORNAMENTO — vernacolo PRECISO (survivor-gate) vs LARGO: le tre configurazioni

| config | recall germ | falsi-TOP |
|--------|:---:|:---:|
| 2 domini (morf+attest) | 2/4 | 0 |
| 3 dom LARGO (vern-ampiezza) | 3/4 | **2** |
| 3 dom PRECISO (vern survivor-gate) | 2/4 | 0 |

Il gate preciso (TOP solo su riflesso germanico ereditato, precoce ≤1300, divergente dal lemma,
forma piena ≥6: Dietrich<Theodoric passa, Claus/Görg no) **ripristina 0 falsi-TOP** ma
**non recupera Gerard**: identico ai 2 domini. Spara TOP solo su Theodoric — che morf+attest
gia' prendevano. E' DISCIPLINATO ma REDUNDANTE su questo set.

## Conclusione netta (la piu' onesta)
Il buco di recall (William, Gerard) **non e' un problema di "mancano domini": e' un difetto
DENTRO la morfologia** — forme erose/assimilate (helm assente; ger+**ard** con perdita di h;
Hrod→**Rob**). Nessun terzo dominio preso dalla STESSA fonte (DMNES) lo colma:
- il vernacolo-LARGO "recupera" Gerard per la ragione sbagliata (popolarita' in area germanica) e
  paga 2 falsi-TOP;
- il vernacolo-PRECISO non introduce errori ma non porta segnale NUOVO sui casi mancati.

**Corollario per il paper (rafforzativo).** Aggiungere domini alza il recall SOLO se i domini sono
(i) indipendenti per provenienza, (ii) ad alta precisione, (iii) portatori di segnale NUOVO sui
casi mancati. Un dominio che viola anche solo uno dei tre non aiuta (o danneggia, via join).
Qui il rimedio corretto e' duplice e NON contaminante:
1. correggere la morfologia sulle forme erose (helm; varianti -ard/-art; assimilazioni Hrod→Rob),
   validando su un set HELD-OUT diverso dai 7 che l'hanno rivelato;
2. per la vera indipendenza, il prossimo dominio va preso da una FONTE DIVERSA (CDL/MGH come
   provenienza fisica separata), non da un altro taglio di DMNES.

Questo n=7 e' il pilota che ha fissato, su dati reali, il vincolo di design del join. La serie
n=60-80 servira' a misurare la CURVA recall/precisione all'aggiunta di domini indipendenti e precisi.
