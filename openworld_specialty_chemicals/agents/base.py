from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable


class AdviceAgent(ABC):
    @abstractmethod
    def advise(self, alerts: Iterable[Dict]) -> Dict[str, object]:
        """Return {actions: List[str], rationale: str} based on alerts."""
        raise NotImplementedError


