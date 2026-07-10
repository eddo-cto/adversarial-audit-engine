# Sintesi trans-dominio — la domain-independence come regolarità empirica (3 bracci)
2026-07-08. Tre ledger di affidabilità, scienze massimamente diverse, dati aperti e riproducibili.

## Cosa RICORRE (struttura invariante) — il contributo
In fisica (esopianeti KOI), genetica clinica (ClinVar/ACMG) e cybersecurity (NVD/CVE) ricorre la
STESSA struttura di come si costruisce affidabilità SENZA una verità unica:
- verdetto GRADUATO con quantale C3-like {⊥ < k < ⊤};
- una classe d'ASTENSIONE esplicita (CANDIDATE / Uncertain-significance-VUS / Deferred-Awaiting);
- un PAVIMENTO / classe di rifiuto (FALSE POSITIVE / refuted / Rejected);
- CANALI INDIPENDENTI accumulati (metodi/flag di transito; sottomettitori; scorer NVD vs CNA);
- il DISACCORDO tra canali indipendenti è registrato ed è misurabile.
Che il pattern emerga in sistemi progettati indipendentemente (uno umano-normativo come ACMG, uno
strumentale come Kepler, uno ingegneristico come NVD) è il punto: non è artefatto di un dominio.

## Cosa VARIA (domain-dependent) — la rifinitura onesta
Il TASSO DI CONVERGENZA dei canali indipendenti è specifico del dominio:
| dominio | disaccordo tra canali indipendenti | note |
|---|---|---|
| esopianeti (fisica) | quasi-concordanza sulla classe positiva; 7 casi-riscatto | canale indip. selettivo (RV) |
| ClinVar (genetica) | 19,8% (≥2 sottomettitori) | non selezionato, tutta la popolazione |
| NVD (cybersecurity) | 55,8% (n=43, doppio scorer) | + caveat cross-versione CVSS |

## Verdetto (postura del progetto)
La domain-independence della STRUTTURA regge su tre domini reali; la CONVERGENZA no — ed è un
risultato, non un fallimento: delimita dove l'affidabilità-per-accumulo satura in fretta e dove
resta contesa. Nessun braccio è "validato" internamente: consegna all'occhio esterno.
Residui dichiarati: n modesto in NVD; cross-versione CVSS; incrocio review_status×verdetto in ClinVar
richiede bulk; anti-tautologia esopianeti (peso sui 7 casi). Tutti aperti e riproducibili.
