#!/usr/bin/env python3
"""Figures for 'Managing circularity in self-referential evaluation'.
Deterministic; all numbers hard-coded from the reproducible analyses in this package.
v2: layout hardened for legibility (no text/graphic collisions), 300 dpi."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np, os

OUT = os.environ.get("FIGOUT", "figure_paper")
os.makedirs(OUT, exist_ok=True)
INK="#141210"; ACC="#2a2a44"; GREY="#63605a"; RULE="#c5cdd2"
RED="#a8432f"; GREEN="#2f6f4f"; AMBER="#b8860b"; BLUE="#33587a"
plt.rcParams.update({
    "font.family":"DejaVu Serif","font.size":9,
    "axes.edgecolor":GREY,"axes.labelcolor":INK,"text.color":INK,
    "xtick.color":GREY,"ytick.color":GREY,"axes.titlesize":10,
    "axes.spines.top":False,"axes.spines.right":False,
})
DPI=300

# ── Fig 1 ─ The survivor gate: C3 verdict tiers and declared non-closure ──────
fig, ax = plt.subplots(figsize=(6.8, 3.0))
ax.axis("off")
ax.set_xlim(0, 10); ax.set_ylim(0, 4.2)

def box(x, y, w, h, label, sub, fc, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                fc=fc, ec=ec, lw=1.1))
    ax.text(x+w/2, y+h*0.62, label, ha="center", va="center", fontsize=9.5, weight="bold", color=INK)
    ax.text(x+w/2, y+h*0.24, sub, ha="center", va="center", fontsize=7.2, color=GREY, style="italic")

box(0.2, 2.4, 2.1, 1.2, "⊥  refuted", "floor: one independent\nfalsification suffices", "#fbeeea", RED)
box(2.6, 2.4, 2.1, 1.2, "k  indeterminate", "abstention: evidence\ndoes not close", "#fdf6e3", AMBER)
box(5.0, 2.4, 2.1, 1.2, "⊤  survivor", "maximally guarded\nresidue", "#eef5f0", GREEN)

ax.annotate("", xy=(2.55,3.0), xytext=(2.35,3.0),
            arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1))
ax.annotate("", xy=(4.95,3.0), xytext=(4.75,3.0),
            arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1))
ax.text(3.65, 3.9, "quantale $C_3$:  ⊥ < k < ⊤", ha="center", fontsize=9, color=ACC, weight="bold")

box(7.5, 2.4, 2.3, 1.2, "governor", "detects failure signatures;\ndoes not certify itself", "#f2f4f8", ACC)
ax.annotate("", xy=(7.45,3.0), xytext=(7.15,3.0),
            arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.2))
arrow = FancyArrowPatch((8.65,2.35),(8.65,1.15), arrowstyle="-|>", mutation_scale=12,
                        color=RED, lw=1.4, linestyle=(0,(4,2)))
ax.add_patch(arrow)
ax.text(8.65, 0.72, "declared non-closure", ha="center", fontsize=8.4, color=RED, weight="bold")
ax.text(8.65, 0.34, "residue → external eye", ha="center", fontsize=7.4, color=GREY, style="italic")

ax.text(0.2, 1.35, "Stratified adversarial layers", fontsize=8.4, color=ACC, weight="bold")
ax.text(0.2, 0.92, "attack (under-demolition guard)  ·  meta-level (over-demolition guard)",
        fontsize=7.4, color=GREY)
ax.text(0.2, 0.55, "the regress is arrested not by one more control of the same nature,",
        fontsize=7.4, color=GREY, style="italic")
ax.text(0.2, 0.22, "but by handing the residue to an eye the architecture cannot manufacture.",
        fontsize=7.4, color=GREY, style="italic")
plt.tight_layout()
plt.savefig(f"{OUT}/fig1_survivor_gate.png", dpi=DPI, bbox_inches="tight", facecolor="white")
plt.close()

# ── Fig 2 ─ Exoplanets: selection-limited concordance vs the 7 rescue cases ───
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw={"width_ratios":[1.08,1]})

tiers = ["FALSE POSITIVE\n(⊥)", "CANDIDATE\n(k)", "CONFIRMED\n(⊤)"]
counts = [4839, 1978, 2746]
scores = [0.038, 0.798, 0.960]
bars = a1.bar(tiers, counts, color=[RED, AMBER, GREEN], alpha=.78, edgecolor="white", width=.66)
a1.set_ylabel("KOI objects")
a1.set_title("Kepler KOI: graded verdict tiers", loc="left", color=ACC)
for b, c, s in zip(bars, counts, scores):
    a1.text(b.get_x()+b.get_width()/2, c+90, f"{c:,}", ha="center", fontsize=8, color=INK)
    a1.text(b.get_x()+b.get_width()/2, c*0.5, f"mean\nkoi_score\n{s:.3f}", ha="center",
            fontsize=7, color="white", weight="bold")
a1.set_ylim(0, 5600)
a1.tick_params(axis="x", labelsize=7.6)

# right panel: waffle block on TOP, all explanatory text BELOW it (no overlap)
a2.axis("off")
a2.set_xlim(0,10); a2.set_ylim(0.4,10)
a2.text(0, 9.55, "External channel: radial velocity", fontsize=9, weight="bold", color=ACC)
a2.text(0, 8.9, "249 joined planets — all already ⊤ in transit", fontsize=7.6, color=GREY)

n=249; cols=27; top=8.15; ystep=0.315; xstep=0.345; sq=0.29
for i in range(n):
    r, c = divmod(i, cols)
    rescue = i >= n-7
    a2.add_patch(plt.Rectangle((0.10+xstep*c, top-ystep*r), sq, sq*0.9,
                 fc=(RED if rescue else "#cdd8d2"), ec="none"))
# bottom of grid ≈ top-ystep*9 = 8.15-2.84 = 5.31 ; text starts at 4.5

def swatch(y, color):
    a2.add_patch(plt.Rectangle((0.10, y-0.02), 0.30, 0.30, fc=color, ec="none"))

swatch(4.30, "#cdd8d2")
a2.text(0.62, 4.44, "242 concordant — but doubly selected:", fontsize=7.7, color=GREY, va="center")
a2.text(0.62, 3.72, "RV runs on promising targets only;", fontsize=7.7, color=GREY, va="center")
a2.text(0.62, 3.14, "transit false positives get no follow-up.", fontsize=7.7, color=GREY, va="center")

swatch(2.15, RED)
a2.text(0.62, 2.29, "7 rescue cases: the independent channel", fontsize=7.8, color=RED,
        weight="bold", va="center")
a2.text(0.62, 1.55, "overrides the transit verdict — selection", fontsize=7.7, color=GREY, va="center")
a2.text(0.62, 0.97, "cannot manufacture these (non-circular weight).", fontsize=7.7, color=GREY, va="center")
plt.tight_layout()
plt.savefig(f"{OUT}/fig2_exoplanets.png", dpi=DPI, bbox_inches="tight", facecolor="white")
plt.close()

# ── Fig 3 ─ Contestedness: the withdrawn spread ──────────────────────────────
fig, ax = plt.subplots(figsize=(6.9, 2.9))
labels = ["ClinVar / ACMG\n(genetics)", "NVD / CVE\n(security, raw)", "NVD / CVE\n(judgement-level)"]
vals = [19.8, 60.0, 23.1]
cols = [BLUE, "#d9c9b0", BLUE]
bars = ax.bar(labels, vals, color=cols, edgecolor="white", width=.52)
bars[1].set_hatch("///"); bars[1].set_edgecolor(GREY)
ax.axhline(19.8, color=GREY, lw=.8, ls=(0,(4,3)))
ax.text(-0.02, 67.5, "– – –  dashed line: genetics baseline 19.8 %", fontsize=7, color=GREY,
        ha="left", va="top")
for b, v in zip(bars, vals):
    ax.text(b.get_x()+b.get_width()/2, v+1.6, f"{v:.1f} %", ha="center", fontsize=8.4, weight="bold", color=INK)
# annotation placed to the RIGHT of the tall bar, above the short judgement-level bar (clear space)
ax.annotate("", xy=(1.08, 57), xytext=(1.55, 50),
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.3,
                            connectionstyle="arc3,rad=-0.2"))
ax.text(1.45, 49, "decomposition: 24 of 39\ndisagreements are one grade\napart (calibration, not\njudgement)",
        fontsize=7.1, color=RED, ha="left", va="top", style="italic")
ax.set_ylabel("independent-channel disagreement (%)")
ax.set_ylim(0, 70)
ax.set_title("The contestedness spread does not survive its own decomposition — claim withdrawn",
             loc="left", color=ACC, fontsize=9)
ax.tick_params(axis="x", labelsize=7.6)
plt.tight_layout()
plt.savefig(f"{OUT}/fig3_contestedness.png", dpi=DPI, bbox_inches="tight", facecolor="white")
plt.close()

# ── Fig 4 ─ The money figure: stratified dose-response ───────────────────────
fig, (ax, axb) = plt.subplots(1, 2, figsize=(7.6, 3.3), gridspec_kw={"width_ratios":[1.35,1]})

ages = ["0–2", "3–5", "6–9", "10+"]
d34 = [6.4, 6.3, 19.6, 27.0]
d59 = [16.3, 12.8, 29.5, 39.7]
d10 = [np.nan, 25.4, 35.7, 58.2]   # 0-2 x 10+ is n=2 -> omitted
x = np.arange(4)

ax.plot(x, d34, "o-", color="#9fb3c8", lw=1.6, ms=5, label="3–4 submitters")
ax.plot(x, d59, "s-", color=BLUE, lw=1.8, ms=5, label="5–9 submitters")
ax.plot(x, d10, "^-", color=ACC, lw=2.0, ms=6, label="10+ submitters")
ax.set_xticks(x); ax.set_xticklabels(ages)
ax.set_xlabel("years in system (exposure)")
ax.set_ylabel("k resolved to a definite verdict (%)")
ax.set_title("Peer accumulation resolves k at fixed exposure", loc="left", color=ACC, fontsize=9)
ax.legend(frameon=False, fontsize=7.4, loc="lower right")   # moved out of the upper-left annotation zone
ax.set_ylim(0, 66)

# highlight the flat-clock band + red annotation (upper-left, now clear of the legend)
ax.add_patch(plt.Rectangle((-0.18, 4.6), 1.36, 3.6, fc="#fbeeea", ec=RED, lw=1.0, zorder=0))
ax.annotate("time is flat here:\n6.4 % → 6.3 %\nat fixed channels",
            xy=(0.5, 6.35), xytext=(0.30, 52),
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.2,
                            connectionstyle="arc3,rad=0.22"),
            fontsize=7.1, color=RED, ha="left", va="top", weight="bold")
ax.annotate("", xy=(1.0, 25.4), xytext=(1.0, 7.4),
            arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.6))
ax.text(1.12, 18.0, "yet accumulation\nlifts 6.3 → 25.4 %\ninside that band",
        fontsize=7.1, color=GREEN, weight="bold", va="center")

# right panel: mechanism comparison
axb.axis("off"); axb.set_xlim(0,10); axb.set_ylim(0,10)
axb.text(0, 9.5, "Both mechanisms resolve k", fontsize=9.5, weight="bold", color=ACC)
bars2 = [("peer-only, 3–4", 14.0, "#9fb3c8"),
         ("peer-only, 5–9", 28.5, BLUE),
         ("peer-only, 10+", 48.9, ACC),
         ("expert panel", 53.1, GREEN)]
for i,(lab,v,c) in enumerate(bars2):
    y = 8.0 - i*1.55
    axb.add_patch(plt.Rectangle((0, y), v*0.115, 0.72, fc=c, ec="none"))
    axb.text(v*0.115+0.20, y+0.34, f"{v:.1f} %", va="center", fontsize=8, weight="bold", color=INK)
    axb.text(0, y+1.02, lab, fontsize=7.3, color=GREY)
# caption as clean, non-overlapping lines (was three overlapping text() calls)
axb.text(0, 1.35, "The external eye is the faster resolver —", fontsize=7.6, color=INK, style="italic")
axb.text(0, 0.72, "not the only one. At high accumulation", fontsize=7.4, color=GREY)
axb.text(0, 0.12, "the two rates converge (48.9 vs 53.1 %).", fontsize=7.4, color=GREY)
plt.tight_layout()
plt.savefig(f"{OUT}/fig4_stratified.png", dpi=DPI, bbox_inches="tight", facecolor="white")
plt.close()

print("4 figure generate in", OUT)
for f in sorted(os.listdir(OUT)):
    print("  ", f)
