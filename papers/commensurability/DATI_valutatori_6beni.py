# =============================================================================
# ESEMPIO REALE B — commensurabilità di DUE linee indipendenti (valutatori grounded)
# su 6 beni reali / 6 territori. Fonte: ROUND_multibene_galassia.md (galassia su perizie reali).
# Lente DIVERSA da quella dell'esempio A (valutazione, non compliance) => robustezza multi-lente.
#
# La commensurabilità delle DUE linee indipendenti (Valutatore A ancorato OMI vs
# Valutatore B ancorato comparabili) è codificata TRASPARENTEMENTE dal documento:
#   TOP = le due bande SI SOVRAPPONGONO (banda comune) -> commensurabili
#   k   = divergono SENZA sovrapporsi -> non-chiusura dichiarata ("non mediare")
#   BOT = l'oracolo standard NON si applica -> ENTRAMBI si astengono (non-conoscenza dichiarata)
# I valori NON sono voti: codificano la tabella "Motore 2 — esiti/astensione" del sorgente.
# =============================================================================
BOT, K, TOP = 0, 1, 2
BENI = [
    # (bene, territorio, divergenza documentata, esito, valore C3, nota dal sorgente)
    ("Albano Laziale (RM) negozio C1", "Lazio",     "15%", "banda comune 507k–561k",            TOP, "convergono"),
    ("Modica (RG) appartamenti A/2",   "Sicilia",   "11%", "banda 225k–267k",                   TOP, "convergono (con flag grounding sui comparabili)"),
    ("Lumezzane (BS) laboratorio C/3", "Lombardia", "9%",  "banda 70k–89k",                     TOP, "convergono"),
    ("Giugliano (NA) abitativo A/4",   "Campania",  "37%", "range NON si sovrappongono",        K,   "divergenza materiale -> non-chiusura: 'non mediare'"),
    ("Stazzema (LU) terreno/bosco",    "Toscana",   "n/a", "oracolo OMI non pertinente",        BOT, "astensione: rinvio a VAM/comparabili agricoli"),
    ("San Felice/Maranello (MO) area", "Emilia",    "n/a", "valore di trasformazione, non OMI", BOT, "astensione: rinvio a valore di trasformazione"),
]
