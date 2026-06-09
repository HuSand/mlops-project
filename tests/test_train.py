import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, mock_open
from steps.train import Trainer
from steps.predict import Predictor
from steps.clean import Cleaner


@pytest.fixture
def sample_train_data():
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'Gender': np.random.choice(['Male', 'Female'], n),
        'Age': np.random.uniform(20, 70, n),
        'HasDrivingLicense': np.random.choice([0.0, 1.0], n),
        'RegionID': np.random.uniform(1, 52, n),
        'Switch': np.random.choice([-1.0, 0.0, 1.0], n),
        'PastAccident': np.random.choice(['Yes', 'No', 'Unknown'], n),
        'AnnualPremium': np.random.uniform(800, 6000, n),
        'target': np.random.choice([0, 1], n)
    })

@pytest.fixture
def trainer():
    config = {
        'model': {
            'name': 'DecisionTreeClassifier',
            'params': {'criterion': 'entropy', 'max_depth': None},
            'store_path': 'models/'
        }
    }
    with patch('builtins.open', mock_open(read_data='dummy')):
        with patch('yaml.safe_load', return_value=config):
            return Trainer()


def test_feature_target_separator(trainer, sample_train_data):
    X, y = trainer.feature_target_separator(sample_train_data)
    assert 'target' not in X.columns
    assert len(y) == len(sample_train_data)


def test_train_model(trainer, sample_train_data):
    X, y = trainer.feature_target_separator(sample_train_data)
    trainer.train_model(X, y)
    assert trainer.pipeline is not None


def test_cleaner_drop_cols():
    cleaner = Cleaner()
    df = pd.DataFrame({
        'id': [1, 2],
        'SalesChannelID': [1, 1],
        'VehicleAge': [1, 1],
        'DaysSinceCreated': [1, 1],
        'Age': [25.0, 30.0],
        'Gender': ['Male', 'Female'],
        'AnnualPremium': [1000.0, 2000.0],
        'HasDrivingLicense': [1.0, 1.0],
        'RegionID': [1.0, 2.0],
        'Switch': [0.0, 1.0],
        'PastAccident': ['Yes', 'No'],
    })
    cleaned = cleaner.clean_data(df.copy())
    assert 'id' not in cleaned.columns
    assert 'SalesChannelID' not in cleaned.columns
    assert 'VehicleAge' not in cleaned.columns
    assert 'DaysSinceCreated' not in cleaned.columns


def test_cleaner_impute_missing():
    cleaner = Cleaner()
    df = pd.DataFrame({
        'Gender': [np.nan, 'Male'],
        'Age': [np.nan, 30.0],
        'HasDrivingLicense': [np.nan, 1.0],
        'RegionID': [np.nan, 2.0],
        'Switch': [np.nan, 0.0],
        'PastAccident': [np.nan, 'Yes'],
        'AnnualPremium': [1000.0, 2000.0],
    })
    cleaned = cleaner.clean_data(df.copy())
    assert not cleaned['Gender'].isnull().any()
    assert not cleaned['Age'].isnull().any()
    assert not cleaned['HasDrivingLicense'].isnull().any()
    assert not cleaned['Switch'].isnull().any()
    assert not cleaned['PastAccident'].isnull().any()
    assert (cleaned['PastAccident'] == 'Unknown').any()
    assert (cleaned['Switch'] == -1).any()
    assert (cleaned['HasDrivingLicense'] == 1).any()


def test_cleaner_annual_premium_dtype():
    cleaner = Cleaner()
    df = pd.DataFrame({
        'AnnualPremium': ['£1,200', '£2,500'],
        'Gender': ['Male', 'Female'],
        'Age': [25.0, 30.0],
        'HasDrivingLicense': [1.0, 1.0],
        'RegionID': [1.0, 2.0],
        'Switch': [0.0, 1.0],
        'PastAccident': ['Yes', 'No'],
    })
    cleaned = cleaner.clean_data(df.copy())
    assert cleaned['AnnualPremium'].dtype == float

def test_predictor_feature_target_separator(sample_train_data):
    predictor = Predictor()
    X, y = predictor.feature_target_separator(sample_train_data)
    assert 'target' not in X.columns
    assert len(y) == len(sample_train_data)

def test_predictor_evaluate_model(trainer, sample_train_data):
    X, y = trainer.feature_target_separator(sample_train_data)
    trainer.train_model(X, y)
    predictor = Predictor()
    X_test, y_test = predictor.feature_target_separator(sample_train_data)
    accuracy, report, roc_auc = predictor.evaluate_model(X_test, y_test)
    assert 0 <= accuracy <= 1
    assert 0 <= roc_auc <= 1