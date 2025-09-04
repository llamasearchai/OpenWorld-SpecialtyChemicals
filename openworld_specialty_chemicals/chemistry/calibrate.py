from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from scipy.optimize import curve_fit
from .sorption_decay import SorptionDecayParams, predict_concentration

@dataclass
class FitResult:
    params: SorptionDecayParams
    rmse: float

def _model(t, Kd, k, V_m3, m_solid_kg, C0):
    p = SorptionDecayParams(Kd_L_per_kg=Kd, k_per_h=k, V_m3=V_m3, m_solid_kg=m_solid_kg)
    return predict_concentration(t, C0, p)

def fit_sorption_decay(t_h: np.ndarray, C_mgL: np.ndarray, V_m3: float, m_solid_kg: float) -> FitResult:
    t = np.asarray(t_h, dtype=float)
    C = np.asarray(C_mgL, dtype=float)
    C0 = float(C[0])
    # Bounds to keep parameters physical
    popt, _ = curve_fit(lambda tt, Kd, k: _model(tt, Kd, k, V_m3, m_solid_kg, C0),
                        t, C, p0=[0.1, 0.01], bounds=([0.0, 0.0], [10.0, 1.0]))
    Kd, k = popt
    params = SorptionDecayParams(Kd_L_per_kg=float(Kd), k_per_h=float(k), V_m3=float(V_m3), m_solid_kg=float(m_solid_kg))
    rmse = float(np.sqrt(np.mean((C - predict_concentration(t, C0, params))**2)))
    return FitResult(params=params, rmse=rmse)


