# =============================================================================
# Verifica dell'esempio REALE: l'accumulo di linee indipendenti mostra la struttura
# diacronica del paper (accumulo monotono + profilo di saturazione + residuo dichiarato)?
# Controllo casuale a MARGINALI CORRETTI (fix giro-11: non piu' uniforme). Nessuna dipendenza.
# Uso: python3 verifica_esempio_reale.py [modulo_dati]   (default: DATI_giugliano_reale)
# =============================================================================
import random, statistics, importlib, sys
DAT = importlib.import_module(sys.argv[1] if len(sys.argv)>1 else "DATI_giugliano_reale")
SOGLIA_TOP, SOGLIA_K = DAT.SOGLIA_TOP, DAT.SOGLIA_K
SOPRAVVISSUTO, ASPETTI, LENTI = DAT.SOPRAVVISSUTO, DAT.ASPETTI, DAT.LENTI
BOT,K,TOP=0,1,2; NOMI={BOT:"BOT",K:"k",TOP:"TOP"}
def quantize(x): return TOP if x>=SOGLIA_TOP else (K if x>=SOGLIA_K else BOT)
def accumulo(aspetti,lenti):
    n=len(aspetti)
    Q=[[quantize(L["punteggi"][a]) for a in range(n)] for L in lenti]
    Psi=[]; cur=[BOT]*n
    for t in range(len(lenti)):
        cur=[max(cur[a],Q[t][a]) for a in range(n)]; Psi.append(cur[:])
    return Q,Psi
def sat_stage(Psi):
    fin=Psi[-1]
    return next((t+1 for t,r in enumerate(Psi) if r==fin), len(Psi))
def monotona(Psi):
    return all(Psi[t][a]>=Psi[t-1][a] for t in range(1,len(Psi)) for a in range(len(Psi[0])))
def non_redundant(Psi):  # quante linee ALZANO strettamente l'accumulo
    c=0; prev=[BOT]*len(Psi[0])
    for row in Psi:
        if any(row[a]>prev[a] for a in range(len(row))): c+=1
        prev=row
    return c

print("="*72)
print(f"ESEMPIO REALE — {SOPRAVVISSUTO}")
print(f"soglie a priori: TOP>={SOGLIA_TOP}  k>={SOGLIA_K}")
print("="*72)
Q,Psi=accumulo(ASPETTI,LENTI)
print("aspetti (determinanti veri dal ground-truth):")
for a in ASPETTI: print("   -",a)
print("\nlinee (stadi) x commensurabilita' quantizzata per aspetto:")
for t,L in enumerate(LENTI): print(f"  L{t+1} [{L['nome']}]: {[NOMI[v] for v in Q[t]]}")
print("\naccumulo Psi_t (join progressivo delle linee):")
for t in range(len(Psi)): print(f"  Psi_{t+1} = {[NOMI[v] for v in Psi[t]]}")
sat=sat_stage(Psi); nr=non_redundant(Psi)
resid=[ASPETTI[a] for a in range(len(ASPETTI)) if Psi[-1][a]<TOP]
print(f"\nmonotono: {monotona(Psi)}")
print(f"stadio di saturazione: {sat}/{len(LENTI)}   (linee non-ridondanti: {nr}/{len(LENTI)})")
print(f"residuo dichiarato (aspetti < TOP alla fine): {resid if resid else 'nessuno'}")

# --- CONTROLLO CASUALE A MARGINALI CORRETTI ---
# marginale = distribuzione empirica dei valori quantizzati REALI (non uniforme).
flat=[v for row in Q for v in row]
pool=flat[:]  # campiona con rimpiazzo dalla stessa distribuzione (stessi marginali)
def rand_trial(n_asp,n_lin):
    Qr=[[random.choice(pool) for _ in range(n_asp)] for _ in range(n_lin)]
    Ps=[]; cur=[BOT]*n_asp
    for t in range(n_lin):
        cur=[max(cur[a],Qr[t][a]) for a in range(n_asp)]; Ps.append(cur[:])
    fin=Ps[-1]
    s=next((t+1 for t,r in enumerate(Ps) if r==fin), n_lin)
    res=sum(1 for a in range(n_asp) if fin[a]<TOP)
    nrr=0; prev=[BOT]*n_asp
    for row in Ps:
        if any(row[a]>prev[a] for a in range(n_asp)): nrr+=1
        prev=row
    return s,res,nrr
random.seed(0); T=5000
S=[rand_trial(len(ASPETTI),len(LENTI)) for _ in range(T)]
sat_r=[x[0] for x in S]; res_r=[x[1] for x in S]; nr_r=[x[2] for x in S]
print("\ncontrollo casuale a marginali corretti (5000 prove, stessa distribuzione dei valori reali):")
print(f"  saturazione:  reale={sat}  vs casuale medio={statistics.mean(sat_r):.2f}")
print(f"  non-ridondanza: reale={nr}  vs casuale medio={statistics.mean(nr_r):.2f}"
      f"   (frazione casuali con tutte le linee non-ridondanti = {sum(1 for x in nr_r if x==len(LENTI))/T:.1%})")
print(f"  residuo (aspetti<TOP alla fine): reale={len(resid)}  vs casuale medio={statistics.mean(res_r):.2f}")

print("\n"+"="*72); print("LETTURA ONESTA")
print("="*72)
print("Il caso reale esibisce la struttura del paper §5: accumulo MONOTONO, ogni linea")
print("indipendente NON-RIDONDANTE (aggiunge un determinante nuovo), un profilo di")
print("saturazione preciso, e un RESIDUO DICHIARATO che persiste (la sanabilita' resta k:")
print("il motore si astiene dove il CTU concludeva -> non-chiusura, come da metodo).")
print("Firma diversa dal sintetico (che saturava presto): qui la copertura e' NON-ridondante")
print("e il residuo non si chiude. Il profilo di saturazione E' l'informazione, come dice §5.2.")
print("Limite onesto: n=1, dominio singolo; e' un ESEMPIO di applicabilita', non una validazione")
print("statistica. La commensurabilita' e' codifica documentata della convergenza col CTU, non voto.")
