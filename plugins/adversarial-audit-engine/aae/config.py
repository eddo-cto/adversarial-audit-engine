"""config.py — Run configuration."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import Posta


@dataclass
class AuditConfig:
    artifact_path: str
    domain_hint: str = ""
    max_posta: Posta = Posta.HIGH          # default to the strict regime
    allow_web: bool = True
    external_review_identity: str | None = None  # set when an external eye ran
    primary_reachable: bool = True         # source-grade gate: False = no primary exists
                                           # for this artifact class (gate abstains)
    out_dir: str = "."
    max_tokens: int = 4096
    # deep layers. Explicit flags force them ON; otherwise they are AUTO-DEPLOYED
    # by stakes (G2): HIGH posta, or a conceptual-novel finding, warrants the deep
    # passes without the operator remembering to ask. The Freno still holds — on a
    # LOW/MEDIUM run with no conceptual-novel signal they stay off.
    enable_triadic: bool = False           # force deductive/inductive/abductive pass
    enable_construens: bool = False        # force cause-of-absence diagnosis
    enable_deep_causal: bool = False       # force root-clustering / chiasm / scenarios
    construens_idea: str = ""              # the idea/gap to diagnose (construens needs it)
    enable_meta: bool = True               # meta-epistemic governor (5th layer; on by default)
