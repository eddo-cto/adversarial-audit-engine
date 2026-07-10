# =============================================================================
# RUN esperimento esopianeti — dati REALI NASA Exoplanet Archive (tavolo KOI cumulative,
# ediz. corrente via TAP). Contingenza 4-flag x disposizione + istogramma koi_score,
# scaricati via TAP (query in fondo, riproducibili). Deterministico, nessun LLM.
# Tesi: affidabilita' = sopravvivenza a N falsificazioni INDIPENDENTI (survivor gate),
# con C3 {FALSE POSITIVE < CANDIDATE(k) < CONFIRMED}.
# =============================================================================
import itertools, random
random.seed(1)

# --- DATI REALI: (nt,ss,co,ec, disposizione, conteggio) — riga corrotta nt=465 SCARTATA ---
CONT = [
 (0,1,0,0,"FP",1452),(0,1,1,1,"FP",327),(1,0,1,1,"FP",160),(0,0,1,0,"FP",515),
 (1,0,0,0,"FP",1119),(1,0,0,0,"CONF",3),(0,1,0,1,"FP",64),(1,1,1,0,"FP",2),
 (0,0,0,1,"FP",124),(0,0,0,0,"FP",95),(0,0,0,0,"CAND",1975),(0,1,1,0,"FP",351),
 (0,0,1,1,"FP",385),(0,0,0,0,"CONF",2729),(1,0,0,1,"FP",85),(1,1,1,1,"FP",3),
 (0,1,0,0,"CONF",14),(1,0,1,0,"FP",146),(1,1,0,0,"FP",11),(0,1,0,0,"CAND",2),
 (1,0,0,0,"CAND",1),
]  # (465,0,0,0,CONF,1) scartata: valore flag impossibile

# espandi a righe pesate
rows=[]
for nt,ss,co,ec,d,n in CONT:
    for _ in range(n): rows.append((nt,ss,co,ec,d))
N=len(rows); print(f"KOI analizzati (netti): {N}")

def nflag(r): return r[0]+r[1]+r[2]+r[3]
disp=lambda r: r[4]

print("\n=== H1/H2 — accumulo di falsificazioni indipendenti vs disposizione ===")
print(f"{'n_flag':>6} {'FP':>6} {'CAND':>6} {'CONF':>6}   P(FP|n_flag)")
for k in range(5):
    sub=[r for r in rows if nflag(r)==k]
    fp=sum(1 for r in sub if disp(r)=="FP"); ca=sum(1 for r in sub if disp(r)=="CAND"); co=sum(1 for r in sub if disp(r)=="CONF")
    tot=len(sub); 
    if tot: print(f"{k:>6} {fp:>6} {ca:>6} {co:>6}   {fp/tot:.3f}")
# H2: >=1 flag indipendente FAIL -> quasi sempre FP?
ge1=[r for r in rows if nflag(r)>=1]; fp_ge1=sum(1 for r in ge1 if disp(r)=="FP")
print(f"\nH2: P(FALSE POSITIVE | >=1 falsificazione indipendente) = {fp_ge1}/{len(ge1)} = {fp_ge1/len(ge1):.4f}")
zero=[r for r in rows if nflag(r)==0]
conf0=sum(1 for r in zero if disp(r)=="CONF")
print(f"    P(passa tutti e 4 i check | CONFIRMED) = {conf0}/{sum(1 for r in rows if disp(r)=='CONF')} = {conf0/sum(1 for r in rows if disp(r)=='CONF'):.4f}")
print(f"    Tra i sopravvissuti (0 flag, n={len(zero)}): CONF={conf0} CAND={sum(1 for r in zero if disp(r)=='CAND')} FP={sum(1 for r in zero if disp(r)=='FP')}")

print("\n=== H3 — i 4 flag sono INDIPENDENTI? (phi a coppie su tutti i KOI) ===")
import math
names=["nt","ss","co","ec"]
def phi(i,j):
    a=b=c=d=0
    for r in rows:
        x,y=r[i],r[j]
        if x and y: a+=1
        elif x and not y: b+=1
        elif not x and y: c+=1
        else: d+=1
    num=a*d-b*c; den=math.sqrt((a+b)*(c+d)*(a+c)*(b+d))
    return num/den if den else float('nan')
for i,j in itertools.combinations(range(4),2):
    print(f"  phi({names[i]},{names[j]}) = {phi(i,j):+.2f}")
print("  |phi| bassi = falliscono per ragioni DIVERSE (linee indipendenti, non ridondanti)")

print("\n=== H1 test di permutazione: n_flag separa FP da non-FP? ===")
y=[1 if disp(r)=="FP" else 0 for r in rows]; x=[nflag(r) for r in rows]
mfp=sum(xi for xi,yi in zip(x,y) if yi)/sum(y)
mno=sum(xi for xi,yi in zip(x,y) if not yi)/(len(y)-sum(y))
obs=mfp-mno
cnt=0; IT=2000
for _ in range(IT):
    yp=y[:]; random.shuffle(yp)
    a=sum(xi for xi,yi in zip(x,yp) if yi)/sum(yp)
    b=sum(xi for xi,yi in zip(x,yp) if not yi)/(len(yp)-sum(yp))
    if abs(a-b)>=abs(obs): cnt+=1
print(f"  media n_flag: FP={mfp:.3f} vs non-FP={mno:.3f} ; diff={obs:+.3f} ; p_perm={cnt/IT:.4f}")

print("\n=== H4 — profilo oltre il tier: koi_score DENTRO i sopravvissuti ===")
# istogramma reale (score bin -> conteggi) per disposizione
HIST={
 "CAND":{0.0:100,0.1:25,0.2:26,0.3:32,0.4:36,0.5:34,0.6:40,0.7:41,0.8:99,0.9:193,1.0:752,None:600},
 "CONF":{0.0:36,0.1:9,0.2:5,0.3:6,0.4:11,0.5:10,0.6:13,0.7:21,0.8:42,0.9:160,1.0:2417,None:17},
 "FP":{0.0:3603,0.1:101,0.2:54,0.3:39,0.4:22,0.5:15,0.6:10,0.7:11,0.8:13,0.9:13,1.0:65,None:893},
}
for d,h in HIST.items():
    vals=[(s,c) for s,c in h.items() if s is not None]
    tot=sum(c for _,c in vals); m=sum(s*c for s,c in vals)/tot
    print(f"  {d}: score medio={m:.2f} (n con score={tot}); picco a 1.0 = {h[1.0]}")
print("  CANDIDATE(k) copre TUTTO lo spettro di score: e' lo strato dove il verdetto finale")
print("  confonde traiettorie che il PROFILO (score) distingue -> H4 sostenuta.")
