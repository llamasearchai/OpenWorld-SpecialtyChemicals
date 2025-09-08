from __future__ import annotations

import json
import os
from typing import Any, Dict

DEFAULT_PERMIT = {
    "limits_mgL": {
        "SO4": 250.0,
        "As": 0.01,
        "Ni": 0.1,
    },
    "rolling_window": 3,
    "actions": {
        "SO4": "Increase lime dosing; verify gypsum precipitation; reduce discharge rate.",
        "As": "Adjust pH to 7-8; add ferric coagulant; check filter performance.",
        "Ni": "Increase ion exchange cycle; ensure resin regeneration; check chelation dosing.",
    }
}

def load_permit(path: str | None) -> Dict[str, Any]:
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_PERMIT


