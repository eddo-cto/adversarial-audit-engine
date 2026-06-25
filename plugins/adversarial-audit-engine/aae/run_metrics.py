"""
run_metrics.py — longitudinal, BIAS-RESISTANT operational metrics across audits.

Why this module is dangerous (and how it is disarmed):
  A metric becomes a target (Goodhart). If we shipped a single "quality score",
  the engine — or its operator — would optimize the number instead of the truth.
  So this module is built to make gaming VISIBLE, not rewarded:

  1. NO single composite score. A panel of ORTHOGONAL rates only.
  2. ABSTENTION is its own bucket. It is never folded into "pass"/"success".
     A run that abstains on everything earns no quality credit.
  3. SYMMETRY. Over-condemnation risk and escape (missed-defect) risk are both
     reported. You cannot inflate one without the other becoming visible.
  4. ESCAPE / precision / recall require EXTERNAL human ground truth. Without it
     they return None ("unknown") — never an imputed, self-serving 0.
  5. A bias_audit() flags the tell-tale signatures (rubber-stamp, over-condemn,
     all-abstain) so a "good-looking" run that is actually degenerate is caught.

Deterministic, stdlib only. No LLM. The numbers describe; they do not decide.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# verdict value categories (schema.Verdict .value strings)
_CONDEMN = {"accusa_vince", "accusa_ridimensionata"}     # ARTIFACT_DEFECTIVE, REDUCED
_ABSOLVE = {"artefatto_regge"}                            # ARTIFACT_HOLDS
_ABSTAIN = {"da_leggere", "conteso", "pending"}           # NEEDS_READING, NEEDS_EXPERT, PENDING


@dataclass
class GroundTruth:
    """Per-decision human labels, aggregated. Only a human can fill these."""
    tp: int = 0   # condemned AND truly defective
    fp: int = 0   # condemned BUT not defective (false accusation)
    fn: int = 0   # NOT condemned BUT truly defective (escape)
    tn: int = 0   # not condemned and not defective

    def total(self) -> int:
        return self.tp + self.fp + self.fn + self.tn


@dataclass
class RunRecord:
    """One audit run reduced to counts. Build from a Ledger or pass directly."""
    verdicts: dict[str, int] = field(default_factory=dict)   # verdict value -> count
    iterations: Optional[int] = None                         # rounds to convergence, if tracked
    grounding_downgrades: int = 0                            # anti-hallucination interventions
    by_class: dict[str, int] = field(default_factory=dict)


def from_ledger(ledger) -> RunRecord:
    v: dict[str, int] = {}
    cls: dict[str, int] = {}
    downg = 0
    for f in ledger.findings:
        vv = f.verdict.value if hasattr(f.verdict, "value") else str(f.verdict)
        v[vv] = v.get(vv, 0) + 1
        cv = getattr(getattr(f, "defect_class", None), "value", None)
        if cv:
            cls[cv] = cls.get(cv, 0) + 1
        if getattr(f, "declared_limit", None) and "GROUNDING" in f.declared_limit:
            downg += 1
    return RunRecord(verdicts=v, grounding_downgrades=downg, by_class=cls)


@dataclass
class Panel:
    n_runs: int
    n_findings: int
    counts: dict[str, int]                 # raw verdict counts
    condemnation_rate: Optional[float]     # share of findings condemned
    absolution_rate: Optional[float]       # share defended/held
    abstention_rate: Optional[float]       # share routed to human (NOT a success)
    grounding_intervention_rate: Optional[float]
    mean_iterations: Optional[float]
    by_class: dict[str, int]
    # ground-truth-only (None unless human labels provided):
    precision: Optional[float]             # of condemnations, how many were real
    recall: Optional[float]                # of real defects, how many caught
    escape_rate: Optional[float]           # of real defects, how many missed
    false_accusation_rate: Optional[float] # of condemnations, how many wrong
    ground_truth_n: int = 0

    def as_text(self) -> str:
        def pc(x): return "n/d" if x is None else f"{x:.0%}"
        L = [
            "=== Panel metriche (descrittivo, NESSUN punteggio unico) ===",
            f"run: {self.n_runs} | findings: {self.n_findings}",
            f"condanna: {pc(self.condemnation_rate)} | assoluzione: {pc(self.absolution_rate)} | "
            f"ASTENSIONE→umano: {pc(self.abstention_rate)} (non è un successo)",
            f"interventi grounding (anti-allucinazione): {pc(self.grounding_intervention_rate)}",
            f"iterazioni medie a convergenza: {'n/d' if self.mean_iterations is None else f'{self.mean_iterations:.2f}'}",
            "conteggi verdetti: " + (", ".join(f"{k}={v}" for k, v in self.counts.items()) or "-"),
            "per classe: " + (", ".join(f"{k}={v}" for k, v in self.by_class.items()) or "-"),
        ]
        if self.ground_truth_n:
            L += ["--- con ground-truth umano (%d decisioni etichettate) ---" % self.ground_truth_n,
                  f"precision: {pc(self.precision)} | recall: {pc(self.recall)} | "
                  f"ESCAPE (difetti mancati): {pc(self.escape_rate)} | "
                  f"false accuse: {pc(self.false_accusation_rate)}"]
        else:
            L += ["--- precision/recall/escape: n/d (richiedono ground-truth umano; non stimati) ---"]
        return "\n".join(L)


def compute(runs: list[RunRecord], ground_truth: Optional[GroundTruth] = None) -> Panel:
    counts: dict[str, int] = {}
    by_class: dict[str, int] = {}
    iters: list[int] = []
    downg = 0
    for r in runs:
        for k, n in r.verdicts.items():
            counts[k] = counts.get(k, 0) + n
        for k, n in r.by_class.items():
            by_class[k] = by_class.get(k, 0) + n
        if r.iterations is not None:
            iters.append(r.iterations)
        downg += r.grounding_downgrades
    total = sum(counts.values())

    def rate(keys):
        if total == 0:
            return None
        return sum(counts.get(k, 0) for k in keys) / total

    gt = ground_truth
    prec = rec = esc = fa = None
    gtn = 0
    if gt and gt.total() > 0:
        gtn = gt.total()
        prec = (gt.tp / (gt.tp + gt.fp)) if (gt.tp + gt.fp) else None
        rec = (gt.tp / (gt.tp + gt.fn)) if (gt.tp + gt.fn) else None
        esc = (gt.fn / (gt.tp + gt.fn)) if (gt.tp + gt.fn) else None
        fa = (gt.fp / (gt.tp + gt.fp)) if (gt.tp + gt.fp) else None

    return Panel(
        n_runs=len(runs), n_findings=total, counts=counts,
        condemnation_rate=rate(_CONDEMN), absolution_rate=rate(_ABSOLVE),
        abstention_rate=rate(_ABSTAIN),
        grounding_intervention_rate=(downg / total if total else None),
        mean_iterations=(sum(iters) / len(iters) if iters else None),
        by_class=by_class,
        precision=prec, recall=rec, escape_rate=esc, false_accusation_rate=fa,
        ground_truth_n=gtn,
    )


def bias_audit(p: Panel) -> list[str]:
    """Flag degenerate / gameable signatures so a 'good-looking' panel that is
    actually biased is caught. Returns warnings; empty list = no red flags."""
    w: list[str] = []
    if p.n_findings == 0:
        return ["Nessun finding: panel non interpretabile."]
    cr, ar, ab = (p.condemnation_rate or 0), (p.absolution_rate or 0), (p.abstention_rate or 0)
    # rubber-stamp: non condanna quasi nulla e non si astiene → 'tutto a posto' sospetto
    if cr <= 0.02 and ab <= 0.10:
        w.append("FIRMA TIMBRO: ~0 condanne e poche astensioni → sospetta leniency, "
                 "non merito. Verifica copertura/recall, non festeggiare il numero.")
    # all-abstain: si astiene su tutto → non è onestà, è inutilità
    if ab >= 0.90:
        w.append("QUASI-TUTTO ASTENUTO: il motore non decide nulla. Astenersi è onesto, "
                 "ma astenersi sempre è inutile — controlla copertura e soglie.")
    # over-condemn: condanna altissima → rischio falsi positivi
    if cr >= 0.80:
        w.append("CONDANNA MOLTO ALTA: rischio falsi positivi. Senza ground-truth, "
                 "non puoi dire se è rigore o accusa facile.")
    # claims of quality without ground truth
    if p.escape_rate is None:
        w.append("ESCAPE/RECALL non misurati: senza ground-truth umano NON affermare "
                 "qualità di copertura. I numeri sopra descrivono solo la distribuzione.")
    # asymmetry reminder if only one side of GT present
    if p.ground_truth_n and (p.recall is not None and p.precision is None):
        w.append("Ground-truth asimmetrico: hai recall ma non precision (o viceversa). "
                 "Riporta entrambi o nessuno.")
    return w
