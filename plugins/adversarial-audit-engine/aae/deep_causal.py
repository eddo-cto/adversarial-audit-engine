"""
deep_causal.py — Deep-causal layer: root clustering, chiasm cross-validation,
gated scenario diffusion.

Stripped of the metaphor ("karst" / "chiasm" / "error-diffuser"), three concrete
operations, each tested on the Raft case:

  1. ROOT CLUSTERING ("karst"): surface findings are often resurfacings of a few
     deep generative causes. Collapse findings to root causes (a root is the
     deep premise that, if fixed, resolves several surface defects). On Raft this
     correctly collapsed the A_cluster=A_nodo cluster (3 findings -> 1 root) and
     the clock-drift cluster (2 -> 1).

  2. CHIASM cross-validation: for each root found backward (symptoms -> root),
     propagate FORWARD (root -> predicted symptoms) and surface symptoms that
     should exist but are not yet in the finding list. A prediction is kept only
     if it carries a discriminating test (the anchoring gate). On Raft this
     recovered real withheld defects -> recall gain.

  3. SCENARIO DIFFUSION (gated): generate possible failure scenarios. A scenario
     is ADMITTED only if (a) mechanistically reachable from the text AND
     (b) falsifiable (states the discriminating test). Otherwise rejected. On
     Raft it correctly rejected a correct-behavior scenario and a non-falsifiable
     one -> false-positive discipline holds.

The gates are enforced in CODE (not left to the prompt): a prediction without a
discriminating test is dropped; a scenario not (anchored AND falsifiable) is
rejected. Deploy adaptively on artifacts with rich causal structure. Does NOT
move the ultimate limit: it traces KNOWN mechanisms to roots and predicts
anchorable symptoms; a genuinely novel mechanism stays with the human expert.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .llm import LLMClient


@dataclass
class RootCause:
    id: str
    name: str
    description: str
    generated_findings: list[str] = field(default_factory=list)


@dataclass
class ChiasmPrediction:
    id: str
    from_root: str
    predicted_symptom: str
    location: str = ""
    why_follows: str = ""
    discriminating_test: str = ""
    kept: bool = False

    def evaluate_gate(self) -> bool:
        """Anchoring gate: a forward prediction is kept only if it states the
        test that would confirm/refute it (else it is speculation)."""
        self.kept = bool(self.discriminating_test.strip())
        return self.kept


@dataclass
class Scenario:
    id: str
    mechanism: str
    reachable: bool = False        # mechanistically reachable from the text
    falsifiable: bool = False      # states a discriminating test/condition
    discriminating_test: str = ""
    admitted: bool = False
    reason: str = ""

    def evaluate_gate(self) -> bool:
        """Admitted only if reachable AND falsifiable."""
        self.admitted = self.reachable and self.falsifiable and \
            bool(self.discriminating_test.strip())
        if not self.admitted and not self.reason:
            if not self.reachable:
                self.reason = "not mechanistically reachable from the text"
            elif not (self.falsifiable and self.discriminating_test.strip()):
                self.reason = "not falsifiable (no discriminating test)"
        return self.admitted


@dataclass
class DeepCausalResult:
    roots: list[RootCause] = field(default_factory=list)
    predictions: list[ChiasmPrediction] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)

    @property
    def kept_predictions(self) -> list[ChiasmPrediction]:
        return [p for p in self.predictions if p.kept]

    @property
    def admitted_scenarios(self) -> list[Scenario]:
        return [s for s in self.scenarios if s.admitted]

    def summary(self) -> str:
        return ("deep-causal: "
                f"roots={len(self.roots)} (collapsing "
                f"{sum(len(r.generated_findings) for r in self.roots)} findings); "
                f"chiasm predictions kept={len(self.kept_predictions)}/"
                f"{len(self.predictions)}; "
                f"scenarios admitted={len(self.admitted_scenarios)}/"
                f"{len(self.scenarios)}")


_CLUSTER_SYS = (
    "ROOT-CAUSE CLUSTERING. Given an artifact and a list of surface findings, "
    "collapse them into a small set of ROOT CAUSES (deep premises that, if fixed, "
    "resolve several findings). Return JSON {\"roots\":[{id,name,description,"
    "generated_findings:[finding-refs]}]}."
)
_CHIASM_SYS = (
    "CHIASM CROSS-VALIDATION. For each root cause, propagate FORWARD into the "
    "artifact and predict ADDITIONAL symptoms that should exist but are NOT in "
    "the given finding list. Each prediction MUST state the discriminating test "
    "that would confirm/refute it. Return JSON {\"predictions\":[{id,from_root,"
    "predicted_symptom,location,why_follows,discriminating_test}]}."
)
_SCENARIO_SYS = (
    "SCENARIO DIFFUSION (gated). Generate possible failure scenarios. For each, "
    "set reachable=true only if mechanistically reachable from the text, and "
    "falsifiable=true only if you give a discriminating test. Return JSON "
    "{\"scenarios\":[{id,mechanism,reachable,falsifiable,discriminating_test}]}."
)


class DeepCausalLayer:
    def __init__(self, client: LLMClient):
        self.client = client

    def run(self, artifact: str, findings: list[str]) -> DeepCausalResult:
        flist = "\n".join(f"- {f}" for f in findings)
        base = f"ARTIFACT:\n{artifact}\n\nFINDINGS:\n{flist}"
        res = DeepCausalResult()

        cl = self._json(_CLUSTER_SYS, base)
        for r in (cl.get("roots", []) if isinstance(cl, dict) else []):
            if isinstance(r, dict) and r.get("name"):
                res.roots.append(RootCause(
                    id=str(r.get("id") or "CR-?"), name=str(r.get("name")),
                    description=str(r.get("description", "")),
                    generated_findings=list(r.get("generated_findings", []) or [])))

        roots_txt = "\n".join(f"{r.id}: {r.name} — {r.description}" for r in res.roots)
        ch = self._json(_CHIASM_SYS, base + "\n\nROOT CAUSES:\n" + roots_txt)
        for p in (ch.get("predictions", []) if isinstance(ch, dict) else []):
            if isinstance(p, dict) and p.get("predicted_symptom"):
                pred = ChiasmPrediction(
                    id=str(p.get("id") or "P-?"),
                    from_root=str(p.get("from_root", "")),
                    predicted_symptom=str(p.get("predicted_symptom")),
                    location=str(p.get("location", "")),
                    why_follows=str(p.get("why_follows", "")),
                    discriminating_test=str(p.get("discriminating_test", "")))
                pred.evaluate_gate()
                res.predictions.append(pred)

        sc = self._json(_SCENARIO_SYS, base)
        for s in (sc.get("scenarios", []) if isinstance(sc, dict) else []):
            if isinstance(s, dict) and s.get("mechanism"):
                scen = Scenario(
                    id=str(s.get("id") or "S-?"), mechanism=str(s.get("mechanism")),
                    reachable=bool(s.get("reachable", False)),
                    falsifiable=bool(s.get("falsifiable", False)),
                    discriminating_test=str(s.get("discriminating_test", "")))
                scen.evaluate_gate()
                res.scenarios.append(scen)
        return res

    def _json(self, system: str, user: str):
        try:
            return self.client.complete_json(system, user, max_tokens=3072)
        except ValueError:
            return {}
