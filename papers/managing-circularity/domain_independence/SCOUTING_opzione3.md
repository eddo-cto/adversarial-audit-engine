# Opzione 3 — verso il contributo forte: DOMAIN-INDEPENDENCE come regolarità empirica
Scouting 2026-07-08. Tutto autorizzato. Deterministico dove misura.

## Riformulazione (il potenziale grosso)
Il contributo non è "un testbed migliore degli esopianeti". È mostrare che **la stessa struttura**
— accumulo di domini INDIPENDENTI → affidabilità graduata (C3 {⊥<k<⊤}), con PAVIMENTO (una
falsificazione indipendente abbatte) e tier d'ASTENSIONE — **ricorre in scienze massimamente
diverse**. Questo *è* l'asse "domain-independence" che il paper rivendica: non un aneddoto, ma una
regolarità trans-dominio di come sistemi maturi costruiscono affidabilità SENZA una verità unica.

- Braccio 1 (fisica): esopianeti KOI. Fatto, ribilanciato dal revisore (peso sui 7 casi-riscatto).
  Limite intrinseco emerso: il canale indipendente per-strumento (RV) è selettivo ⇒ niente potere
  discriminante pieno sulla classe negativa.
- **Braccio 2 (genetica clinica): ClinVar / ACMG.** Sistema progettato dall'uomo che accumula linee
  di evidenza da SOTTOMETTITORI INDIPENDENTI in un verdetto graduato:
  Benign < VUS(=k) < Pathogenic, con **"Conflicting classifications" = disaccordo tra canali
  indipendenti REGISTRATO su tutta la popolazione multi-sottomessa** (fattibilità: 196.224 varianti
  conflicting, verificate via NCBI eutils). Più: **review status (gold stars) = n. canali concordi**,
  e movimento diacronico VUS→(likely)pathogenic all'accumularsi dell'evidenza.

## Perché ClinVar risolve ciò che gli esopianeti non potevano (R1)
La proprietà mancante era "canali indipendenti + disaccordo misurabile su TUTTA la popolazione, non
solo sui positivi selezionati". In ClinVar i sottomettitori indipendenti classificano le stesse
varianti e il DISACCORDO è una classe esplicita ("Conflicting") su ogni variante multi-sottomessa →
potere discriminante misurabile su entrambe le classi. Non c'è il bias di follow-up degli esopianeti.

## Fattibilità (verificata)
- ClinVar aperto, alto N, fetchabile (eutils via browser; per il lavoro vero: `variant_summary.txt`
  / VCF con campi germline_classification + review_status + numero sottomettitori).
- Endpoint NCBI eutils risponde in JSON strutturato. Nessun voto LLM nello scoring.

## Riga rossa (dichiarata)
Analisi SOLO della STRUTTURA della tassonomia di affidabilità (come l'evidenza indipendente si
accumula in tier), MAI interpretazione clinica di varianti per una persona. Aggregato/metodologico.

## Piano proposto (specchio del braccio esopianeti, disciplina di pre-registrazione)
1. Pre-registrare il disegno ClinVar (unità = variante; C3 = benign/VUS/pathogenic; canali = review
   status + n. sottomettitori concordi; disaccordo = conflicting; asse diacronico = reclassificazione).
2. Tirare i dati veri da `variant_summary` (campi classificazione, review_status, #submitters).
3. Analisi deterministica: accumulo di sottomettitori concordi → tier (H1); disaccordo (conflicting)
   vs concordanza per numero di canali (potere discriminante, la parte che mancava); VUS come k;
   reclassificazione diacronica se le date sono disponibili (profilo).
4. Terzo braccio opzionale (metrologia CODATA o GRADE) per chiudere il triangolo trans-dominio.

## Aggiornamento fattibilità ClinVar (dati reali via eutils, campo [Review Status] verificato)
Ordinale d'accumulo di canali (sottomettitori) indipendenti — conteggi reali:
- criteria provided, single submitter (1★): 3.290.338
- criteria provided, multiple submitters, no conflicts (2★): 662.778
- criteria provided, CONFLICTING classifications (disaccordo): 163.647
- reviewed by expert panel (3★): 22.128
Faceting via eutils funziona (nessun file bulk necessario); incrocio review_status × clinical
significance via term combinati "[Review Status] AND [Clinical Significance]". Braccio 2 FATTIBILE.

## Piano a 3 bracci (stress test sul terzo, per volontà esplicita)
- Braccio 1 fisica: esopianeti KOI (fatto, ribilanciato).
- Braccio 2 genetica clinica: ClinVar/ACMG (fattibile, dati confermati). Solo struttura, mai clinica.
- Braccio 3 STRESS TEST — dominio massimamente diverso (non scienza naturale) per mettere alla prova
  la domain-independence: candidato primario CVE/NVD (cybersecurity: scorer indipendenti, tier
  "Disputed"/"Rejected"/"Awaiting", CVSS multipli; API JSON aperta). Se non regge (dati o struttura),
  si ripiega a 2 bracci e si documenta il fallimento come confine onesto.

## Arm-3 (NVD/CVE) — fattibilità CONFERMATA (2026-07-08)
API NVD 2.0 risponde in JSON: totalResults=364.005 CVE. Ogni record ha `vulnStatus`
(Received→Awaiting→Undergoing→Analyzed, +Modified/Rejected) = ordinale di maturazione del verdetto,
e `metrics` CVSS con `source`+`type` Primary/Secondary = scorer INDIPENDENTI (NVD vs CNA/vendor).
Disaccordo = dove Primary e Secondary divergono (severità/score). Endpoint aperto:
https://services.nvd.nist.gov/rest/json/cves/2.0 . Da costruire: distribuzione vulnStatus +
divergenza Primary/Secondary su un campione, come terzo braccio (stress test domain-independence).
