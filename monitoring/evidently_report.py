"""
Evidently AI Drift Report Generator - Final Aligned Version
Menyelaraskan nama kolom antara feature_0...9 (Reference) dan nama asli dari log BigQuery.
"""

import argparse
import json
import pandas as pd
try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset
except ImportError:
    from evidently.legacy.report import Report
    from evidently.legacy.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset


def run_drift_report(reference_path: str, current_path: str, output_html: str, output_json: str):
    """Generate Evidently drift report dengan pemetaan kolom yang disinkronkan."""

    # Load data
    reference = pd.read_csv(reference_path)
    current = pd.read_csv(current_path)

    # 1. DEFINISI PEMETAAN (Mapping) Berdasarkan Cross-Check
    # Reference: feature_0 s/d feature_9
    # Current: Gender, Age, HasDrivingLicense, RegionID, Switch, PastAccident, AnnualPremium
    mapping = {
        "feature_0": "Gender",
        "feature_1": "Age",
        "feature_2": "HasDrivingLicense",
        "feature_3": "RegionID",
        "feature_4": "Switch",
        "feature_5": "PastAccident",
        "feature_6": "AnnualPremium",
        # Jika ada feature_7, 8, 9, silakan tambahkan di sini jika sudah ada di log BQ
        "target": "prediction" 
    }

    print("--- SCHEMA CROSS-CHECK ---")
    print(f"Reference Raw Columns: {list(reference.columns)}")
    print(f"Current Raw Columns:   {list(current.columns)}")

    # Ganti nama kolom di Reference agar match dengan Current
    reference = reference.rename(columns=mapping)

    # 2. Ambil irisan kolom yang ada di keduanya
    common_cols = [c for c in reference.columns if c in current.columns]
    
    # Filter kolom metadata yang tidak perlu dihitung drift-nya
    exclude_from_drift = ['model_version', 'timestamp']
    analysis_cols = [c for c in common_cols if c not in exclude_from_drift]

    if not analysis_cols:
        print("ERROR: Tidak ada kolom fitur yang cocok untuk dibandingkan!")
        return

    print(f"Aligned Columns for Analysis: {analysis_cols}")

    # 3. Jalankan Report
    metrics_to_run = [DataDriftPreset(), DataQualityPreset()]
    if "prediction" in analysis_cols:
        print("Adding TargetDriftPreset for 'prediction' column.")
        metrics_to_run.append(TargetDriftPreset())

    report = Report(metrics=metrics_to_run)
    report.run(reference_data=reference[analysis_cols], current_data=current[analysis_cols])

    # Simpan report HTML
    report.save_html(output_html)
    print(f"HTML report saved: {output_html}")

    # 4. Extract Metrics untuk JSON
    result = report.as_dict()
    drift_metrics = {
        "drift_share": 0.0,
        "number_of_drifted_columns": 0,
        "number_of_columns": len([c for c in analysis_cols if c != 'prediction']),
        "dataset_drift": False,
        "drifted_features": [],
    }

    for metric in result.get("metrics", []):
        res = metric.get("result", {})
        if "dataset_drift" in res:
            drift_metrics["drift_share"] = res.get("share_of_drifted_columns", 0)
            drift_metrics["number_of_drifted_columns"] = res.get("number_of_drifted_columns", 0)
            drift_metrics["dataset_drift"] = res.get("dataset_drift", False)

            for col_name, col_data in res.get("drift_by_columns", {}).items():
                if col_data.get("drift_detected", False):
                    drift_metrics["drifted_features"].append({
                        "feature": col_name,
                        "drift_score": col_data.get("drift_score", 0),
                    })

    with open(output_json, "w") as f:
        json.dump(drift_metrics, f, indent=2)

    print(f"Metrics JSON saved: {output_json}")
    return drift_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Evidently drift report")
    parser.add_argument("--reference", required=True, help="Path to reference (training) CSV")
    parser.add_argument("--current", required=True, help="Path to current (production) CSV")
    parser.add_argument("--output-html", required=True, help="Output path for HTML report")
    parser.add_argument("--output-json", required=True, help="Output path for metrics JSON")

    args = parser.parse_args()
    run_drift_report(args.reference, args.current, args.output_html, args.output_json)
