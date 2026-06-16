import argparse
import json
import os
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from scipy.stats import chi2
from sklearn.metrics import accuracy_score, roc_auc_score

from steps.clean import Cleaner


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare champion and staging models and decide if the challenger should be promoted."
    )
    parser.add_argument(
        "run_id",
        help="MLflow run ID for the staging challenger model.",
    )
    parser.add_argument(
        "--test-csv",
        default="data/test.csv",
        help="Path to the test CSV file.",
    )
    parser.add_argument(
        "--output",
        default="promote_decision.json",
        help="Output JSON file path.",
    )
    return parser.parse_args()


def load_test_data(test_csv_path: Path) -> pd.DataFrame:
    if not test_csv_path.exists():
        raise FileNotFoundError(f"Test data not found: {test_csv_path}")
    df = pd.read_csv(test_csv_path)
    cleaner = Cleaner()
    cleaned = cleaner.clean_data(df)
    return cleaned


def load_model(model_uri: str):
    return mlflow.pyfunc.load_model(model_uri)


def safe_roc_auc(model, X, y):
    if hasattr(model, "predict_proba"):
        y_score = model.predict_proba(X)
        if isinstance(y_score, np.ndarray) and y_score.ndim == 2:
            y_score = y_score[:, 1]
        return roc_auc_score(y, y_score)
    if hasattr(model, "decision_function"):
        y_score = model.decision_function(X)
        return roc_auc_score(y, y_score)
    y_pred = model.predict(X)
    return roc_auc_score(y, y_pred)


def mcnemar_test(y_true, y_a, y_b):
    y_a = np.asarray(y_a).astype(int)
    y_b = np.asarray(y_b).astype(int)
    y_true = np.asarray(y_true).astype(int)

    correct_a = y_a == y_true
    correct_b = y_b == y_true

    b = np.sum(np.logical_and(~correct_a, correct_b))
    c = np.sum(np.logical_and(correct_a, ~correct_b))
    total = b + c

    if total == 0:
        return 1.0

    statistic = (abs(b - c) - 1) ** 2 / total
    p_value = 1 - chi2.cdf(statistic, df=1)
    return float(p_value)


def predict_model(model, X):
    if hasattr(model, "predict"):
        return np.asarray(model.predict(X)).astype(int)
    raise AttributeError("Loaded model does not support predict().")


def evaluate_model(model, X, y):
    y_pred = predict_model(model, X)
    accuracy = float(accuracy_score(y, y_pred))
    roc_auc = float(safe_roc_auc(model, X, y))
    return y_pred, accuracy, roc_auc


def write_decision(output_path: Path, payload: dict):
    output_path.write_text(json.dumps(payload, indent=2))


def main() -> int:
    args = parse_args()
    run_id = args.run_id
    test_csv_path = Path(args.test_csv)
    output_path = Path(args.output)

    mlflow_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if not mlflow_tracking_uri:
        print("ERROR: MLFLOW_TRACKING_URI must be set in the environment.")
        return 1

    mlflow.set_tracking_uri(mlflow_tracking_uri)

    try:
        test_data = load_test_data(test_csv_path)
    except Exception as exc:
        print(f"ERROR: Failed to load or clean test data: {exc}")
        return 1

    X_test = test_data.iloc[:, :-1]
    y_test = test_data.iloc[:, -1].astype(int)

    try:
        champion_model = load_model("models:/insurance_model/Production")
    except Exception as exc:
        print(f"ERROR: Failed to load champion Production model: {exc}")
        return 1

    try:
        challenger_model = load_model(f"runs:/{run_id}/model")
    except Exception as exc:
        print(f"ERROR: Failed to load challenger model for run_id={run_id}: {exc}")
        return 1

    try:
        champion_preds, champion_accuracy, champion_roc_auc = evaluate_model(
            champion_model, X_test, y_test
        )
        challenger_preds, challenger_accuracy, challenger_roc_auc = evaluate_model(
            challenger_model, X_test, y_test
        )
    except Exception as exc:
        print(f"ERROR: Evaluation failed: {exc}")
        return 1

    p_value = mcnemar_test(y_test, champion_preds, challenger_preds)
    accuracy_delta = challenger_accuracy - champion_accuracy
    # decision = "PROMOTE"
    decision = "PROMOTE" if accuracy_delta > 0.01 and p_value < 0.05 else "KEEP_STAGING"

    result = {
        "decision": decision,
        "challenger_accuracy": challenger_accuracy,
        "champion_accuracy": champion_accuracy,
        "accuracy_delta": accuracy_delta,
        "p_value": p_value,
        "run_id": run_id,
        "champion_roc_auc": champion_roc_auc,
        "challenger_roc_auc": challenger_roc_auc,
    }

    try:
        write_decision(output_path, result)
    except Exception as exc:
        print(f"ERROR: Failed to write decision JSON: {exc}")
        return 1
    
    # Simpan model ke GCS untuk visualisasi Sandy
    try:
        from google.cloud import storage as gcs

        gcs_client = gcs.Client()
        bucket = gcs_client.bucket("mlflow-artifacts-mlops")

        run_number = os.environ.get("GITHUB_RUN_NUMBER", "local")

        # Download dan upload challenger model
        challenger_path = mlflow.artifacts.download_artifacts(
            f"runs:/{run_id}/model/model.pkl"
        )
        bucket.blob(f"models/history/challenger-run{run_number}.pkl").upload_from_filename(challenger_path)

        # Download dan upload champion model
        champion_path = mlflow.artifacts.download_artifacts(
            "models:/insurance_model/Production/model/model.pkl"
        )
        bucket.blob(f"models/history/champion-run{run_number}.pkl").upload_from_filename(champion_path)

        print(f"Models saved to GCS: challenger-run{run_number}.pkl, champion-run{run_number}.pkl")
    except Exception as e:
        print(f"Warning: Failed to save models to GCS (non-fatal): {e}")

    print(json.dumps(result, indent=2))
    return 0 


if __name__ == "__main__":
    raise SystemExit(main())
