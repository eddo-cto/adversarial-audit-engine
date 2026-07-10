#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Produce le 4 figure del paper (fig1..fig4) come PNG. Solo matplotlib.
# Uso: python3 make_figures.py   (scrive nella cartella corrente)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

NAVY="#1c2f47"; GREY="#6a7a88"; RED="#b03a2e"; GREEN="#1e7a52"; AMBER="#b9770e"
plt.rcParams.update({"font.size":11,"font.family":"DejaVu Sans"})

def node(ax,x,y,inner,color,r=0.17):
    ax.add_patch(plt.Circle((x,y),r,facecolor="white",edgecolor=color,lw=2.1,zorder=3))
    ax.text(x,y,inner,ha="center",va="center",fontsize=12,color=color,fontweight="bold",zorder=4)

# ---------- Fig 1: V-poset vs chain ----------
fig,axes=plt.subplots(1,2,figsize=(8.6,4.0))
ax=axes[0]; ax.set_title("Naïve reading: truth chain $C_3$",fontsize=11,color=NAVY,pad=10)
ax.plot([0,0],[0,2],color=GREY,lw=1.5,zorder=1)
for y,inner,lab in [(2,"R⁺","⊤"),(1,"R?","k"),(0,"R⁻","⊥")]:
    node(ax,0,y,inner,NAVY); ax.text(-0.45,y,lab,ha="right",va="center",fontsize=11,color=GREY)
ax.text(0,-0.75,"false < indeterminate < true\nlets R⁻ rise to R⁺   ✗",ha="center",va="top",fontsize=9,color=RED)
ax.set_xlim(-1.5,1.1); ax.set_ylim(-1.7,2.55); ax.axis("off"); ax.set_aspect("equal")
ax=axes[1]; ax.set_title("Correct reading: the V-poset",fontsize=11,color=NAVY,pad=10)
ax.plot([0,-1.05],[0,1.35],color=GREY,lw=1.5,zorder=1); ax.plot([0,1.05],[0,1.35],color=GREY,lw=1.5,zorder=1)
node(ax,-1.05,1.35,"R⁺",GREEN); ax.text(-1.05,1.62,"(sim ⊤, dis ⊥)",ha="center",va="bottom",fontsize=8.5,color=GREEN)
node(ax,1.05,1.35,"R⁻",RED);   ax.text(1.05,1.62,"(sim ⊥, dis ⊤)",ha="center",va="bottom",fontsize=8.5,color=RED)
node(ax,0,0,"R?",AMBER);       ax.text(0,-0.28,"(sim ⊥, dis ⊥)",ha="center",va="top",fontsize=8.5,color=AMBER)
ax.text(0,-0.95,"R⁺ and R⁻ incomparable; R? at bottom\npreserves both poles   ✓",ha="center",va="top",fontsize=9,color=GREEN)
ax.set_xlim(-2.0,2.0); ax.set_ylim(-1.9,2.35); ax.axis("off"); ax.set_aspect("equal")
fig.suptitle("Fig. 1 — The enrichment order of the partial-structure morphism (§3)",fontsize=11.5,color=NAVY,y=1.0)
fig.tight_layout(); fig.savefig("fig1_vposet_vs_chain.png",dpi=170,bbox_inches="tight"); plt.close(fig)

