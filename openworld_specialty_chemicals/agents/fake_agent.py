from __future__ import annotations

from typing import Dict, Iterable, List

from .base import AdviceAgent


class FakeAdviceAgent(AdviceAgent):
    def advise(self, alerts: Iterable[Dict]) -> Dict[str, object]:
        species = sorted({a.get("species", "") for a in alerts if isinstance(a, dict)})
        actions: List[str] = [f"Increase sorbent dosage for {s}" for s in species if s]
        if not actions:
            actions = ["Check process"]
        rationale = "Deterministic recommendations based on species in alerts."
        return {"actions": actions, "rationale": rationale}


