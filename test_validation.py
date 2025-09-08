#!/usr/bin/env python3
"""
Validation script for OpenWorld Specialty Chemicals
Tests core functionality to ensure system is ready for publication
"""

import sys
from pathlib import Path

import pandas as pd

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all core modules can be imported"""
    print("[TEST] Testing module imports...")

    try:
        from openworld_specialty_chemicals.agents.fake_agent import FakeAdviceAgent
        from openworld_specialty_chemicals.chemistry import fit_parameters
        from openworld_specialty_chemicals.cli import app
        from openworld_specialty_chemicals.reporting import generate_certificate
        from openworld_specialty_chemicals.rules import check_permit
        print("    [SUCCESS] All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"    [ERROR] Import failed: {e}")
        return False

def test_chemistry_modeling():
    """Test chemistry parameter fitting"""
    print("[TEST] Testing chemistry modeling...")

    try:
        from openworld_specialty_chemicals.chemistry import fit_parameters

        # Create sample data
        df = pd.DataFrame({
            'time': [0, 1, 2, 3, 4],
            'species': ['SO4'] * 5,
            'concentration': [200, 210, 220, 280, 300]
        })

        result = fit_parameters(df, 'SO4')
        assert result.species == 'SO4'
        assert result.k >= 0
        assert result.kd > 0

        print("    [SUCCESS] Chemistry parameter fitting works correctly")
        return True
    except Exception as e:
        print(f"    [ERROR] Chemistry modeling failed: {e}")
        return False

def test_compliance_monitoring():
    """Test compliance monitoring"""
    print("[TEST] Testing compliance monitoring...")

    try:
        from openworld_specialty_chemicals.rules import check_permit

        # Create sample data with violations
        df = pd.DataFrame({
            'time': [0, 1, 2, 3, 4],
            'species': ['SO4'] * 5,
            'concentration': [200, 210, 220, 280, 300]
        })

        permit = {'limits': {'SO4': 250.0}, 'rolling_window': 3}
        alerts = check_permit(df, permit)

        assert len(alerts) > 0
        assert any(a['species'] == 'SO4' for a in alerts)

        print(f"    [SUCCESS] Compliance monitoring detected {len(alerts)} violations")
        return True
    except Exception as e:
        print(f"    [ERROR] Compliance monitoring failed: {e}")
        return False

def test_certificate_generation():
    """Test certificate generation"""
    print("[TEST] Testing certificate generation...")

    try:
        from openworld_specialty_chemicals.reporting import generate_certificate

        alerts = [
            {'species': 'SO4', 'value': 280.0, 'limit': 250.0}
        ]

        html = generate_certificate(alerts, 'Test Plant A')
        assert 'Test Plant A' in html
        assert 'NON-COMPLIANT' in html

        print("    [SUCCESS] Certificate generation works correctly")
        return True
    except Exception as e:
        print(f"    [ERROR] Certificate generation failed: {e}")
        return False

def test_ai_recommendations():
    """Test AI recommendation system"""
    print("[TEST] Testing AI recommendation system...")

    try:
        from openworld_specialty_chemicals.agents.fake_agent import FakeAdviceAgent

        alerts = [
            {'species': 'SO4', 'value': 280.0, 'limit': 250.0}
        ]

        agent = FakeAdviceAgent()
        advice = agent.advise(alerts)

        assert 'actions' in advice
        assert 'rationale' in advice
        assert len(advice['actions']) > 0

        print("    [SUCCESS] AI recommendation system works correctly")
        return True
    except Exception as e:
        print(f"    [ERROR] AI recommendation system failed: {e}")
        return False

def test_cli_commands():
    """Test CLI command structure"""
    print("[TEST] Testing CLI command structure...")

    try:
        from typer.testing import CliRunner

        from openworld_specialty_chemicals.cli import app

        runner = CliRunner()

        # Test help command
        result = runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert 'process-chemistry' in result.stdout
        assert 'monitor-batch' in result.stdout
        assert 'cert' in result.stdout
        assert 'advise' in result.stdout

        print("    [SUCCESS] CLI commands are properly structured")
        return True
    except Exception as e:
        print(f"    [ERROR] CLI testing failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=" * 60)
    print("OpenWorld Specialty Chemicals - System Validation")
    print("=" * 60)

    tests = [
        test_imports,
        test_chemistry_modeling,
        test_compliance_monitoring,
        test_certificate_generation,
        test_ai_recommendations,
        test_cli_commands
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"VALIDATION RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All systems are operational and ready for publication!")
        print("[READY] OpenWorld Specialty Chemicals platform is production-ready")
        return 0
    else:
        print("[WARNING] Some tests failed - review and fix before publication")
        return 1

if __name__ == "__main__":
    sys.exit(main())