# ---------- Fig 2: two-diagonal square ----------
fig,ax=plt.subplots(figsize=(5.2,4.2))
ax.annotate("",xy=(1.35,0),xytext=(0,0),arrowprops=dict(arrowstyle="-|>",color=GREY,lw=1.4))
ax.annotate("",xy=(0,1.35),xytext=(0,0),arrowprops=dict(arrowstyle="-|>",color=GREY,lw=1.4))
node(ax,0,0,"R?",AMBER,r=0.13); ax.text(-0.16,-0.16,"(⊥,⊥)",ha="right",va="top",fontsize=8.5,color=AMBER)
node(ax,1,0,"R⁺",GREEN,r=0.13); ax.text(1,-0.20,"(⊤,⊥)",ha="center",va="top",fontsize=8.5,color=GREEN)
node(ax,0,1,"R⁻",RED,r=0.13);   ax.text(-0.16,1.02,"(⊥,⊤)",ha="right",va="center",fontsize=8.5,color=RED)
ax.text(1.40,-0.02,"similarity",fontsize=9.5,color=GREY,va="center",ha="left")
ax.text(0.03,1.44,"dissimilarity",fontsize=9.5,color=GREY,ha="left",va="center")
ax.text(0.66,0.66,"product order\n= V-poset",fontsize=8.8,color=NAVY,ha="center",style="italic")
ax.set_title("Fig. 2 — Two-component encoding\n$R^+\\!=(\\top,\\bot),\\ \\ R^-\\!=(\\bot,\\top),\\ \\ R?=(\\bot,\\bot)$",fontsize=10,color=NAVY)
ax.set_xlim(-0.65,1.9); ax.set_ylim(-0.6,1.65); ax.axis("off"); ax.set_aspect("equal")
fig.tight_layout(); fig.savefig("fig2_two_diagonal.png",dpi=170,bbox_inches="tight"); plt.close(fig)

# ---------- Fig 3: real accumulation (Giugliano) ----------
aspects=["cadastral /\nplanimetry","sanability\n(art.36)","habitability /\nSCA","common\nproperty"]
Psi=np.array([[2,0,0,0],[2,1,0,0],[2,1,2,0],[2,1,2,2]])
lines=["L1 cross-cadastral","L2 sanability","L3 habitability","L4 condominium"]
fig,ax=plt.subplots(figsize=(6.2,3.8))
cmap=matplotlib.colors.ListedColormap(["#eceff2","#f2d38a","#1e7a52"])
ax.imshow(Psi,cmap=cmap,vmin=0,vmax=2,aspect="auto")
ax.set_xticks(range(4)); ax.set_xticklabels(aspects,fontsize=8)
ax.set_yticks(range(4)); ax.set_yticklabels([f"$\\Psi_{i+1}$: +{lines[i]}" for i in range(4)],fontsize=8)
for i in range(4):
    for j in range(4):
        v=Psi[i,j]; ax.text(j,i,{0:"⊥",1:"k",2:"⊤"}[v],ha="center",va="center",
                            fontsize=11,color="white" if v!=1 else "#5a3d00",fontweight="bold")
ax.set_title("Fig. 3 — Real diachronic accumulation $\\Psi_n$ (Giugliano audit)\nmonotone, non-redundant; residue: sanability stays k (declared abstention)",fontsize=9.5,color=NAVY)
fig.tight_layout(); fig.savefig("fig3_accumulation_giugliano.png",dpi=170,bbox_inches="tight"); plt.close(fig)

# ---------- Fig 4: interleaving ----------
fig,ax=plt.subplots(figsize=(6.2,3.4))
t=np.arange(0,11)
M1=np.where(t>=3,2,0); N1=np.where(t>=6,2,0)
ax.step(t,M1,where="post",color=GREEN,lw=2.2,label="survivor M (saturates t=3)")
ax.step(t,N1+0.05,where="post",color=NAVY,lw=2.2,label="survivor N (saturates t=6)")
ax.annotate("",xy=(6,1.0),xytext=(3,1.0),arrowprops=dict(arrowstyle="<|-|>",color=RED,lw=1.6))
ax.text(4.5,1.12,"interleaving $d_I=3$",ha="center",color=RED,fontsize=9)
ax.text(9.6,2.05,"same colimit ⊤\n(join confuses them)",ha="right",va="bottom",fontsize=8,color=GREY)
ax.set_yticks([0,2]); ax.set_yticklabels(["⊥","⊤"]); ax.set_xlabel("stage (independent line index)",fontsize=9)
ax.set_ylim(-0.4,2.6); ax.legend(fontsize=8,loc="center right")
ax.set_title("Fig. 4 — The interleaving distance separates trajectories the join conflates (§5)",fontsize=9.5,color=NAVY)
ax.spines[["top","right"]].set_visible(False)
fig.tight_layout(); fig.savefig("fig4_interleaving.png",dpi=170,bbox_inches="tight"); plt.close(fig)
print("figure generate: fig1..fig4")
