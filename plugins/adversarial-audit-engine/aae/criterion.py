"""
criterion.py — explicit, tunable decision criterion (the engine owns beta).

Estesia transduction §15-A: the LLM auditor should report a GRADED suspicion score
(0-100), and the ENGINE — not the model — owns the condemn/abstain/holds thresholds.
This separates *sensitivity* (the graded evidence the model produces) from *criterion*
(how much evidence we demand before acting), in software. It turns abstention into an
explicit BAND, gives a single precision/recall dial, and enforces the OCR trust contract
(an OCR-sourced score may never reach 'condemn').

Stdlib only, deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CriterionConfig:
    condemn_at: float = 80.0      # score >= this -> condemn (only if trust allows)
    abstain_at: float = 40.0      # score in [abstain_at, condemn_at) -> needs_reading
    # below abstain_at -> holds. Move these to slide precision<->recall.


@dataclass
class Decision:
    band: str                     # "condemn" | "needs_reading" | "holds"
    score: float
    reason: str


def decide(score: float, source_trust: str = "high",
           posta: str = "medium", cfg: CriterionConfig | None = None) -> Decision:
    """Map a graded suspicion score to a verdict band, with explicit criterion.

    - source_trust not in (high,None)  -> OCR/uncertain: cap at 'needs_reading' (never condemn).
    - posta 'high' (high stakes)        -> lower the abstain entry by 10 pts (more cautious:
      route more to human). posta 'low' -> raise it by 10 (let small stuff pass).
    The criterion (thresholds) is OWNED HERE and tunable; the model only supplies `score`.
    """
    cfg = cfg or CriterionConfig()
    s = max(0.0, min(100.0, float(score)))
    abstain_at = cfg.abstain_at + (-10.0 if posta == "high" else (10.0 if posta == "low" else 0.0))
    ocr = source_trust not in ("high", None)

    if s >= cfg.condemn_at:
        if ocr:
            return Decision("needs_reading", s,
                            f"score {s:.0f} >= condemn {cfg.condemn_at:.0f} MA fonte OCR "
                            "(trust ridotta) -> verifica umana, mai condanna strict")
        return Decision("condemn", s, f"score {s:.0f} >= criterio di condanna {cfg.condemn_at:.0f}")
    if s >= abstain_at:
        return Decision("needs_reading", s,
                        f"score {s:.0f} in banda d'astensione [{abstain_at:.0f},{cfg.condemn_at:.0f}) "
                        f"(posta={posta}) -> verifica umana")
    return Decision("holds", s, f"score {s:.0f} < soglia d'astensione {abstain_at:.0f}")
