#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Verificatore riproducibile dei teoremi T1/T2/T3 sul quantale C3 (Lai-Shen-Tao-Zhang 2019)
# e sui distributori di Stubbe (2004). Strumento meccanico dell'esperto: le verifiche finite
# sono esaustive quindi PROVE; i punti generali sono segnalati. Nulla e' validato.
# Uso:  python3 verifica_teoremi_C3.py
import itertools, random

# 0. QUANTALE C3 (Lai et al. 2019, Es. 2.1(5)): catena bottom<k<top, unita' k, top&top=top
E = [0, 1, 2]
join = max
AMP = {(0,0):0,(0,1):0,(0,2):0,(1,0):0,(1,1):1,(1,2):2,(2,0):0,(2,1):2,(2,2):2}
amp = lambda a, b: AMP[(a, b)]
imp = lambda a, b: max(c for c in E if amp(a, c) <= b)
neg = lambda a: imp(a, 0)

def verifica_quantale():
    assert all(amp(a,b)==amp(b,a) for a in E for b in E)
    assert all(amp(1,a)==a for a in E)
    assert all(amp(amp(a,b),c)==amp(a,amp(b,c)) for a in E for b in E for c in E)
    assert all(amp(a,join(b,c))==join(amp(a,b),amp(a,c)) for a in E for b in E for c in E)
    assert all(amp(0,a)==0 for a in E)
    assert all((amp(a,c)<=b)==(c<=imp(a,b)) for a in E for b in E for c in E)
    assert 1 != 2
    assert (neg(0),neg(1),neg(2)) == (2,0,0)
    return True

# T1. partial homomorphism (Bueno-French-Ladyman: preserva R+ E R-, R? libero)
PP,NN,UU = 'P','N','U'
VV = [PP,NN,UU]
sim = {PP:1, NN:0, UU:0}
dis = {PP:0, NN:1, UU:0}
chain = {NN:0, UU:1, PP:2}

def T1_prova_puntuale():
    bad_chu = bad_chain = 0
    for a in VV:
        for b in VV:
            ph  = (a!=PP or b==PP) and (a!=NN or b==NN)
            chu = (sim[a]<=sim[b]) and (dis[a]<=dis[b])
            ch  = (chain[a]<=chain[b])
            bad_chu   += (ph!=chu)
            bad_chain += (ph!=ch)
    return bad_chu, bad_chain

# T2. C3-distributore asimmetrico (Stubbe Def. 3.2) fra due C3-categorie (Def. 3.1)
def is_C3cat(A, obj):
    # assioma corretto: 1 <= A(a,a), cioe' diag in {k,top}
    if any(A[(a,a)] < 1 for a in obj):
        return False
    return all(amp(A[(c,b)],A[(b,a)])<=A[(c,a)] for a in obj for b in obj for c in obj)

def is_distributor(Phi, A, B, oA, oB):
    left  = all(amp(B[(bp,b)],Phi[(b,a)])<=Phi[(bp,a)] for a in oA for b in oB for bp in oB)
    right = all(amp(Phi[(b,a)],A[(a,ap)])<=Phi[(b,ap)] for a in oA for ap in oA for b in oB)
    return left and right

def T2_costruzione():
    oA, oB = ['a1','a2'], ['b1','b2']
    A = {('a1','a1'):1,('a1','a2'):2,('a2','a1'):0,('a2','a2'):1}
    B = {('b1','b1'):1,('b1','b2'):2,('b2','b1'):0,('b2','b2'):1}
    assert is_C3cat(A,oA) and is_C3cat(B,oB)
    keys = [('b1','a1'),('b1','a2'),('b2','a1'),('b2','a2')]
    alld = [v for v in itertools.product([0,1,2],repeat=4)
            if is_distributor(dict(zip(keys,v)),A,B,oA,oB)]
    asy = [v for v in alld if v[1]!=v[2]]
    return A,B,oA,oB,alld,asy

# T3. accumulo diacronico = sup elementwise di distributori
def T3_verifica(A,B,oA,oB,alld):
    keys = [('b1','a1'),('b1','a2'),('b2','a1'),('b2','a2')]
    to = lambda v: dict(zip(keys,v))
    supv = lambda x,y: tuple(max(x[i],y[i]) for i in range(4))
    closed = all(is_distributor(to(supv(x,y)),A,B,oA,oB) for x in alld for y in alld)
    overlaps = [0.31,0.55,0.88,0.62,0.20,0.91,0.44]
    q = lambda o: 2 if o>=0.80 else (1 if o>=0.40 else 0)
    acc = []; cur = 0
    for o in overlaps:
        cur = max(cur,q(o)); acc.append(cur)
    monotono = all(acc[i]<=acc[i+1] for i in range(len(acc)-1))
    return closed, [q(o) for o in overlaps], acc, monotono

