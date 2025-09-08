from __future__ import annotations

import os
from dataclasses import dataclass


def _env(key: str, default: str | None = None) -> str | None:
    v = os.getenv(key)
    return v if v is not None else default

@dataclass(frozen=True)
class Settings:
    data_dir: str = _env("OW_SC_DATA_DIR", "./data") or "./data"
    artifacts_dir: str = _env("OW_SC_ARTIFACTS_DIR", "./artifacts") or "./artifacts"
    provenance_ledger: str = (
        _env("OW_SC_PROVENANCE_LEDGER", "./provenance/ledger.jsonl")
        or "./provenance/ledger.jsonl"
    )
    lineage_ledger: str = (
        _env("OW_SC_LINEAGE_LEDGER", "./lineage/samples.jsonl")
        or "./lineage/samples.jsonl"
    )

settings = Settings()


