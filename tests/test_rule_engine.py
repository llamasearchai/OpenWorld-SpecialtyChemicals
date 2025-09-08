import pandas as pd

from openworld_specialty_chemicals.permits import DEFAULT_PERMIT
from openworld_specialty_chemicals.rule_engine import evaluate_permit


def test_evaluate_permit_generates_alerts():
    df = pd.DataFrame({"time_h":[0,1,2], "SO4_mgL":[200,260,270], "As_mgL":[0.005,0.006,0.007]})
    alerts = evaluate_permit(df, DEFAULT_PERMIT)
    species = {a["species"] for a in alerts}
    assert "SO4" in species


