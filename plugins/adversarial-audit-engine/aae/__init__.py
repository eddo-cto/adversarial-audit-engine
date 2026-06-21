"""
Adversarial Audit Engine (aae)
==============================

A software-engineered scaffold that orchestrates a hive of blind LLM "attacker"
roles to audit high-complexity artifacts, while CODE enforces the discipline
that seven adversarial test rounds proved matters:

  - a verdict state machine (pattern can flag, only reading can condemn),
  - a defense-gate (no condemnation without a recorded best-defense attempt),
  - coverage enforcement over a fixed dimension taxonomy,
  - per-class expected recall, with the conceptual-novel class routed to a
    human expert,
  - an independence block: never 'validated' on internal grounds alone.

The LLM is the semantic engine; this package is the deterministic scaffold.
"""

from .config import AuditConfig
from .llm import LLMClient, MockLLMClient, AnthropicLLMClient
from .orchestrator import Orchestrator, AuditResult, write_outputs
from .schema import (Ledger, Finding, Verdict, DefectClass, Posta,
                     IndependenceLevel)
from .triadic import TriadicLayer, TriadicResult, RivalHypothesis
from .construens import (ConstruensLayer, ConstruensResult, AbsenceCause,
                         AbsenceLabel, SurvivingFragment)
from .discovery import (DiscoveryLayer, DiscoveryResult, CandidateSpace,
                        PRIMITIVES, rebalance_weights)
from .deep_causal import (DeepCausalLayer, DeepCausalResult, RootCause,
                          ChiasmPrediction, Scenario)
from .meta_epistemic import (MetaGovernor, MetaAssessment, GovernorCheck,
                             ReliabilityVerdict)
from .adapters import (OpenAICompatibleClient, GeminiClient,
                       independence_level_between)

__version__ = "0.6.0"

__all__ = [
    "AuditConfig", "LLMClient", "MockLLMClient", "AnthropicLLMClient",
    "Orchestrator", "AuditResult", "write_outputs",
    "Ledger", "Finding", "Verdict", "DefectClass", "Posta", "IndependenceLevel",
    "TriadicLayer", "TriadicResult", "RivalHypothesis",
    "ConstruensLayer", "ConstruensResult", "AbsenceCause", "AbsenceLabel",
    "SurvivingFragment",
    "DiscoveryLayer", "DiscoveryResult", "CandidateSpace", "PRIMITIVES",
    "rebalance_weights",
    "DeepCausalLayer", "DeepCausalResult", "RootCause", "ChiasmPrediction",
    "Scenario",
    "MetaGovernor", "MetaAssessment", "GovernorCheck", "ReliabilityVerdict",
    "OpenAICompatibleClient", "GeminiClient", "independence_level_between",
]
