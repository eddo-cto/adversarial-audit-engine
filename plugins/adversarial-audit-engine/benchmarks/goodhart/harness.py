"""
harness.py — the RUNNER of the Goodhart step-2 adversarial loop.

Pure orchestration: it wires three PLUGGABLE producers into the observation tuples that analysis.py
turns into the pre-registered decision. The three producers are protocols (duck-typed); the real,
LLM-driven ones are separate adapters (forger #118, gold #119, engine-auditor). This module has NO
engine dependency and is stdlib only, so the loop logic is testable in isolation with deterministic mocks.

The loop, per ablation cell and per pressure level p, repeated K times:
    artifact = forger.forge(p, feedback)      # forger adapts to feedback (rising p = more pressure)
    gold     = gold.label(artifact)           # INDEPENDENT ground truth, computed outside the engine
    cleared  = auditor.audit(artifact, cell)  # the engine under this ablation config; True = not condemned
    record   {cell, pressure, gold, cleared}

INVARIANTS enforced here (the anti-circularity guards from the protocol):
  * the forger's feedback contains ONLY the auditor verdict (`cleared`), NEVER the gold label — the gold
    is hidden from the attacker;
  * the gold is asked independently of the auditor (neither sees the other's output);
  * nothing here adjudicates or scores — it only produces tuples. Analysis is elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Iterable

from analysis import PRESSURE_LEVELS, K_PER_CELL_PRESSURE, N_SEEDS


@dataclass(frozen=True)
class AblationCell:
    """One configuration of the defences to be ablated (the 'science mode' toggles)."""
    name: str
    eye: bool = True            # cross-vendor external eye ON/OFF (independence 3 vs 1)
    axes: bool = True           # orthogonal-axis multiplexing (all roles) ON/OFF
    governor: bool = True       # non-self-certifying governor ON/OFF
    eye_mode: str = "cross_vendor"   # 'cross_vendor' (real diversity) or 'cross_seed' (H2 placebo)


# the pre-registered ablation set (see GOODHART_step2_protocollo.md §6)
DEFAULT_CELLS: tuple[AblationCell, ...] = (
    AblationCell("defenses_off", eye=False, axes=False, governor=False),
    AblationCell("defenses_on",  eye=True,  axes=True,  governor=True),
    AblationCell("cross_vendor", eye=True,  axes=True,  governor=True, eye_mode="cross_vendor"),
    AblationCell("cross_seed",   eye=True,  axes=True,  governor=True, eye_mode="cross_seed"),
)


class Gold(Protocol):
    def label(self, artifact: Any) -> str: ...        # "VALID" | "INVALID"


class Auditor(Protocol):
    def audit(self, artifact: Any, cell: AblationCell) -> bool: ...   # True == CLEARED (not condemned)


class Forger(Protocol):
    def forge(self, pressure: int, feedback: list[dict]) -> Any: ...  # adapts to prior verdicts


def run_cell(forger: Forger, gold: Gold, auditor: Auditor, cell: AblationCell, *,
             pressure_levels: Iterable[int] = PRESSURE_LEVELS,
             k: int = K_PER_CELL_PRESSURE) -> list[dict]:
    """Run one ablation cell across the pressure levels. Returns the observation tuples.
    The forger receives ONLY `{"cleared": bool}` feedback — never the gold (anti-leak invariant)."""
    recs: list[dict] = []
    feedback: list[dict] = []
    for p in pressure_levels:
        for _ in range(k):
            artifact = forger.forge(p, feedback)
            gold_label = str(gold.label(artifact)).upper()          # independent ground truth
            cleared = bool(auditor.audit(artifact, cell))           # engine under this ablation
            recs.append({"cell": cell.name, "pressure": int(p),
                         "gold": gold_label, "cleared": cleared})
            feedback.append({"cleared": cleared})                   # verdict ONLY — gold stays hidden
    return recs


def run_experiment(make_forger, gold: Gold, auditor: Auditor,
                   cells: Iterable[AblationCell] = DEFAULT_CELLS, *,
                   seeds: Iterable[int] = range(N_SEEDS)) -> list[dict]:
    """Full experiment: independent seeds × ablation cells. `make_forger(seed)` returns a fresh forger
    per seed (independence between runs). Aggregates all observation tuples for analysis.py."""
    recs: list[dict] = []
    for s in seeds:
        for cell in cells:
            recs.extend(run_cell(make_forger(s), gold, auditor, cell))
    return recs
