import numpy as np
import pandas as pd
from hypothesis import given, strategies as st

from openworld_specialty_chemicals.chemistry import fit_parameters


@given(
    c0=st.floats(min_value=1e-3, max_value=1e6, allow_nan=False, allow_infinity=False),
    k=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
)
def test_fit_non_negative_and_reasonable(c0: float, k: float):
    t = np.arange(0, 6, dtype=float)
    conc = c0 * np.exp(-k * t)
    df = pd.DataFrame({"time": t, "species": ["SO4"] * len(t), "concentration": conc})
    res = fit_parameters(df, "SO4")
    assert res.k >= 0 and res.kd >= 0
    # Fitted k should be within a reasonable factor (tolerant)
    assert res.k <= 3.0

