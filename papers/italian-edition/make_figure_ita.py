#!/usr/bin/env python3
"""Figure in italiano per l'edizione leggibile."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np, os

os.makedirs("figure_ita", exist_ok=True)
INK="#141210"; ACC="#2a2a44"; GREY="#63605a"
RED="#a8432f"; GREEN="#2f6f4f"; AMBER="#b8860b"; BLUE="#33587a"
plt.rcParams.update({
    "font.family":"DejaVu Serif","font.size":8.5,
    "axes.edgecolor":GREY,"axes.labelcolor":INK,"text.color":INK,
    "xtick.color":GREY,"ytick.color":GREY,"axes.titlesize":9.5,
    "axes.spines.top":False,"axes.spines.right":False,
})

# ── Fig 1 ─ il cancello dei sopravvissuti ────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.6, 2.9)); ax.axis("off")
ax.set_xlim(0, 10); ax.set_ylim(0, 4.2)
def box(x,y,w,h,label,sub,fc,ec):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.06",fc=fc,ec=ec,lw=1.1))
    ax.text(x+w/2,y+h*0.64,label,ha="center",va="center",fontsize=9,weight="bold",color=INK)
    ax.text(x+w/2,y+h*0.24,sub,ha="center",va="center",fontsize=6.8,color=GREY,style="italic")
box(0.2,2.4,2.1,1.2,"respinto","basta una smentita\nindipendente","#fbeeea",RED)
box(2.6,2.4,2.1,1.2,"indeciso","l'evidenza\nnon chiude","#fdf6e3",AMBER)
box(5.0,2.4,2.1,1.2,"sopravvissuto","ciò che resta dopo\nogni attacco","#eef5f0",GREEN)
ax.annotate("",xy=(2.55,3.0),xytext=(2.35,3.0),arrowprops=dict(arrowstyle="-|>",color=GREY,lw=1))
ax.annotate("",xy=(4.95,3.0),xytext=(4.75,3.0),arrowprops=dict(arrowstyle="-|>",color=GREY,lw=1))
ax.text(3.65,3.85,"tre esiti possibili, non due",ha="center",fontsize=8.5,color=ACC,weight="bold")
box(7.5,2.4,2.3,1.2,"il controllore","riconosce i fallimenti,\nma non certifica sé stesso","#f2f4f8",ACC)
ax.annotate("",xy=(7.45,3.0),xytext=(7.15,3.0),arrowprops=dict(arrowstyle="-|>",color=ACC,lw=1.2))
ax.add_patch(FancyArrowPatch((8.65,2.35),(8.65,1.15),arrowstyle="-|>",mutation_scale=12,
                             color=RED,lw=1.4,linestyle=(0,(4,2))))
ax.text(8.65,0.72,"limite dichiarato",ha="center",fontsize=8,color=RED,weight="bold")
ax.text(8.65,0.34,"il residuo passa a un occhio esterno",ha="center",fontsize=6.6,color=GREY,style="italic")
ax.text(0.2,1.35,"Attacchi su più strati",fontsize=8,color=ACC,weight="bold")
ax.text(0.2,0.95,"chi demolisce troppo poco  ·  chi demolisce troppo: entrambi sorvegliati",
        fontsize=7,color=GREY)
ax.text(0.2,0.55,"la catena non si ferma con un ennesimo controllo della stessa natura,",
        fontsize=7,color=GREY,style="italic")
ax.text(0.2,0.18,"ma consegnando ciò che resta a un occhio che non ci si può fabbricare in casa.",
        fontsize=7,color=GREY,style="italic")
plt.tight_layout(); plt.savefig("figure_ita/fig1.png",dpi=190,bbox_inches="tight",facecolor="white"); plt.close()

# ── Fig 2 ─ esopianeti ───────────────────────────────────────────────────────
fig,(a1,a2)=plt.subplots(1,2,figsize=(6.8,2.7),gridspec_kw={"width_ratios":[1.15,1]})
tiers=["falso positivo\n(respinto)","candidato\n(indeciso)","confermato"]
counts=[4839,1978,2746]
bars=a1.bar(tiers,counts,color=[RED,AMBER,GREEN],alpha=.78,edgecolor="white",width=.66)
a1.set_ylabel("oggetti osservati da Kepler")
a1.set_title("Un archivio reale usa gli stessi tre esiti",loc="left",color=ACC,fontsize=9)
for b,c in zip(bars,counts):
    a1.text(b.get_x()+b.get_width()/2,c+90,f"{c:,}".replace(",","."),ha="center",fontsize=7.5,color=INK)
a1.set_ylim(0,5600); a1.tick_params(axis="x",labelsize=7)
a2.axis("off"); a2.set_xlim(0,10); a2.set_ylim(-0.7,10)
a2.text(0,9.4,"Il secondo canale, di natura diversa",fontsize=8.6,weight="bold",color=ACC)
a2.text(0,8.55,"249 pianeti pesati con un metodo indipendente",fontsize=7.1,color=GREY)
n=249; cols=25
for i in range(n):
    r,c=divmod(i,cols)
    a2.add_patch(plt.Rectangle((0.30+0.36*c,7.35-0.62*r),0.26,0.44,
                 fc=(RED if i>=n-7 else "#cdd8d2"),ec="none"))
a2.add_patch(plt.Rectangle((0.30,3.35),0.26,0.44,fc="#cdd8d2",ec="none"))
a2.text(0.85,3.57,"242 d'accordo — ma il campione è scelto:",fontsize=7.1,color=GREY,va="center")
a2.text(0.85,2.72,"il secondo metodo si usa solo sui casi promettenti;",fontsize=7.1,color=GREY,va="center")
a2.text(0.85,2.05,"i falsi positivi non vengono mai ricontrollati.",fontsize=7.1,color=GREY,va="center")
a2.add_patch(plt.Rectangle((0.30,0.95),0.26,0.44,fc=RED,ec="none"))
a2.text(0.85,1.17,"7 casi di riscatto: il canale indipendente",fontsize=7.2,color=RED,weight="bold",va="center")
a2.text(0.85,0.36,"corregge l'errore del primo. Questi la selezione",fontsize=7.1,color=GREY,va="center")
a2.text(0.85,-0.28,"non può fabbricarli: sono il vero risultato.",fontsize=7.1,color=GREY,va="center")
plt.tight_layout(); plt.savefig("figure_ita/fig2.png",dpi=190,bbox_inches="tight",facecolor="white"); plt.close()

# ── Fig 3 ─ la tesi ritirata ─────────────────────────────────────────────────
fig,ax=plt.subplots(figsize=(6.6,2.6))
labels=["genetica clinica\n(ClinVar)","sicurezza informatica\n(dato grezzo)","sicurezza informatica\n(disaccordo vero)"]
vals=[19.8,60.0,23.1]
bars=ax.bar(labels,vals,color=[BLUE,"#d9c9b0",BLUE],edgecolor="white",width=.55)
bars[1].set_hatch("///"); bars[1].set_edgecolor(GREY)
ax.axhline(19.8,color=GREY,lw=.8,ls=(0,(4,3)))
for b,v in zip(bars,vals):
    ax.text(b.get_x()+b.get_width()/2,v+1.4,f"{v:.1f} %".replace(".",","),ha="center",fontsize=8,weight="bold",color=INK)
ax.annotate("",xy=(1.0,55),xytext=(2.0,26),
            arrowprops=dict(arrowstyle="-|>",color=RED,lw=1.3,connectionstyle="arc3,rad=-0.25"))
ax.text(1.5,44,"24 disaccordi su 39\nerano di un solo gradino:\nnon giudizi diversi,\nsolo misure tarate diversamente",
        fontsize=6.9,color=RED,ha="center",style="italic")
ax.set_ylabel("quante volte due valutatori indipendenti\nnon sono d'accordo (%)",fontsize=7.6)
ax.set_ylim(0,70); ax.tick_params(axis="x",labelsize=7)
ax.set_title("Una nostra tesi, smentita da una nostra misura",loc="left",color=ACC,fontsize=9)
plt.tight_layout(); plt.savefig("figure_ita/fig3.png",dpi=190,bbox_inches="tight",facecolor="white"); plt.close()

# ── Fig 4 ─ la figura decisiva ───────────────────────────────────────────────
fig,(ax,axb)=plt.subplots(1,2,figsize=(7.0,3.0),gridspec_kw={"width_ratios":[1.35,1]})
ages=["0–2","3–5","6–9","10+"]
d34=[6.4,6.3,19.6,27.0]; d59=[16.3,12.8,29.5,39.7]; d10=[np.nan,25.4,35.7,58.2]
x=np.arange(4)
ax.plot(x,d34,"o-",color="#9fb3c8",lw=1.6,ms=5,label="3–4 laboratori")
ax.plot(x,d59,"s-",color=BLUE,lw=1.8,ms=5,label="5–9 laboratori")
ax.plot(x,d10,"^-",color=ACC,lw=2.0,ms=6,label="10 o più laboratori")
ax.set_xticks(x); ax.set_xticklabels(ages)
ax.set_xlabel("anni trascorsi nel sistema")
ax.set_ylabel("casi indecisi che si sciolgono (%)")
ax.set_title("Più occhi indipendenti, più dubbi risolti",loc="left",color=ACC,fontsize=9)
ax.legend(frameon=False,fontsize=7,loc="upper left"); ax.set_ylim(0,65)
ax.add_patch(plt.Rectangle((-0.18,4.6),1.36,3.6,fc="#fbeeea",ec=RED,lw=1.0,zorder=0))
ax.annotate("qui il tempo\nnon serve a nulla:\nda 6,4 % a 6,3 %",xy=(0.5,6.35),xytext=(0.62,47),
            arrowprops=dict(arrowstyle="-|>",color=RED,lw=1.2,connectionstyle="arc3,rad=0.22"),
            fontsize=6.9,color=RED,ha="center",weight="bold")
ax.annotate("",xy=(1.0,25.4),xytext=(1.0,7.4),arrowprops=dict(arrowstyle="-|>",color=GREEN,lw=1.6))
ax.text(1.12,15.5,"eppure gli occhi\nin più fanno salire\nda 6,3 % a 25,4 %",fontsize=6.9,color=GREEN,weight="bold")
axb.axis("off"); axb.set_xlim(0,10); axb.set_ylim(0,10)
axb.text(0,9.4,"Due modi di sciogliere un dubbio",fontsize=9,weight="bold",color=ACC)
for i,(lab,v,c) in enumerate([("3–4 laboratori",14.0,"#9fb3c8"),("5–9 laboratori",28.5,BLUE),
                              ("10 o più laboratori",48.9,ACC),("un collegio di esperti",53.1,GREEN)]):
    y=7.6-i*1.55
    axb.add_patch(plt.Rectangle((0,y),v*0.115,0.72,fc=c,ec="none"))
    axb.text(v*0.115+0.18,y+0.34,f"{v:.1f} %".replace(".",","),va="center",fontsize=7.6,weight="bold",color=INK)
    axb.text(0,y+1.0,lab,fontsize=7,color=GREY)
axb.text(0,1.35,"L'occhio esterno è il più ",fontsize=7.4,color=INK)
axb.text(2.86,1.35,"veloce",fontsize=7.4,color=GREEN,weight="bold")
axb.text(0,0.72,"— non è l'unico. Con molti occhi indipendenti",fontsize=7.2,color=GREY)
axb.text(0,0.12,"i due modi quasi si raggiungono (48,9 e 53,1).",fontsize=7.2,color=GREY)
plt.tight_layout(); plt.savefig("figure_ita/fig4.png",dpi=190,bbox_inches="tight",facecolor="white"); plt.close()
print("4 figure italiane generate")
