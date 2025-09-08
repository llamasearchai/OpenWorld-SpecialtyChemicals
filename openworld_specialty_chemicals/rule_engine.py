from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np


@dataclass
class Alert:
    species: str
    type: str   # 'exceedance' | 'trend'
    level: str  # 'info' | 'watch' | 'warning' | 'critical'
    value: float
    limit: float
    action: str

def rolling_mean(x: np.ndarray, w: int) -> np.ndarray:
    if w <= 1:
        return x
    c = np.convolve(x, np.ones(w), "valid") / w
    pad = np.full(w-1, c[0])
    return np.concatenate([pad, c])

def evaluate_permit(df, permit: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []

    # Handle both column format styles: species columns (SO4_mgL) and
    # tidy format (species, concentration)
    limits = permit.get("limits_mgL", permit.get("limits", {}))
    window = int(permit.get("rolling_window", 3))
    actions = permit.get("actions", {})

    # If tidy format (species, concentration columns), convert to wide format
    if "species" in df.columns and "concentration" in df.columns:
        # Group by species and use the last few readings per species
        for sp, limit in limits.items():
            species_data = df[df["species"] == sp].copy()
            if species_data.empty:
                continue

            # Get time series for this species
            concentrations = species_data["concentration"].to_numpy(dtype=float)
            times = species_data.get("time", range(len(concentrations))).to_numpy()

            if len(concentrations) == 0:
                continue

            # Current exceedance check
            current_val = concentrations[-1]
            if current_val > float(limit):
                severity = _get_severity(current_val, float(limit))
                alerts.append({
                    "time": float(times[-1]) if len(times) > 0 else 0.0,
                    "species": sp,
                    "type": "exceedance",
                    "level": severity,
                    "value": float(current_val),
                    "limit": float(limit),
                    "action": actions.get(sp, f"Review {sp} treatment process"),
                    "message": f"{sp} concentration {current_val:.3f} mg/L exceeds "
                    f"limit {float(limit):.3f} mg/L"
                })

            # Rolling mean trend check
            if len(concentrations) >= window:
                rm = rolling_mean(concentrations, window)
                trend_val = rm[-1]
                if trend_val > float(limit):
                    severity = _get_severity(trend_val, float(limit))
                    alerts.append({
                        "time": float(times[-1]) if len(times) > 0 else 0.0,
                        "species": sp,
                        "type": "trend",
                        "level": severity,
                        "value": float(trend_val),
                        "limit": float(limit),
                        "action": actions.get(sp, f"Review {sp} treatment process"),
                        "message": f"{sp} rolling mean {trend_val:.3f} mg/L over "
                        f"{window} readings exceeds limit {float(limit):.3f} mg/L"
                    })
    else:
        # Wide format with species-specific columns (e.g., SO4_mgL, As_mgL)
        for sp, limit in limits.items():
            col = f"{sp}_mgL"
            if col not in df.columns:
                continue

            x = df[col].to_numpy(dtype=float)
            if len(x) == 0:
                continue

            # Current exceedance
            if x[-1] > float(limit):
                severity = _get_severity(x[-1], float(limit))
                alerts.append({
                    "time": len(x) - 1,  # Use row index as time if no time column
                    "species": sp,
                    "type": "exceedance",
                    "level": severity,
                    "value": float(x[-1]),
                    "limit": float(limit),
                    "action": actions.get(sp, f"Review {sp} treatment process"),
                    "message": f"{sp} concentration {x[-1]:.3f} mg/L exceeds "
                    f"limit {float(limit):.3f} mg/L"
                })

            # Rolling mean trend
            if len(x) >= window:
                rm = rolling_mean(x, window)
                if rm[-1] > float(limit):
                    severity = _get_severity(rm[-1], float(limit))
                    alerts.append({
                        "time": len(x) - 1,
                        "species": sp,
                        "type": "trend",
                        "level": severity,
                        "value": float(rm[-1]),
                        "limit": float(limit),
                        "action": actions.get(sp, f"Review {sp} treatment process"),
                        "message": f"{sp} rolling mean {rm[-1]:.3f} mg/L over "
                        f"{window} readings exceeds limit {float(limit):.3f} mg/L"
                    })

    return alerts

def _get_severity(value: float, limit: float) -> str:
    """Determine alert severity based on how much the value exceeds the limit."""
    ratio = value / limit
    if ratio >= 2.0:
        return "critical"
    elif ratio >= 1.5:
        return "warning"
    elif ratio >= 1.25:
        return "watch"
    elif ratio >= 1.0:
        return "info"
    else:
        return "info"


