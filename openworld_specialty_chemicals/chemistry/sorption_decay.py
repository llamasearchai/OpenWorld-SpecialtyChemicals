from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class SorptionDecayParams:
    Kd_L_per_kg: float   # linear isotherm coefficient
    k_per_h: float       # first-order decay rate (1/h)
    V_m3: float          # reactor volume (m^3)
    m_solid_kg: float    # mass of solids (kg)

def effective_rate(params: SorptionDecayParams) -> float:
    """
    For batch reactor with linear sorption:
    Total capacity factor: phi = V + m_solid * Kd (treating units consistent with mg/L, L, kg).
    Effective decay on aqueous concentration:
    \[ dC/dt = - (k * V / (V + m_solid * Kd)) C \]
    """
    V_L = params.V_m3 * 1000.0  # convert m^3 to L
    phi_L = V_L + params.m_solid_kg * params.Kd_L_per_kg
    return params.k_per_h * (V_L / max(1e-9, phi_L))

def predict_concentration(t_h: np.ndarray, C0_mgL: float, params: SorptionDecayParams) -> np.ndarray:
    keff = effective_rate(params)
    return C0_mgL * np.exp(-keff * t_h)


