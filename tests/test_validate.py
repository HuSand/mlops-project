import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ml.validate import build_schema, main


@pytest.fixture
def valid_data(tmp_path):
    df = pd.DataFrame({
        'Gender': ['Male', 'Female'],
        'Age': [25.0, 30.0],
        'HasDrivingLicense': [1.0, 0.0],
        'RegionID': [1.0, 2.0],
        'Switch': [0.0, 1.0],
        'PastAccident': ['Yes', 'No'],
        'AnnualPremium': [1000.0, 2000.0],
        'target': [0, 1]
    })
    csv_path = tmp_path / "valid.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def invalid_data(tmp_path):
    df = pd.DataFrame({
        'Gender': ['Male', 'Female'],
        'Age': ['RUSAK', 'RUSAK'],
        'HasDrivingLicense': [1.0, 0.0],
        'RegionID': [1.0, 2.0],
        'Switch': [0.0, 1.0],
        'PastAccident': ['Yes', 'No'],
        'AnnualPremium': [1000.0, 2000.0],
        'target': [0, 1]
    })
    csv_path = tmp_path / "invalid.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def test_build_schema_with_target():
    schema = build_schema(include_target=True)
    assert 'target' in schema.columns


def test_build_schema_without_target():
    schema = build_schema(include_target=False)
    assert 'target' not in schema.columns


def test_validate_valid_data(valid_data):
    result = main.__wrapped__(valid_data) if hasattr(main, '__wrapped__') else None
    import sys
    sys.argv = ['validate.py', str(valid_data)]
    from ml.validate import main as validate_main
    assert validate_main() == 0


def test_validate_no_target(valid_data):
    import sys
    sys.argv = ['validate.py', str(valid_data), '--no-target']
    from ml.validate import main as validate_main
    assert validate_main() == 0


def test_validate_invalid_data(invalid_data):
    import sys
    sys.argv = ['validate.py', str(invalid_data)]
    from ml.validate import main as validate_main
    assert validate_main() == 1