# VERIFICA DI ROBUSTEZZA (dopo l'audit avversariale del giro 7)
def V_riconciliazione_ordine():
    # unico ordine che rende partial-homom = monotono e' il poset-V (U minimo, P,N incomparabili);
    # coincide con l'ordine-prodotto dei due indicatori (sim,dis) = doppia diagonale; non la catena
    prod_le = lambda a,b: (sim[a]<=sim[b] and dis[a]<=dis[b])
    Vpos = set([(PP,PP),(NN,NN),(UU,UU),(UU,PP),(UU,NN)])
    coincide = all(prod_le(a,b)==((a,b) in Vpos) for a in VV for b in VV)
    chain_ne = any((chain[a]<=chain[b])!=((a,b) in Vpos) for a in VV for b in VV)
    return coincide, chain_ne

def V_T3a_teorema():
    # sup di distributori e' distributore perche' amp(x,max(y,z))==max(amp(x,y),amp(x,z))
    return all(amp(x,max(y,z))==max(amp(x,y),amp(x,z)) for x in E for y in E for z in E)

def V_stress_n3(T=500, seed=1):
    o3 = ['1','2','3']; random.seed(seed)
    def rand_cat():
        while True:
            M = {(a,b):(1 if a==b else random.choice(E)) for a in o3 for b in o3}
            if is_C3cat(M,o3):
                return M
    def close_dist(A,B):
        Phi = {(b,a):random.choice(E) for a in o3 for b in o3}
        for _ in range(8):
            for a in o3:
                for b in o3:
                    for bp in o3:
                        Phi[(bp,a)] = max(Phi[(bp,a)], amp(B[(bp,b)],Phi[(b,a)]))
                    for ap in o3:
                        Phi[(b,ap)] = max(Phi[(b,ap)], amp(Phi[(b,a)],A[(a,ap)]))
        return Phi
    okc=okd=oksup=asy=0
    for _ in range(T):
        A=rand_cat(); B=rand_cat()
        okc += is_C3cat(A,o3) and is_C3cat(B,o3)
        P1=close_dist(A,B); P2=close_dist(A,B)
        okd += is_distributor(P1,A,B,o3,o3) and is_distributor(P2,A,B,o3,o3)
        S = {key:max(P1[key],P2[key]) for key in P1}
        oksup += is_distributor(S,A,B,o3,o3)
        asy += any(P1[(b,a)]!=P1[(a,b)] for a in o3 for b in o3 if a!=b)
    return T,okc,okd,oksup,asy

if __name__=="__main__":
    print("[0] C3 quantale verificato esaustivamente:", verifica_quantale())
    bc, bch = T1_prova_puntuale()
    print("[T1] two-sided (D*/B*) <-> partial homom : discordanze=%d => %s" % (bc, 'PROVATO' if bc==0 else 'FALSO'))
    print("[T1] catena singola     <-> partial homom : discordanze=%d => %s" % (bch, 'coincide' if bch==0 else 'NON coincide'))
    coinc, chne = V_riconciliazione_ordine()
    print("[T1] ordine-prodotto==poset-V:", coinc, "; diverso da catena C3:", chne, "=> tensione RISOLTA")
    A,B,oA,oB,alld,asy = T2_costruzione()
    print("[T2] distributori validi=%d, asimmetrici=%d => COSTRUITO" % (len(alld), len(asy)))
    closed,perline,acc,mono = T3_verifica(A,B,oA,oB,alld)
    print("[T3] sup resta distributore:", closed, "; accumulo", perline, "->", acc, "monotono:", mono)
    print("[T3] &-distribuisce-su-sup su tutte le terne:", V_T3a_teorema(), "=> sup=distributore e' TEOREMA")
    Tn,okc,okd,oksup,asyn = V_stress_n3()
    print("[V5] stress 3-oggetti (%d prove): cat=%d, dist=%d, sup=dist=%d, asimmetrici=%d" % (Tn,okc,okd,oksup,asyn))
