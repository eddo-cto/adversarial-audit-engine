# ==========================================================================================
# AUDIT INDIPENDENTE (giro 8) della NOTA del settimo giro. Codice da zero.
# Attacca: (A) T1/T2/T3 riconferma; (B) ostruzione di transitivita' [decisiva, principiata];
# (C) riproduzione indipendente della falsificazione statistica di T2* + critica di potenza;
# (D) invariante diacronico; (E) matematica adeguata (home = Q-Rel, non Dist(Q)).
# ==========================================================================================
import itertools, random, statistics

# ---- C3 quantale (da zero) : 0=bot,1=k(unit),2=top
V=[0,1,2]
def amp(a,b):
    if a==0 or b==0: return 0
    if a==1: return b
    if b==1: return a
    return 2
def res(a,b): return max([c for c in V if amp(a,c)<=b], default=0)
assert all(amp(1,q)==q for q in V) and all(amp(0,q)==0 for q in V)
assert all(amp(a,b)==amp(b,a) for a in V for b in V)
assert all(amp(amp(a,b),c)==amp(a,amp(b,c)) for a in V for b in V for c in V)

print("="*80); print("(A) RICONFERMA INDIPENDENTE T1/T2/T3"); print("="*80)
# T1 pointwise: partial-homom vs two-sided vs chain
P,N,U='+','-','?'; sim={P:1,N:0,U:0}; dis={P:0,N:1,U:0}; chain={N:0,U:1,P:2}
ph =lambda a,b:(a!=P or b==P) and (a!=N or b==N)
two=lambda a,b:(sim[a]<=sim[b]) and (dis[a]<=dis[b])
ch =lambda a,b:(chain[a]<=chain[b])
d_two=sum(ph(a,b)!=two(a,b) for a in [P,N,U] for b in [P,N,U])
d_ch =sum(ph(a,b)!=ch(a,b) for a in [P,N,U] for b in [P,N,U])
print(f"T1 two-sided discordanze={d_two} (atteso 0) ; catena discordanze={d_ch} (atteso 3) -> {'OK' if d_two==0 and d_ch==3 else 'DIVERGE'}")
# T2/T3 su 2 oggetti
def is_cat(M,n):
    if any(M[i][i]<1 for i in range(n)): return False
    return all(amp(M[i][k],M[k][j])<=M[i][j] for i in range(n) for k in range(n) for j in range(n))
def is_dist(P_,A,B,n):
    L=all(amp(B[bp][b],P_[b][a])<=P_[bp][a] for a in range(n) for b in range(n) for bp in range(n))
    R=all(amp(P_[b][a],A[a][ap])<=P_[b][ap] for a in range(n) for ap in range(n) for b in range(n))
    return L and R
A=[[1,2],[0,1]]; B=[[1,2],[0,1]]
assert is_cat(A,2) and is_cat(B,2)
alld=[P_ for P_ in [[[v[0],v[1]],[v[2],v[3]]] for v in itertools.product(V,repeat=4)] if is_dist(P_,A,B,2)]
asy=[P_ for P_ in alld if P_[0][1]!=P_[1][0]]
print(f"T2 distributori validi={len(alld)}, asimmetrici={len(asy)} (atteso 13/11) -> {'OK' if len(alld)==13 and len(asy)==11 else 'DIVERGE'}")
supclosed=all(is_dist([[max(x[i][j],y[i][j]) for j in range(2)] for i in range(2)],A,B,2) for x in alld for y in alld)
print(f"T3 sup di distributori chiuso: {supclosed} -> {'OK' if supclosed else 'DIVERGE'}")

