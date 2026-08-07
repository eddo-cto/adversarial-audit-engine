"""
run_manifest.py — the execution manifest (round 13, standardization step 2).

Purpose: make "a run" a checkable object with an execution contract, so the
"loses pieces" failure mode becomes impossible to hide. For each declared stage
it records RAN / NOT_APPLICABLE(justified) / MISSING.

`REQUIRED_LAYERS` is now POPULATED FROM MEASUREMENT (round 15, five artifact
classes; see the constant below) — never assumed from the module sprawl, because
freezing an unmeasured minimum is the one misstep to avoid. So the A+B judgment is
LIVE:
  * condition A — no REQUIRED layer is MISSING;
  * condition B — no declared layer is left un-adjudicated (every one is either
    RAN or NOT_APPLICABLE with a justification — the 0/1 certification).
`run_validity` is VALID / INVALID (A fails) / INCOMPLETE (B fails) — RECORD_ONLY
only if REQUIRED were emptied again.

Enforcement is by JUDGMENT, not yet by refusal: run_core records `run_validity`
on the artifact but does not (yet) hard-refuse an INVALID run. The non-bypassable
refuse-to-emit, and making the scaffolding layers' execution *measured* rather
than self-declared, are the remaining steps toward a fully enforced method.

Honesty of measurement: layers that EMIT findings are marked RAN from the DATA
(their `source_role` on the ledger), not from self-report — the model cannot lie
about them. Non-emitting layers (oracle, triage, governor, external_auditor)
still rely on the run's declared status, but it is now RECORDED and auditable.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum

# The canonical pipeline stages. Order is narrative, not priority.
DECLARED_LAYERS: tuple = (
    "triage", "oracle", "verifier", "reasoner", "propagator",
    "deep_causal", "external_auditor", "governor",
)

# Populated from measurement and CORRECTED by the round-18 ten-run consolidation.
# verifier + propagator emit in 10/10 runs across every class; triage/oracle/governor
# are the always-run scaffolding. reasoner (8/10) and deep_causal (7/10) turned out
# CONTEXTUAL — reasoner produced nothing in the two runs whose defects verifier+
# propagator already covered — so both are OPTIONAL, adjudicated per run.
# external_auditor (0/10) is independence-conditional. This corrected the round-15
# over-inclusion of reasoner that the smaller 5-run sample had wrongly frozen —
# exactly why the hard gate was not switched on until the minimum was consolidated.
REQUIRED_LAYERS: tuple = (
    "triage", "oracle", "verifier", "propagator", "governor",
)


class LayerStatus(str, Enum):
    RAN = "ran"                        # executed (emitting layers: measured from data)
    NOT_APPLICABLE = "not_applicable"  # legitimately skipped, with justification (B: 1)
    MISSING = "missing"                # neither ran nor justified — a silent gap


def _norm(s) -> str:
    return str(s or "").strip().lower().replace("-", "_").replace(" ", "_")


@dataclass
class LayerRecord:
    name: str
    status: LayerStatus = LayerStatus.MISSING
    findings: int = 0            # findings attributed to this layer (0 if non-emitting)
    measured: bool = False       # True ⇒ status came from data, not from self-report
    justification: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status.value,
                "findings": self.findings, "measured": self.measured,
                "justification": self.justification}


@dataclass
class RunManifest:
    artifact_name: str = ""
    artifact_class: str = ""     # e.g. "finance" | "paper" | "auction" — for cross-class measurement
    layers: dict = field(default_factory=dict)      # name -> LayerRecord
    specialists: dict = field(default_factory=dict)  # ad-hoc roles outside DECLARED_LAYERS -> count
    run_validity: str = "RECORD_ONLY"
    gaps: list = field(default_factory=list)

    def record(self, name, status, findings=0, measured=False, justification=""):
        self.layers[name] = LayerRecord(name=name, status=status, findings=findings,
                                        measured=measured, justification=justification)

    def evaluate(self) -> list:
        """Compute run_validity. Record-only until REQUIRED_LAYERS is populated."""
        self.gaps = []
        if not REQUIRED_LAYERS:
            self.run_validity = "RECORD_ONLY"
            return self.gaps
        missing_required = [n for n in REQUIRED_LAYERS
                            if self.layers.get(n, LayerRecord(n)).status == LayerStatus.MISSING]
        unadjudicated = [n for n, r in self.layers.items()
                         if r.status == LayerStatus.MISSING]
        if missing_required:
            self.run_validity = "INVALID"
            self.gaps = [f"REQUIRED layer missing (condition A): {n}" for n in missing_required]
        elif unadjudicated:
            self.run_validity = "INCOMPLETE"
            self.gaps = [f"layer un-adjudicated — neither RAN nor NOT_APPLICABLE-justified "
                         f"(condition B): {n}" for n in unadjudicated]
        else:
            self.run_validity = "VALID"
        return self.gaps

    def to_dict(self) -> dict:
        return {
            "artifact_name": self.artifact_name,
            "artifact_class": self.artifact_class,
            "run_validity": self.run_validity,
            "required_layers": list(REQUIRED_LAYERS),
            "gaps": self.gaps,
            "layers": {n: r.to_dict() for n, r in self.layers.items()},
            "specialists": dict(self.specialists),
        }


def _distinct_sources(ledger) -> set:
    out = set()
    for f in ledger.findings:
        for src in (getattr(f, "sources", []) or []):
            if src:
                out.add(str(src))
    return out


def build_manifest(ledger, execution: dict | None = None, *,
                   triage: dict | None = None, governor_ran: bool = False) -> RunManifest:
    """Build the manifest from the ledger (data) plus the run's declared
    `execution` block. Round-16 — the scaffolding layers are now MEASURED from
    their real outputs, not self-declared, and the triage decision optimizes the
    optional layers (one effort, two things counted):

      * governor — measured iff a meta verdict was produced (`governor_ran`);
      * oracle   — measured from the grounding it supplied: the distinct cited
                   sources across the findings;
      * triage   — measured from its decision record `triage`
                   ({"dimensions_present": [...], "deploy_roles": [...]}), and any
                   OPTIONAL layer NOT in `deploy_roles` is auto-marked
                   NOT_APPLICABLE ("not selected by triage") — a data-driven 0/1,
                   not a self-report, and the run does not waste an unselected layer.

    `execution` shape (fallback for whatever is not measured):
        {"artifact_class": "finance",
         "layers": {"external_auditor": {"status": "not_applicable",
                                         "justification": "single-vendor run"}}}
    """
    execution = execution or {}
    triage = triage or {}
    m = RunManifest(artifact_name=getattr(ledger, "artifact_name", ""),
                    artifact_class=str(execution.get("artifact_class", "")))

    counts = Counter(_norm(f.source_role) for f in ledger.findings
                     if getattr(f, "source_role", ""))
    declared = {_norm(k): (v or {}) for k, v in (execution.get("layers", {}) or {}).items()}

    dims = list(triage.get("dimensions_present") or [])
    deploy = {_norm(r) for r in (triage.get("deploy_roles") or [])}
    triage_measured = bool(dims or deploy)
    sources = _distinct_sources(ledger)

    for layer in DECLARED_LAYERS:
        n = counts.get(layer, 0)
        if n > 0:                                   # emitting: measured from data
            m.record(layer, LayerStatus.RAN, findings=n, measured=True)
            continue
        # measured scaffolding
        if layer == "triage" and triage_measured:
            m.record("triage", LayerStatus.RAN, findings=len(dims) or len(deploy),
                     measured=True); continue
        if layer == "oracle" and sources:
            m.record("oracle", LayerStatus.RAN, findings=len(sources), measured=True)
            continue
        if layer == "governor" and governor_ran:
            m.record("governor", LayerStatus.RAN, findings=0, measured=True); continue
        # An explicit declaration WINS over the triage deduction — it is more
        # informative (round-17 fix: external_auditor is NOT_APPLICABLE for
        # INDEPENDENCE, not merely because triage did not select it; the auto-rule
        # was overwriting that truer reason). Declared status first:
        d = declared.get(layer, {})
        st = _norm(d.get("status"))
        if st == "ran":
            m.record(layer, LayerStatus.RAN, findings=0,
                     justification=str(d.get("justification", ""))); continue
        if st in ("not_applicable", "na", "n_a"):
            m.record(layer, LayerStatus.NOT_APPLICABLE, findings=0,
                     justification=str(d.get("justification", ""))); continue
        # OPTIONAL layer with NO declaration that triage did not select -> data-driven
        # NOT_APPLICABLE. Never a REQUIRED layer (that stays MISSING -> INVALID).
        if deploy and layer not in REQUIRED_LAYERS and layer not in deploy:
            m.record(layer, LayerStatus.NOT_APPLICABLE, measured=True,
                     justification="not selected by triage"); continue
        m.record(layer, LayerStatus.MISSING)

    for role, n in counts.items():
        if role not in DECLARED_LAYERS:
            m.specialists[role] = n

    m.evaluate()
    return m
