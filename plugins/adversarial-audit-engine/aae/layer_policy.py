"""layer_policy.py — deterministic policy for WHEN the deep-causal layer is warranted.

A1. The 10-run measurement classified deep_causal as CONTEXTUAL (it ran 7/10, produced nothing in 3/10):
so a blanket "always on HIGH posta" contradicts the data, and "the agent decides" is not measurable. The
honest middle is a deterministic STRUCTURAL trigger: deep-causal clusters roots ACROSS findings, so it
pays only when there is structure to cluster. It is warranted when the run carries stakes AND has
something to cluster:

    HIGH posta  AND  ( a conceptual-novel finding
                       OR  >= DEEP_CAUSAL_MIN_FINDINGS findings
                       OR  >= 2 findings sharing a taxonomy cell (a candidate common root) )

On a small, sparse run (e.g. 3 unrelated findings) it is NOT warranted — matching both the measurement
and what a competent auditor did on a short document. Used on BOTH entry points: the orchestrator to
auto-deploy, and `pipeline.discipline` to ENFORCE (a warranted-but-absent deep-causal is flagged, so it
cannot be silently skipped on the product path).

DEEP_CAUSAL_MIN_FINDINGS is a HYPOTHESIS until measured; the MECHANISM (structural trigger) is the
principled part. Keep it a named, tunable constant.
"""
from __future__ import annotations

from collections import Counter

from .schema import Posta, DefectClass

DEEP_CAUSAL_MIN_FINDINGS = 5   # hypothesis: below this, clustering is noise. Tune with data.


def deep_causal_warranted(findings, max_posta, min_findings: int = DEEP_CAUSAL_MIN_FINDINGS) -> bool:
    """Deterministic. `findings` is a list of Finding objects (both entry points hold parsed Findings
    by the time this is called). `max_posta` is a Posta."""
    if max_posta != Posta.HIGH:
        return False
    if not findings:
        return False
    if any(getattr(f, "defect_class", None) == DefectClass.NON_LOCAL_CONCEPTUAL_NOVEL for f in findings):
        return True
    if len(findings) >= min_findings:
        return True
    cells = Counter(getattr(f, "taxonomy_cell", None) for f in findings)
    return any(n >= 2 for n in cells.values())
