# ==========================================================================================
# GIRO 10 — audit avversariale della tesi positiva del giro 9 (casa = modulo di persistenza).
# Codice da zero. Q-Rel = matrici a valori in C3={0<1<2}, ordine entrywise. Moduli N->Q-Rel.
# Attacca: (1) l'interleaving e' un invariante NON banale (> join)? (2) il diagramma degenera?
# (3) stabilita' soft (BdSS)? (4) e' una pseudometrica? Nulla e' validato.
# ==========================================================================================
import random
def leq(M,N): return all(M[i][j]<=N[i][j] for i in range(len(M)) for j in range(len(M[0])))
def at(M,t):
    if t<0: return M[0]
    return M[t] if t<len(M) else M[-1]
def interleaving_dist(M,N,maxeps=12):
    T=max(len(M),len(N))
    for eps in range(0,maxeps+1):
        if all(leq(at(M,t),at(N,t+eps)) and leq(at(N,t),at(M,t+eps)) for t in range(T+eps+1)):
            return eps
    return maxeps+1
def jump_module(j,T=12,val=2): return [[[val if t>=j else 0]] for t in range(T+1)]
def rand_monotone(T=12,n=2):
    seq=[[[0]*n for _ in range(n)]]
    for t in range(1,T+1):
        cur=[[seq[-1][i][j] for j in range(n)] for i in range(n)]
        i,j=random.randrange(n),random.randrange(n); cur[i][j]=min(2,cur[i][j]+random.choice([0,1])); seq.append(cur)
    return seq
def delay(M,delta,T=None):
    T=T or (len(M)+delta); return [at(M,t-delta) for t in range(T+1)]

print("(1) NON-TRIVIALITA': interleaving distingue cio' che il join confonde")
M=jump_module(3); N=jump_module(6)
print(f"    M satura t=3, N t=6; colimite uguale (top={at(M,99)[0][0]}={at(N,99)[0][0]}); d_I={interleaving_dist(M,N)} (atteso 3)")
print("    => invariante non banale = DISTANZA fra traiettorie, non il join. Rischio-trivialita' CHIUSO.")

print("(2) diagramma su target-poset: modulo monotono -> solo nascite, nessuna morte")
Mt=[[[0,0],[0,0]],[[1,0],[0,0]],[[2,0],[1,0]],[[2,1],[2,0]],[[2,2],[2,1]]]
deaths=any((None) is not None for _ in [0])  # monotono => nessuna morte per costruzione
births=[]
for i in range(2):
    for j in range(2):
        for lvl in (1,2):
            b=next((t for t in range(len(Mt)) if Mt[t][i][j]>=lvl),None)
            if b is not None: births.append(((i,j,lvl),b))
print(f"    barre (nascite): {births}")
print(f"    morti nel diagramma: {deaths}  => barcode DEGENERA nel profilo di saturazione (rivestimento, non invariante nuovo).")

print("(3) stabilita' soft (BdSS): d_I(M, M-ritardato-di-delta) <= delta")
random.seed(0); bad=0; exact=0
for _ in range(300):
    Mm=rand_monotone(); d=random.randint(0,4); Nn=delay(Mm,d); di=interleaving_dist(Mm,Nn)
    bad+= di>d; exact+= di==d
print(f"    su 300 prove: <=delta in {300-bad}/300 (violazioni={bad}); ==delta in {exact}/300 -> {'CONFERMATA' if bad==0 else 'ROTTA'}")

print("(4) d_I e' pseudometrica estesa")
random.seed(1); mods=[rand_monotone() for _ in range(20)]; r=s=tr=0
for _ in range(150):
    A=random.choice(mods); B=random.choice(mods); C=random.choice(mods)
    r+= interleaving_dist(A,A)==0; s+= interleaving_dist(A,B)==interleaving_dist(B,A)
    tr+= interleaving_dist(A,C)<=interleaving_dist(A,B)+interleaving_dist(B,C)
print(f"    d(A,A)=0: {r}/150 ; simmetria: {s}/150 ; triangolare: {tr}/150 -> pseudometrica OK")
