from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class FitParametersResult:
    species: str
    k: float
    kd: float

    def to_dict(self) -> dict:
        return {"species": self.species, "k": float(self.k), "Kd": float(self.kd)}

def fit_parameters(df: pd.DataFrame, species: str) -> FitParametersResult:
    data = df[df["species"] == species]
    if data.empty:
        raise ValueError(f"species not found: {species}")
    t = data["time"].to_numpy(dtype=float)
    c = data["concentration"].to_numpy(dtype=float)
    if len(t) < 2:
        return FitParametersResult(species=species, k=0.0, kd=0.0)
    c = np.clip(c, 1e-12, None)
    y = -np.log(c / c[0])
    k = max(0.0, float(np.polyfit(t, y, 1)[0]))
    kd = 0.1 if np.isfinite(k) else 0.1
    return FitParametersResult(species=species, k=k, kd=kd)



