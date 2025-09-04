from __future__ import annotations
import json, os, time, hashlib, getpass, socket, subprocess
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class ProvenanceRecord:
    timestamp: float
    actor: str
    host: str
    step: str
    params: dict[str, Any]
    inputs: list[str]
    outputs: list[str]
    code_version: str | None
    digest: str

class ProvenanceStore:
    def __init__(self, ledger_path: str) -> None:
        parent = os.path.dirname(ledger_path) or "."
        os.makedirs(parent, exist_ok=True)
        self.ledger_path = ledger_path

    def _code_version(self) -> str | None:
        try:
            out = subprocess.check_output(["git","rev-parse","HEAD"], stderr=subprocess.DEVNULL)
            return out.decode().strip()
        except Exception:
            return None

    def _digest(self, payload: dict[str, Any]) -> str:
        h = hashlib.sha256()
        h.update(json.dumps(payload, sort_keys=True, default=str).encode())
        return h.hexdigest()

    def log(self, step: str, params: dict[str, Any], inputs: list[str], outputs: list[str]) -> ProvenanceRecord:
        rec_base = {
            "timestamp": time.time(),
            "actor": getpass.getuser(),
            "host": socket.gethostname(),
            "step": step,
            "params": params,
            "inputs": inputs,
            "outputs": outputs,
            "code_version": self._code_version(),
        }
        digest = self._digest(rec_base)
        rec = ProvenanceRecord(**rec_base, digest=digest)
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec)) + "\n")
        return rec


