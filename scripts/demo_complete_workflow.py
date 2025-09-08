#!/usr/bin/env python3
"""
Complete workflow demonstration for OpenWorld Specialty Chemicals monitoring system.
This script demonstrates the end-to-end process from data ingestion to compliance reporting.
"""
import json
import os

import pandas as pd

from openworld_specialty_chemicals.agents.fake_agent import FakeAdviceAgent
from openworld_specialty_chemicals.chemistry import fit_parameters
from openworld_specialty_chemicals.reporting import generate_certificate
from openworld_specialty_chemicals.rules import check_permit


def create_demo_data():
    """Create sample effluent data for demonstration."""
    print("[DATA] Creating sample effluent data...")

    # Create batch data with SO4 concentrations showing an excursion
    df = pd.DataFrame({
        "time": list(range(10)),  # hours
        "species": ["SO4"] * 10,
        "concentration": [200, 205, 210, 215, 220, 280, 300, 250, 240, 230]  # mg/L
    })

    # Save to data directory
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/lab_batch.csv", index=False)
    print(f"[SUCCESS] Created data/lab_batch.csv with {len(df)} samples")
    return df


def fit_chemistry_parameters(df):
    """Fit chemistry parameters for SO4 species."""
    print("\n[CHEMISTRY] Fitting chemistry parameters...")

    result = fit_parameters(df, "SO4")
    fit_data = {
        "species": result.species,
        "decay_rate_k": result.k,
        "partition_coeff_Kd": result.kd
    }

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/so4_parameters.json", "w") as f:
        json.dump(fit_data, f, indent=2)

    print("[SUCCESS] Chemistry parameters fitted and saved to artifacts/so4_parameters.json")
    return fit_data


def monitor_compliance(df, fit_data):
    """Monitor compliance against permit limits."""
    print("\n[COMPLIANCE] Monitoring compliance...")

    # Define permit limits
    permit = {
        "limits": {"SO4": 250.0},  # mg/L
        "rolling_window": 3
    }

    # Check for permit violations
    alerts = check_permit(df, permit)

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/compliance_alerts.json", "w") as f:
        json.dump(alerts, f, indent=2)

    print(f"[SUCCESS] Compliance monitoring completed: {len(alerts)} alerts generated")
    for alert in alerts:
        print(
            f"   - {alert['species']}: {alert['value']:.1f} mg/L "
            f"exceeds {alert['limit']:.1f} mg/L"
        )

    return alerts


def generate_compliance_certificate(alerts):
    """Generate compliance certificate."""
    print("\n[CERTIFICATE] Generating compliance certificate...")

    html_content = generate_certificate(alerts, "Demo Plant A")

    os.makedirs("reports", exist_ok=True)
    with open("reports/compliance_certificate.html", "w") as f:
        f.write(html_content)

    print("[SUCCESS] Compliance certificate generated: reports/compliance_certificate.html")
    print(f"   Status: {'NON-COMPLIANT' if alerts else 'COMPLIANT'}")
    return html_content


def get_advice_recommendations(alerts):
    """Get AI-powered advice recommendations."""
    print("\n[ADVICE] Getting advice recommendations...")

    agent = FakeAdviceAgent()
    advice = agent.advise(alerts)

    print("[SUCCESS] Advice recommendations generated:")
    print(f"   Rationale: {advice['rationale']}")
    for action in advice['actions']:
        print(f"   - {action}")

    return advice


def main():
    """Run the complete workflow demonstration."""
    print("OpenWorld Specialty Chemicals - Complete Workflow Demo")
    print("=" * 60)

    try:
        # Step 1: Create sample data
        df = create_demo_data()

        # Step 2: Fit chemistry parameters
        fit_data = fit_chemistry_parameters(df)

        # Step 3: Monitor compliance
        alerts = monitor_compliance(df, fit_data)

        # Step 4: Generate certificate
        _ = generate_compliance_certificate(alerts)

        # Step 5: Get advice
        _ = get_advice_recommendations(alerts)

        print("\n" + "=" * 60)
        print("[SUCCESS] Complete workflow demonstration successful!")
        print("\nGenerated files:")
        print("  [DATA] data/lab_batch.csv - Sample effluent data")
        print("  [CHEMISTRY] artifacts/so4_parameters.json - Fitted chemistry parameters")
        print("  [COMPLIANCE] artifacts/compliance_alerts.json - Compliance alerts")
        print("  [CERTIFICATE] reports/compliance_certificate.html - Compliance certificate")

        # Summary
        status = "NON-COMPLIANT" if alerts else "COMPLIANT"
        print(f"\n[SUMMARY] Plant status is {status}")
        if alerts:
            print(f"   Found {len(alerts)} permit violations requiring attention")
        else:
            print("   All parameters within permit limits - excellent compliance!")

    except Exception as e:
        print(f"\n[ERROR] Error during demonstration: {e}")
        raise


if __name__ == "__main__":
    main()
