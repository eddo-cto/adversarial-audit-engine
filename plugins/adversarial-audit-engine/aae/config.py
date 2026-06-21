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
    out_dir: str = "."
    max_tokens: int = 4096
    # deep layers (adaptive; off by default to respect the Freno)
    enable_triadic: bool = False           # deductive/inductive/abductive pass
    enable_construens: bool = False        # cause-of-absence diagnosis
    construens_idea: str = ""              # the idea/gap to diagnose (construens)
    enable_meta: bool = True               # meta-epistemic governor (5th layer; on by default)