print(); print("="*80); print("(B) OSTRUZIONE DI TRANSITIVITA' [DECISIVA]"); print("="*80)
# La legge di composizione di C3-categoria  A(i,k)&A(k,j) <= A(i,j)  E' la transitivita'.
# Una similarita' NON transitiva NON puo' essere una C3-categoria => cade il lato OGGETTI (T1d).
# Esempio Tversky: sim(a,b)=top, sim(b,c)=top, sim(a,c)=bot ; diagonale top.
S=[[2,2,0],[2,2,2],[0,2,2]]
viol=[(i,k,j) for i in range(3) for k in range(3) for j in range(3) if amp(S[i][k],S[k][j])>S[i][j]]
print(f"Similarita' non-transitiva (a~b,b~c ma a≁c): e' C3-categoria? {is_cat(S,3)}  (violazioni composizione: {len(viol)})")
print(f"  es. violazione (i,k,j)={viol[0]}: A(i,k)&A(k,j)={amp(S[viol[0][0]][viol[0][1]],S[viol[0][1]][viol[0][2]])} > A(i,j)={S[viol[0][0]][viol[0][2]]}")
# quanto e' generico: su TUTTE le similarita' simmetriche riflessive (diag=top) a 3 oggetti in C3
cnt=0; transit=0
for u in itertools.product(V,repeat=3):  # (ab,ac,bc)
    M=[[2,u[0],u[1]],[u[0],2,u[2]],[u[1],u[2],2]]
    cnt+=1; transit+= is_cat(M,3)
print(f"  su {cnt} similarita' simmetriche riflessive in C3: transitive (=C3-cat) = {transit} ({100*transit//cnt}%)")
print("  => la maggioranza delle similarita' NON e' una C3-categoria. Il lato OGGETTI (T1d, assunto")
print("     nell'articolo) FALLISCE per similarita' reali non-transitive. Ostruzione PRINCIPIATA, non statistica.")

print(); print("="*80); print("(C) RIPRODUZIONE INDIPENDENTE DELLA FALSIFICAZIONE STATISTICA DI T2*"); print("="*80)
# Isbell double-closure su C3: dalla matrice-peso W verso il distributore piu' vicino.
def isbell(W,A,B,n,iters=20):
    Pm=[row[:] for row in W]
    for _ in range(iters):
        up=[[min(res(B[b][bp],Pm[bp][a]) for bp in range(n)) for a in range(n)] for b in range(n)]
        lo=[[min(res(A[ap][a],up[b][ap]) for ap in range(n)) for a in range(n)] for b in range(n)]
        if lo==Pm: break
        Pm=lo
    return Pm
def nontriv(P_): return any(x>0 for r in P_ for x in r)
def asym3(P_,n): return any(P_[b][a]!=P_[a][b] for a in range(n) for b in range(n) if a!=b)
def valid_asym_cats(n=3,limit=120):
    out=[]; offpos=[(i,j) for i in range(n) for j in range(n) if i!=j]
    for diag in itertools.product([1,2],repeat=n):
        for off in itertools.product(V,repeat=len(offpos)):
            M=[[0]*n for _ in range(n)]
            for i in range(n): M[i][i]=diag[i]
            for idx,(i,j) in enumerate(offpos): M[i][j]=off[idx]
            if is_cat(M,n) and any(M[i][j]!=M[j][i] for i in range(n) for j in range(n) if i<j):
                out.append(M)
                if len(out)>=limit: return out
    return out
