"""
sealed_labels.py — the ONLY module allowed to read hold-out labels (the M/G separation, in code).

The invariant (brief §1.7): nothing that OPTIMIZES may read G, the hold-out labels, or metrics derived from
them. Enforced here, not by convention: a caller that declares itself an optimizer (env AAE_SELFTEST_ROLE=
optimizer, or passes optimizer=True) is refused with a LeakError. A test asserts the refusal, so an optimizer
path that reaches the labels fails loudly.
"""
from __future__ import annotations

import os


class LeakError(RuntimeError):
    """Raised when an optimizer tries to read sealed hold-out labels."""


def _is_optimizer(optimizer: bool | None) -> bool:
    if optimizer:
        return True
    return os.environ.get("AAE_SELFTEST_ROLE", "").strip().lower() == "optimizer"


def read_holdout_labels(cases: list[dict], split: dict, *, optimizer: bool | None = None) -> dict:
    """Return {case_id: label} for the hold-out cases ONLY. Raises LeakError if the caller is an optimizer."""
    if _is_optimizer(optimizer):
        raise LeakError("an optimizer may not read hold-out labels (M/G separation)")
    hold = set(split.get("holdout", []))
    return {c["id"]: c["label"] for c in cases if c["id"] in hold}


def read_holdout_defects(cases: list[dict], split: dict, *, optimizer: bool | None = None) -> dict:
    """Return {case_id: defects} for hold-out cases ONLY (for scoring G). Same seal."""
    if _is_optimizer(optimizer):
        raise LeakError("an optimizer may not read hold-out defects (M/G separation)")
    hold = set(split.get("holdout", []))
    return {c["id"]: c.get("defects", []) for c in cases if c["id"] in hold}
