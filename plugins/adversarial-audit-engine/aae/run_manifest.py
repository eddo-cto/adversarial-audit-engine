"""
run_manifest.py — the execution manifest (round 13, standardization step 2).

Purpose: make "a run" a checkable object with an execution contract, so the
"loses pieces" failure mode becomes impossible to hide. For each declared stage
it records RAN / NOT_APPLICABLE(justified) / MISSING.

This version RECORDS, it does not ENFORCE. `REQUIRED_LAYERS` is left EMPTY on
purpose: the minimum core must be POPULATED FROM MEASUREMENT (which layers
actually earn their keep across artifact classes), not assumed from the current
module sprawl. Freezing an unmeasured minimum is the one misstep to avoid. While
`REQUIRED_LAYERS` is empty, `run_validity` is always RECORD_ONLY.

The A+B rule the manifest will eventually enforce, once REQUIRED is populated:
  * condition A — no REQUIRED layer is MISSING;
  * condition B — no declared layer is left un-adjudicated (every one is either
    RAN or NOT_APPLICABLE with a justification — the 0/1 certification).
`run_validity` then becomes VALID / INVALID (A fails) / INCOMPLETE (B fails).

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

# Populated ONLY after cross-class measurement. Empty ⇒ record-only (no gate).
REQUIRED_LAYERS: tuple = ()


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


def build_manifest(ledger, execution: dict | None = None) -> RunManifest:
    """Build the manifest from the ledger (data) plus the run's declared
    `execution` block (for non-emitting layers). `execution` shape:
        {"artifact_class": "finance",
         "layers": {"oracle": {"status": "ran"},
                    "external_auditor": {"status": "not_applicable",
                                         "justification": "single-vendor run"}}}
    """
    execution = execution or {}
    m = RunManifest(artifact_name=getattr(ledger, "artifact_name", ""),
                    artifact_class=str(execution.get("artifact_class", "")))

    counts = Counter(_norm(f.source_role) for f in ledger.findings
                     if getattr(f, "source_role", ""))
    declared = {_norm(k): (v or {}) for k, v in (execution.get("layers", {}) or {}).items()}

    for layer in DECLARED_LAYERS:
        n = counts.get(layer, 0)
        if n > 0:
            # measured from data — the model cannot lie about an emitting layer
            m.record(layer, LayerStatus.RAN, findings=n, measured=True)
            continue
        d = declared.get(layer, {})
        st = _norm(d.get("status"))
        if st == "ran":
            m.record(layer, LayerStatus.RAN, findings=0,
                     justification=str(d.get("justification", "")))
        elif st in ("not_applicable", "na", "n_a"):
            m.record(layer, LayerStatus.NOT_APPLICABLE, findings=0,
                     justification=str(d.get("justification", "")))
        else:
            m.record(layer, LayerStatus.MISSING)

    for role, n in counts.items():
        if role not in DECLARED_LAYERS:
            m.specialists[role] = n

    m.evaluate()
    return m