cats=valid_asym_cats(3,120)
def quant(x): return 2 if x>=0.80 else (1 if x>=0.40 else 0)
fwd=[0.31,0.55,0.88,0.62,0.20,0.91,0.44]; bwd=[0.33,0.55,0.84,0.60,0.20,0.93,0.46]
def ruler_W():
    idx=0; W=[[0]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            if i==j: W[i][j]=1
            elif i<j: W[i][j]=quant(fwd[idx%len(fwd)]); idx+=1
            else: W[i][j]=quant(bwd[idx%len(bwd)]); idx+=1
    return W
def success_rate(Wfun, trials, cats, seed):
    random.seed(seed); ok=0; tot=0
    for _ in range(trials):
        A=random.choice(cats); B=random.choice(cats); W=Wfun()
        P_=isbell(W,A,B,3)
        tot+=1; ok+= (is_dist(P_,A,B,3) and nontriv(P_) and asym3(P_,3))
    return ok/tot
r_ruler=success_rate(ruler_W, 1500, cats, 1)
def rand_W(): return [[1 if i==j else random.choice(V) for j in range(3)] for i in range(3)]
r_rand=success_rate(rand_W, 1500, cats, 2)
print(f"C3: tasso di 'distributore valido asimmetrico nontriviale' via Isbell-closure")
print(f"   dati righello W = {100*r_ruler:.1f}%   vs   controllo casuale = {100*r_rand:.1f}%")
print(f"   rapporto dati/caso = {r_ruler/max(r_rand,1e-9):.2f}  ->", 
      "INDISTINGUIBILE (adeguatezza vacua): conferma la nota" if abs(r_ruler-r_rand)<0.03 else "SEPARA (contesta la nota)")

print(); print("="*80); print("(D) INVARIANTE DIACRONICO vs STATICO"); print("="*80)
# accumulo per supremo su linee (quantizzato). Invariante = punto di plateau (saturazione).
overlaps=[0.31,0.55,0.88,0.62,0.20,0.91,0.44]
acc=[]; cur=0
for o in overlaps: cur=max(cur,quant(o)); acc.append(cur)
sat=next((i+1 for i in range(len(acc)) if acc[i]==2), None)
print(f"accumulo ⋁ = {acc} ; monotono={all(acc[i]<=acc[i+1] for i in range(len(acc)-1))} ; saturazione a linea {sat}/{len(acc)}")
print("  la nota afferma: nessun modello STATICO separa dai dati casuali; solo il diacronico regge.")
print("  concordo sul principio (l'invariante robusto e' il PROFILO di saturazione), MA vedi (F) sui limiti.")

print(); print("="*80); print("(E) MATEMATICA ADEGUATA: home = Q-Rel (matrici), non Dist(Q)"); print("="*80)
# Q-Rel(B,A) = tutte le matrici B x A a valori in C3, sup-reticolo sotto join elementwise.
# join di due Q-relazioni e' una Q-relazione (banale ma fondante). I distributori sono il
# sub-reticolo chiuso (punti fissi di Isbell). Verifica: join chiuso in Q-Rel; e i distributori
# NON sono chiusi sotto tutte le operazioni che servono all'accumulo se i dati non sono transitivi.
def join_rel(X,Y,n): return [[max(X[i][j],Y[i][j]) for j in range(n)] for i in range(n)]
# join di matrici arbitrarie e' sempre una matrice (Q-Rel chiuso): banalmente vero.
print("Q-Rel: join di matrici e' una matrice -> sup-reticolo completo. (chiusura banale, fondante)")
# Il join di due DISTRIBUTORI resta distributore (T3a) — gia' verificato. Ma il join di due
# Q-relazioni NON-distributori resta una Q-relazione utile all'accumulo, senza pretendere transitivita'.
# Demotion (Freno): su base DISCRETA (A=B=identita'), OGNI matrice e' un distributore =>
# l'apparato categoriale non aggiunge nulla oltre il sup-reticolo.
Adisc=[[1 if i==j else 0 for j in range(3)] for i in range(3)]
allmat_are_dist=all(is_dist(W,Adisc,Adisc,3) for W in [[[random.choice(V) for _ in range(3)] for _ in range(3)] for _ in range(50)])
print(f"su base discreta ogni matrice e' distributore: {allmat_are_dist} -> il 'weighted colimit' si riduce al JOIN.")
print("  Conseguenza (Freno): la casa adeguata e' l'umile sup-reticolo delle Q-relazioni + il profilo")
print("  di saturazione; il distributore statico e' una fetta chiusa, generi camente inadeguata (ostruzione B).")
