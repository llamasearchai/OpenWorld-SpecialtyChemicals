import numpy as np
import pandas as pd
# from hypothesis import given
# from hypothesis import strategies as st

from openworld_specialty_chemicals.chemistry import fit_parameters


def test_fit_non_negative_and_reasonable():
    c0 = 100.0
    k = 0.1
    t = np.arange(0, 6, dtype=float)
    conc = c0 * np.exp(-k * t)
    df = pd.DataFrame({"time": t, "species": ["SO4"] * len(t), "concentration": conc})
    res = fit_parameters(df, "SO4")
    assert res.k >= 0 and res.kd >= 0
    # Fitted k should be within a reasonable factor (tolerant)
    assert res.k <= 3.0

