from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class SampleLineage:
    timestamp: float
    sample_id: str
    source: str
    species: str
    method: str
    calibration: Dict[str, Any]
    file: str
    digest: str

class LineageStore:
    def __init__(self, ledger_path: str) -> None:
        parent = os.path.dirname(ledger_path) or "."
        os.makedirs(parent, exist_ok=True)
        self.ledger_path = ledger_path

    def _digest(self, obj: dict) -> str:
        import json
        h = hashlib.sha256()
        h.update(json.dumps(obj, sort_keys=True, default=str).encode())
        return h.hexdigest()

    def log_sample(
        self,
        sample_id: str,
        source: str,
        species: str,
        method: str,
        calibration: Dict[str, Any],
        file: str
    ) -> SampleLineage:
        base = {
            "timestamp": time.time(),
            "sample_id": sample_id,
            "source": source,
            "species": species,
            "method": method,
            "calibration": calibration,
            "file": file,
        }
        rec = SampleLineage(**base, digest=self._digest(base))
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec)) + "\n")
        return rec


