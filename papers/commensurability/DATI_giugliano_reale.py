# =============================================================================
# ESEMPIO REALE — pilota Giugliano (NA), RGE 323/2024, CTU Arch. Passaro.
# Fonte: PILOTA_round_Giugliano_esito.md (run del motore END-TO-END su perizia reale).
# Dominio DIVERSO dalla genesi della teoria (edilizia, non il righello semantico) => niente circolarita'.
#
# MAPPATURA TRASPARENTE (verificabile riga per riga contro il file sorgente):
#  - SOPRAVVISSUTO/aspetti = i determinanti VERI del caso, dal ground-truth del CTU (umano, esterno).
#  - LINEE = i core indipendenti del motore, negli STADI reali documentati (round a 3 core -> +condominio).
#  - punteggio[0,1] = grado di CONVERGENZA documentata di quel core col ground-truth su quell'aspetto:
#       "centro pieno / coglie la trappola"      -> 0.90 (TOP)
#       "astensione onesta / piu' conservativo"  -> 0.50 (k)   [il motore NON conclude come il CTU]
#       "non tratta / escape / non attiva"       -> 0.10 (BOT)
#  I valori NON sono voti LLM: codificano la tabella "Esito per core (vs ground-truth)" del sorgente.
# =============================================================================

# --- SOGLIE (dichiarate a priori, PRIMA di guardare l'accumulo) ---
SOGLIA_TOP = 0.70
SOGLIA_K   = 0.35

SOPRAVVISSUTO = "CTU Giugliano RGE 323/2024 (Passaro): determinanti reali del caso"
# I 4 determinanti veri (dal ground-truth del CTU):
ASPETTI = ["catasto/planimetria (art.29 nullita')", "sanabilita' (via art.36)",
           "agibilita'/SCA", "condominiale / parti comuni"]

# --- LINEE = core indipendenti, in ordine di STADIO reale (3-core round, poi +condominio) ---
LENTI = [
    # stadio 1 — round a 3 core
    {"nome": "core cross catasto-edilizio", "punteggi": [0.90, 0.10, 0.10, 0.10]},  # "centro pieno" su A1
    {"nome": "core sanabilita'",            "punteggi": [0.10, 0.50, 0.10, 0.10]},  # "astensione onesta" su A2 (k)
    {"nome": "core catena agibilita'",      "punteggi": [0.10, 0.10, 0.90, 0.10]},  # coglie il determinante OMESSO dal CTU (A3)
    # stadio 2 — ri-esecuzione a 4 core (gap condominio chiuso)
    {"nome": "core condominio (aggiunto)",  "punteggi": [0.10, 0.10, 0.10, 0.90]},  # "gap chiuso: blocco" su A4; precision: interni non attivano
]

# secondo sopravvissuto: non fornito (aspetti non allineati con altri lotti -> forzarlo sarebbe un artefatto).
SOPRAVVISSUTO_2 = None
ASPETTI_2 = None
LENTI_2 = None
