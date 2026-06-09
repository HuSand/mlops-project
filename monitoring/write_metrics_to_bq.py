"""
Write drift metrics ke BigQuery.
Data ini nanti ditampilkan di Looker Studio dashboard.
"""

import argparse
import json
from datetime import datetime
from google.cloud import bigquery


def write_metrics(project_id: str, metrics_file: str):
    """Insert drift metrics ke tabel BigQuery mlops.drift_metrics."""

    with open(metrics_file) as f:
        metrics = json.load(f)

    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.mlops.drift_metrics"

    # Siapkan row untuk di-insert
    row = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "timestamp": datetime.utcnow().isoformat(),
        "drift_share": metrics.get("drift_share", 0.0),
        "number_of_drifted_columns": metrics.get("number_of_drifted_columns", 0),
        "number_of_columns": metrics.get("number_of_columns", 0),
        "dataset_drift": metrics.get("dataset_drift", False),
        "drifted_features": json.dumps(metrics.get("drifted_features", [])),
        "missing_values_count": metrics.get("data_quality", {}).get("missing_values_count", 0),
        "total_rows": metrics.get("data_quality", {}).get("total_rows", 0),
    }

    try:
        errors = client.insert_rows_json(table_id, [row])
        if errors:
            print(f"BigQuery insert errors: {errors}")
        else:
            print(f"Metrics written to BigQuery: {table_id}")
            print(f"  drift_share: {row['drift_share']}")
            print(f"  drifted_columns: {row['number_of_drifted_columns']}/{row['number_of_columns']}")
    except Exception as e:
        print(f"BigQuery write error: {e}")
        print("Metrics not saved to BigQuery (table may not exist yet)")
        print("To create the table, run: bq mk --table mlops.drift_metrics monitoring/schema/drift_metrics.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--metrics-file", required=True)
    args = parser.parse_args()
    write_metrics(args.project_id, args.metrics_file)