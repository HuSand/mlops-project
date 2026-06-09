"""Generate a markdown model card from MLflow run information."""

import argparse
import os
from datetime import datetime
from pathlib import Path

import mlflow
import pandas as pd
import yaml


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a markdown model card from MLflow run information."
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="MLflow run ID.",
    )
    parser.add_argument(
        "--model-version",
        required=True,
        help="Model version (e.g., '1', '2').",
    )
    parser.add_argument(
        "--output",
        default="model_card.md",
        help="Output markdown file path.",
    )
    return parser.parse_args()


def load_config() -> dict:
    """Load config.yml to get model name and details."""
    with open("config.yml", "r") as f:
        return yaml.safe_load(f)


def get_dataset_info() -> dict:
    """Get dataset info: row count, column names."""
    test_csv = Path("data/test.csv")
    if test_csv.exists():
        df = pd.read_csv(test_csv)
        return {
            "row_count": len(df),
            "columns": list(df.columns),
        }
    return {"row_count": "N/A", "columns": []}


def get_mlflow_run_info(run_id: str) -> dict:
    """Fetch MLflow run info and metrics."""
    mlflow_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if mlflow_tracking_uri:
        mlflow.set_tracking_uri(mlflow_tracking_uri)

    try:
        run = mlflow.get_run(run_id)
        metrics = run.data.metrics
        params = run.data.params
        return {
            "metrics": metrics,
            "params": params,
            "start_time": datetime.fromtimestamp(run.info.start_time / 1000),
        }
    except Exception as e:
        print(f"WARNING: Could not fetch MLflow run info: {e}")
        return {
            "metrics": {},
            "params": {},
            "start_time": datetime.now(),
        }


def get_git_info() -> dict:
    """Get Git SHA and branch from environment."""
    git_sha = os.environ.get("GITHUB_SHA", "N/A")
    git_ref = os.environ.get("GITHUB_REF", "N/A")
    git_branch = git_ref.replace("refs/heads/", "") if git_ref.startswith("refs/heads/") else git_ref
    return {
        "sha": git_sha,
        "branch": git_branch,
    }


def get_github_event() -> str:
    """Get GitHub event trigger type."""
    return os.environ.get("GITHUB_EVENT_NAME", "manual")


def generate_model_card(
    run_id: str,
    model_version: str,
    output_path: Path,
) -> int:
    """Generate model card markdown file."""
    config = load_config()
    dataset_info = get_dataset_info()
    mlflow_info = get_mlflow_run_info(run_id)
    git_info = get_git_info()
    github_event = get_github_event()

    # Extract metrics
    metrics = mlflow_info["metrics"]
    accuracy = metrics.get("accuracy", "N/A")
    roc_auc = metrics.get("roc_auc_score", "N/A")
    precision = metrics.get("precision", "N/A")
    recall = metrics.get("recall", "N/A")

    # Format metrics for display
    if isinstance(accuracy, (int, float)):
        accuracy = f"{accuracy:.4f}"
    if isinstance(roc_auc, (int, float)):
        roc_auc = f"{roc_auc:.4f}"
    if isinstance(precision, (int, float)):
        precision = f"{precision:.4f}"
    if isinstance(recall, (int, float)):
        recall = f"{recall:.4f}"

    model_name = config.get("model", {}).get("name", "Unknown Model")
    start_time = mlflow_info["start_time"].strftime("%Y-%m-%d %H:%M:%S")

    # Generate markdown content
    markdown_content = f"""# Insurance Cross-Sell Prediction Model Card

## Model Information

- **Model Name:** {model_name}
- **Version:** {model_version}
- **Run ID:** {run_id}
- **Training Date:** {start_time}

## Dataset

- **Name:** Insurance Cross-Sell
- **Training Split:** data/train.csv
- **Test Split:** data/test.csv
- **Total Test Rows:** {dataset_info["row_count"]}
- **Features:** {len(dataset_info["columns"])} columns

### Dataset Columns

{', '.join(dataset_info['columns'])}

## Model Details

### Algorithm

**{model_name}**

Model algorithm configured via `config.yml`.

### Preprocessing

The model uses a preprocessing pipeline with the following transformers:

- **OneHotEncoder:** Categorical feature encoding
- **StandardScaler:** Feature normalization
- **MinMaxScaler:** Feature scaling to [0, 1] range
- **SMOTE:** Synthetic Minority Over-Sampling for class imbalance

## Performance Metrics

| Metric | Value |
|--------|-------|
| Accuracy | {accuracy} |
| ROC AUC Score | {roc_auc} |
| Precision | {precision} |
| Recall | {recall} |

## Training Information

### Git Details

- **Commit SHA:** {git_info["sha"]}
- **Branch:** {git_info["branch"]}

### Trigger

- **GitHub Event:** {github_event}

## Limitations

This model was trained on historical insurance data and may have the following limitations:

- **Data Freshness:** Model performance may degrade if the distribution of new data differs significantly from the training data.
- **Feature Dependencies:** Model relies on features that may not capture all relevant factors affecting customer cross-sell propensity.
- **Class Imbalance:** Despite SMOTE preprocessing, the model may show bias in handling minority class predictions.
- **Generalization:** Model trained on specific geographic regions; performance may vary for other regions.
- **Business Context:** This model is intended for decision support only; human review is recommended before taking action on predictions.

## Additional Notes

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    try:
        output_path.write_text(markdown_content)
        print(f"Model card generated successfully: {output_path}")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to write model card to {output_path}: {e}")
        return 1


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    return generate_model_card(
        run_id=args.run_id,
        model_version=args.model_version,
        output_path=output_path,
    )


if __name__ == "__main__":
    exit(main())
