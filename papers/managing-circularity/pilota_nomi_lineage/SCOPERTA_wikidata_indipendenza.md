# Finding — dominio a provenienza GENUINAMENTE indipendente (Wikidata) — 2026-07

Seguendo la via del paper (vera indipendenza-per-provenienza), NON ho usato CDL/MGH:
**DMNES li ingerisce** (li cita come fonti: `[CDL-1.1.1]`, `[MGH-DD]`) → non sarebbero
indipendenti. Ho preso **Wikidata via SPARQL**: provenienza disgiunta (biografie
Wikipedia vs editori di cartulari), aperta, e ogni query e' un **artefatto riproducibile**.

## Ostacolo reale (onesto) su fonti aperte indipendenti
Le fonti primarie indipendenti fetchabili senza JS sono scarse: Trismegistos/Regesta Imperii/
papyri.info tornano shell vuote (client-rendered); i papiri ravennati tardo-antichi NON coprono
i nomi germanici MEDIEVALI (mismatch cronologico). Wikidata SPARQL e' l'unica fonte insieme
indipendente + aperta + riproducibile + interrogabile via HTTP. Anche li', il join sui paesi
(per la frazione in area germanofona) supera il timeout WDQS di 60s: tenuto il segnale leggero
(precocita' del portatore celebre + conteggio).

## Dati reali (query.wikidata.org, 2026-07)
| nome | vero-G | WD earliest | WD n | DMNES earliest |
|------|:---:|---|---|---|
| Theodoric | sì | 454 | 224 | 673 |
| William | sì | 500 | 2486 | 928 |
| Gerard | sì | 800 | 232 | 779 |
| Robert | sì | 650 | 1171 | 890 |
| Theodore | no | 400 | 104 | 814 |
| Nicholas | no | 793 | 417 | 1106 |
| George | no | 500 | 556 | 1032 |

## Due risultati
1. **Indipendenza confermata.** Pearson(WD_earliest, DMNES_earliest) = **+0.33**: bassa. Le due
   provenienze non si eco-replicano — è indipendenza reale, non due copie della stessa fonte.
   (Wikidata è sistematicamente più precoce: cattura re goti/imperatori bizantini che i cartulari
   medievali non hanno.)
2. **Ma il segnale non porta ORIGINE.** corr(WD_earliest, è-germanico) = **+0.12** ≈ 0.
   earliest germanici {454,500,650,800} e greci {400,500,793} si sovrappongono del tutto: i nomi
   greci hanno portatori celebri precoci (Theodore 400, George 500 bizantini). La precocità-di-
   notabile misura "ha avuto bearer famosi presto", non l'origine linguistica.

## Conclusione (completa l'arco dei tre tentativi di terzo dominio)
- vernacolo-LARGO: (ii) impreciso → falsi-TOP.
- vernacolo-PRECISO: preciso ma (iii) ridondante → nessun guadagno.
- Wikidata: (i) **genuinamente indipendente** ma (iii) **non-informativo sull'origine** → se
  scorato onestamente deve ASTENERSI (k ovunque); non aggiunge né errori né recall.

**Tesi consolidata, su dati reali:** perché l'accumulo-join alzi il recall, un dominio deve essere
simultaneamente (i) indipendente per provenienza, (ii) ad alta precisione, (iii) informativo
sull'origine. Ottenerli tutti e tre da fonti aperte e riproducibili è il vero collo di bottiglia
ingegneristico — non un dettaglio. Questo è il risultato onesto (anti-hype) del pilota: la
fattibilità del metodo è dimostrata; la scarsità di domini che soddisfano i-ii-iii insieme è il
limite reale, da attaccare col fix morfologia (root-cause) + ricerca di corpora primari fuori-DMNES.

Provenienza: query in wd_urls_light.json (riproducibili); diagnostica in questo file. Deterministico.
