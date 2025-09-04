import pandas as pd
from openworld_specialty_chemicals.rules import check_permit


def test_rules_severity_and_trend():
    # Construct a series just above limit to trigger trend
    df = pd.DataFrame({
        "time": [0, 1, 2, 3, 4],
        "species": ["SO4"] * 5,
        "concentration": [100, 110, 120, 130, 140],
    })
    permit = {"limits": {"SO4": 120.0}, "rolling_window": 3}
    alerts = check_permit(df, permit)
    assert any(a.get("level") in {"watch", "warning", "critical"} for a in alerts)
    assert any("rolling mean" in a.get("message", "") for a in alerts)


