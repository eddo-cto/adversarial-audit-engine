"""
dedup.py — Cross-agent deduplication.

Hostile rounds showed heavy overlap: the same defect found by 3-5 roles. That
redundancy is cross-confirmation, but the ledger should carry one entry per
defect with the roles that corroborated it. We deduplicate by a cheap textual
signature (no embedding dependency); a real deployment can swap in embeddings.
"""

from __future__ import annotations

import re
from collections import defaultdict

from .schema import Finding


_WORD = re.compile(r"[a-zA-Z0-9§]+")


def _signature(f: Finding) -> str:
    """A coarse signature: sorted significant tokens of the cited sections +
    the element text. Two findings about the same sections/element collapse."""
    sections = " ".join(sorted(f.accusation.sections))
    text = f"{sections} {f.element}".lower()
    tokens = [t for t in _WORD.findall(text) if len(t) > 2]
    # keep the most distinctive tokens, order-independent
    return " ".join(sorted(set(tokens)))


def deduplicate(findings: list[Finding]) -> tuple[list[Finding], dict[str, list[str]]]:
    """Collapse near-duplicate findings. Returns (unique_findings,
    corroboration map id->[role,...]). The kept finding is the one with the
    most severe verdict / most evidence; the rest become corroborations."""
    groups: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        groups[_signature(f)].append(f)

    severity_rank = {
        "accusa_vince": 4, "conteso": 3, "accusa_ridimensionata": 2,
        "da_leggere": 1, "artefatto_regge": 0, "pending": 0,
    }

    unique: list[Finding] = []
    corroboration: dict[str, list[str]] = {}
    for sig, group in groups.items():
        # pick the representative: highest verdict severity, then most sources
        rep = max(group, key=lambda g: (severity_rank.get(g.verdict.value, 0),
                                        len(g.sources),
                                        len(g.accusation.evidence)))
        roles = sorted({g.source_role for g in group if g.source_role})
        corroboration[rep.id] = roles
        unique.append(rep)
    return unique, corroboration
