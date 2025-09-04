from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd


def _severity(value: float, limit: float) -> str:
    if value >= 1.25 * limit:
        return "critical"
    if value >= 1.05 * limit:
        return "warning"
    if value >= limit:
        return "watch"
    return "info"

def check_permit(df: pd.DataFrame, permit: Dict[str, Any]) -> List[Dict[str, Any]]:
    limits = permit.get("limits", {})
    window = int(permit.get("rolling_window", 3))
    alerts: List[Dict[str, Any]] = []
    for sp, limit in limits.items():
        rows = df[df["species"] == sp].copy()
        if rows.empty:
            continue
        last = rows.iloc[-1]
        val = float(last["concentration"])
        if val > float(limit):
            alerts.append({
                "time": float(last["time"]),
                "species": sp,
                "value": val,
                "limit": float(limit),
                "level": _severity(val, float(limit)),
                "message": f"{sp} instantaneous {val:.3f} exceeds limit {float(limit):.3f}",
            })
        # Rolling mean trend alert
        try:
            rm = rows["concentration"].rolling(window=window, min_periods=window).mean()
            if len(rm) and not rm.dropna().empty:
                last_rm = float(rm.iloc[-1])
                if last_rm > float(limit):
                    alerts.append({
                        "time": float(rows.iloc[-1]["time"]),
                        "species": sp,
                        "value": last_rm,
                        "limit": float(limit),
                        "level": _severity(last_rm, float(limit)),
                        "message": f"{sp} rolling mean {last_rm:.3f} over window {window} exceeds limit {float(limit):.3f}",
                    })
        except Exception:
            pass
    return alerts


def suggest_remediation(alerts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    suggestions: List[Dict[str, str]] = []
    for a in alerts:
        sp = a.get("species", "")
        if sp == "SO4":
            s = "Increase lime dosing; verify gypsum precipitation; reduce discharge rate."
        elif sp == "As":
            s = "Adjust pH to 7-8; add ferric coagulant; check filter performance."
        elif sp == "Ni":
            s = "Increase ion exchange cycle; ensure resin regeneration; check chelation dosing."
        else:
            s = "Increase treatment intensity; verify dosing and filtration; reassess setpoints."
        suggestions.append({"species": sp, "suggestion": s})
    return suggestions
