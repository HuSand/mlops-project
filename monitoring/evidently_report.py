"""
Evidently AI Drift Report Generator
Dijalankan oleh monitor.yml setiap hari.
Membandingkan reference data (training) vs current data (production).
"""

import argparse
import json
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset


def run_drift_report(reference_path: str, current_path: str, output_html: str, output_json: str):
    """Generate Evidently drift report dan simpan hasilnya."""

    # Load data
    reference = pd.read_csv(reference_path)
    current = pd.read_csv(current_path)

    print(f"Reference data: {len(reference)} rows")
    print(f"Current data:   {len(current)} rows")

    # Jalankan Evidently report dengan 3 preset yang dibutuhkan
    report = Report(metrics=[
        DataDriftPreset(),       # deteksi pergeseran distribusi fitur
        TargetDriftPreset(),     # deteksi pergeseran distribusi prediksi
        DataQualityPreset(),     # deteksi data kotor (missing, duplikat)
    ])

    report.run(reference_data=reference, current_data=current)

    # Simpan report HTML (untuk upload ke GCS)
    report.save_html(output_html)
    print(f"HTML report saved: {output_html}")

    # Extract metrics penting untuk threshold check
    result = report.as_dict()
    drift_metrics = {
        "drift_share": 0.0,
        "number_of_drifted_columns": 0,
        "number_of_columns": 0,
        "dataset_drift": False,
        "drifted_features": [],
    }

    for metric in result.get("metrics", []):
        res = metric.get("result", {})

        # Extract data drift info
        if "dataset_drift" in res and "share_of_drifted_columns" in res:
            drift_metrics["drift_share"] = res["share_of_drifted_columns"]
            drift_metrics["number_of_drifted_columns"] = res["number_of_drifted_columns"]
            drift_metrics["number_of_columns"] = res["number_of_columns"]
            drift_metrics["dataset_drift"] = res["dataset_drift"]

            # Detail per fitur
            for col_name, col_data in res.get("drift_by_columns", {}).items():
                if col_data.get("drift_detected", False):
                    drift_metrics["drifted_features"].append({
                        "feature": col_name,
                        "drift_score": col_data.get("drift_score", 0),
                        "stattest": col_data.get("stattest_name", "unknown"),
                    })

    # Simpan metrics sebagai JSON (untuk threshold check di workflow)
    with open(output_json, "w") as f:
        json.dump(drift_metrics, f, indent=2)

    print(f"Metrics JSON saved: {output_json}")
    print(f"Drift share: {drift_metrics['drift_share']:.2f}")
    print(f"Drifted features: {drift_metrics['number_of_drifted_columns']}/{drift_metrics['number_of_columns']}")

    return drift_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Evidently drift report")
    parser.add_argument("--reference", required=True, help="Path to reference (training) CSV")
    parser.add_argument("--current", required=True, help="Path to current (production) CSV")
    parser.add_argument("--output-html", required=True, help="Output path for HTML report")
    parser.add_argument("--output-json", required=True, help="Output path for metrics JSON")

    args = parser.parse_args()
    run_drift_report(args.reference, args.current, args.output_html, args.output_json)