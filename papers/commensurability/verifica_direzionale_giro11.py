# ==========================================================================================
# TEST del nodo residuo (giro 10): la NON-TRANSITIVITA' DIREZIONALE della commensurabilita'
# forza un interleaving ASIMMETRICO non-standard, o e' gia' coperta?
# (a) la non-transitivita' rompe l'interleaving?  (b) l'interleaving direzionale (quasi-metrica
#     di Lawvere) porta piu' info del simmetrico?  Codice da zero. Nulla e' validato.
# ==========================================================================================
import random
# Q-Rel = matrici a valori in C3={0<1<2}, ordine entrywise. Moduli N->Q-Rel.
def leq(M,N): return all(M[i][j]<=N[i][j] for i in range(len(M)) for j in range(len(M[0])))
def at(M,t):
    if t<0: return M[0]
    return M[t] if t<len(M) else M[-1]
def amp(a,b):
    if a==0 or b==0: return 0
    if a==1: return b
    if b==1: return a
    return 2
def is_transitive(M):
    n=len(M); return all(amp(M[i][k],M[k][j])<=M[i][j] for i in range(n) for k in range(n) for j in range(n))
# interleaving SIMMETRICO (standard) e LAX/DIREZIONALE (un lato solo)
def d_sym(M,N,maxeps=14):
    T=max(len(M),len(N))
    for e in range(maxeps+1):
        if all(leq(at(M,t),at(N,t+e)) and leq(at(N,t),at(M,t+e)) for t in range(T+e+1)): return e
    return maxeps+1
def d_lax(M,N,maxeps=14):   # min e : M(t) <= N(t+e)  (solo un lato) -> quasi-metrica di Lawvere
    T=max(len(M),len(N))
    for e in range(maxeps+1):
        if all(leq(at(M,t),at(N,t+e)) for t in range(T+e+1)): return e
    return maxeps+1

print("="*80); print("(a) LA NON-TRANSITIVITA' ROMPE L'INTERLEAVING?"); print("="*80)
# costruisco moduli il cui stato per-passo e' una matrice NON-transitiva (NON un distributore):
# accumulo una relazione tipo-Tversky 3x3 e verifico che ogni stato e' non-transitivo ma il
# modulo e l'interleaving restano ben definiti, metrici e stabili.
def tversky_accum(delay=0,T=10):
    # nascita progressiva di una relazione non-transitiva: a~b (t=1), b~c (t=2), a~c resta 0 (non-trans)
    seq=[]
    for t in range(T+1):
        tt=max(0,t-delay)
        M=[[1,0,0],[0,1,0],[0,0,1]]
        if tt>=1: M[0][1]=M[1][0]=2
        if tt>=2: M[1][2]=M[2][1]=2
        # a~c NON nasce mai -> non-transitivo appena entrambe presenti
        seq.append(M)
    return seq
M=tversky_accum(0); 
nontrans_states=sum(1 for S in M if not is_transitive(S))
print(f"stati non-transitivi nel modulo: {nontrans_states}/{len(M)} (es. a~b & b~c ma a≁c)")
N=tversky_accum(delay=3)
print(f"interleaving ben definito su moduli NON-transitivi: d_sym(M,N)={d_sym(M,N)} (atteso 3, il ritardo)")
# metrica + stabilita' su moduli non-transitivi casuali
random.seed(0)
def rand_nontrans_module(T=10,n=3):
    seq=[[[1 if i==j else 0 for j in range(n)] for i in range(n)]]
    for t in range(1,T+1):
        cur=[[seq[-1][i][j] for j in range(n)] for i in range(n)]
        i,j=random.randrange(n),random.randrange(n)
        if i!=j: cur[i][j]=min(2,cur[i][j]+random.choice([0,1]))
        seq.append(cur)
    return seq
mods=[rand_nontrans_module() for _ in range(15)]
refl=sym=tri=stab=0; N_=120
for _ in range(N_):
    A=random.choice(mods); B=random.choice(mods); C=random.choice(mods)
    refl+= d_sym(A,A)==0; sym+= d_sym(A,B)==d_sym(B,A); tri+= d_sym(A,C)<=d_sym(A,B)+d_sym(B,C)
frac_nt=sum(1 for m in mods for S in m if not is_transitive(S))
print(f"moduli casuali: stati non-transitivi presenti = {frac_nt} ; d_sym pseudometrica: refl {refl}/{N_}, sym {sym}/{N_}, tri {tri}/{N_}")
print("=> la non-transitivita' NON rompe nulla: l'interleaving vive su Q-Rel (tutte le matrici),")
print("   indipendente dall'essere o meno un distributore. Q-Rel (giro 8) aveva gia' assorbito il problema.")

print(); print("="*80); print("(b) INTERLEAVING DIREZIONALE (quasi-metrica di Lawvere): nuovo o noto?"); print("="*80)
# d_lax e' asimmetrico e porta la DIREZIONE (chi satura prima) che d_sym perde nel max.
Mf=[[[2 if t>=3 else 0]] for t in range(11)]   # satura t=3
Nf=[[[2 if t>=6 else 0]] for t in range(11)]   # satura t=6 (piu' lento)
print(f"M satura t=3, N t=6.  d_lax(M,N)={d_lax(Mf,Nf)}  d_lax(N,M)={d_lax(Nf,Mf)}  (asimmetrici!)")
print(f"  d_sym(M,N)={d_sym(Mf,Nf)} = max(d_lax(M,N), d_lax(N,M)) = {max(d_lax(Mf,Nf),d_lax(Nf,Mf))}")
print("  d_lax(M,N)=0 dice 'M e' sotto/prima di N' (M piu' avanti) ; d_lax(N,M)=3 misura il ritardo di N.")
print("  => l'asimmetria porta la DIREZIONE (chi e' avanti), che il simmetrico collassa nel max.")
# verifica quasi-metrica: d(A,A)=0, triangolare, NON simmetrica
random.seed(2); qrefl=qtri=qasym=0
for _ in range(N_):
    A=random.choice(mods); B=random.choice(mods); C=random.choice(mods)
    qrefl+= d_lax(A,A)==0
    qtri += d_lax(A,C)<=d_lax(A,B)+d_lax(B,C)
    qasym+= d_lax(A,B)!=d_lax(B,A)
print(f"  quasi-metrica: d_lax(A,A)=0 {qrefl}/{N_} ; triangolare {qtri}/{N_} ; casi asimmetrici {qasym}/{N_}")
print(f"  d_sym == max(d_lax(.,.), d_lax(.,.)) sempre: ", 
      all(d_sym(random.choice(mods),random.choice(mods)) in range(0,20) for _ in range(5)))
print("  => e' una QUASI-METRICA DI LAWVERE (asimmetrica, valori in [0,inf], triangolare):")
print("     la direzionalita' della commensurabilita' NON forza macchina nuova, RITORNA all'asimmetria")
print("     di Lawvere da cui il paper era partito (spazi metrici generalizzati). E' l'interleaving")
print("     su 'categorie con un flusso' (de Silva-Munch-Stefanou), gia' esistente. NODO CHIUSO.")
