import numpy as np

from openworld_specialty_chemicals.chemistry.sorption_decay import (
    SorptionDecayParams,
    effective_rate,
    predict_concentration,
)


def test_effective_rate_monotonic_with_Kd():
    p1 = SorptionDecayParams(Kd_L_per_kg=0.0, k_per_h=0.02, V_m3=10.0, m_solid_kg=50.0)
    p2 = SorptionDecayParams(Kd_L_per_kg=1.0, k_per_h=0.02, V_m3=10.0, m_solid_kg=50.0)
    assert effective_rate(p2) < effective_rate(p1)

def test_predict_concentration_decreases():
    p = SorptionDecayParams(Kd_L_per_kg=0.3, k_per_h=0.02, V_m3=10.0, m_solid_kg=50.0)
    t = np.array([0, 1, 5, 10], dtype=float)
    c = predict_concentration(t, 200.0, p)
    assert c[0] >= c[-1]


