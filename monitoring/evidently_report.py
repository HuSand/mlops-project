import argparse
import json
import pandas as pd
import sys

# --- SAFE IMPORT STRATEGY ---
try:
    # Versi Modern (0.4.0+)
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset
    from evidently import ColumnMapping
except ImportError:
    try:
        # Versi Menengah
        from evidently.model_monitoring import Report
        from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset
        from evidently import ColumnMapping
    except ImportError:
        try:
            # Versi Legacy
            from evidently.dashboard import Dashboard
            from evidently.tabs import DataDriftTab, CatTargetDriftTab
            print("WARNING: Using legacy Evidently structure. Report might look different.")
            # Mocking modern classes for legacy if needed (advanced)
            # Untuk sekarang kita stop jika versi terlalu lama
            raise ImportError("Evidently version is too old. Please use v0.4.0+")
        except ImportError as e:
            print(f"ERROR: Cannot find Evidently modules. sys.path: {sys.path}")
            raise e
# ----------------------------

def run_drift_report(reference_path: str, current_path: str, output_html: str, output_json: str):
    """Generate Evidently drift report dengan konfigurasi profesional."""

    # 1. Load data
    try:
        reference = pd.read_csv(reference_path)
        current = pd.read_csv(current_path)
    except Exception as e:
        print(f"ERROR: Gagal membaca file CSV: {e}")
        sys.exit(1)

    # 2. Sinkronisasi Nama Kolom (MAPPING)
    # Kita ubah nama kolom di data training (feature_x) agar sama dengan data produksi
    mapping = {
        "feature_0": "Gender",
        "feature_1": "Age",
        "feature_2": "HasDrivingLicense",
        "feature_3": "RegionID",
        "feature_4": "Switch",
        "feature_5": "PastAccident",
        "feature_6": "AnnualPremium",
        "target": "prediction" 
    }
    
    print("--- SCHEMA CROSS-CHECK ---")
    print(f"Reference Raw Columns: {list(reference.columns)}")
    print(f"Current Raw Columns:   {list(current.columns)}")
    
    reference = reference.rename(columns=mapping)

    # 3. Definisikan Column Mapping
    # Ini memberi tahu Evidently tipe data tiap kolom agar tidak salah hitung
    column_mapping = ColumnMapping()
    column_mapping.target = 'prediction' # Di CM, kita pantau hasil prediksi model
    column_mapping.numerical_features = ['Age', 'AnnualPremium', 'RegionID']
    column_mapping.categorical_features = ['Gender', 'HasDrivingLicense', 'Switch', 'PastAccident']

    # Ambil hanya kolom yang ada di kedua data (irisan)
    common_cols = [c for c in reference.columns if c in current.columns]
    
    # Pastikan ada data untuk dianalisis
    if len(common_cols) < 2:
        print(f"ERROR: Kolom tidak cocok! Common columns: {common_cols}")
        print("Pastikan mapping di dalam script sudah sesuai dengan header CSV.")
        sys.exit(1)

    print(f"--- ANALYZING COLUMNS: {common_cols} ---")

    # 4. Jalankan Report dengan Preset Lengkap
    # Kita tambahkan DataQuality untuk mengecek data yang aneh/kosong
    report = Report(metrics=[
        DataDriftPreset(drift_share=0.3), # Global Threshold 30%
        DataQualityPreset(),
        TargetDriftPreset()
    ])

    report.run(
        reference_data=reference[common_cols], 
        current_data=current[common_cols],
        column_mapping=column_mapping
    )

    # Simpan laporan HTML
    report.save_html(output_html)
    print(f"HTML report saved: {output_html}")

    # 5. Extract Metrics untuk JSON (digunakan untuk Alerting)
    result = report.as_dict()
    
    # Inisialisasi ringkasan drift
    drift_metrics = {
        "drift_share": 0.0,
        "number_of_drifted_columns": 0,
        "number_of_columns": 0,
        "dataset_drift": False,
        "drifted_features": [],
    }

    # Cari metrik drift di dalam kamus hasil
    for metric in result.get("metrics", []):
        # Evidently v0.4+ menggunakan nama class metric sebagai key
        res = metric.get("result", {})
        if "dataset_drift" in res:
            drift_metrics["drift_share"] = res.get("share_of_drifted_columns", 0)
            drift_metrics["number_of_drifted_columns"] = res.get("number_of_drifted_columns", 0)
            drift_metrics["number_of_columns"] = res.get("number_of_columns", 0)
            drift_metrics["dataset_drift"] = res.get("dataset_drift", False)
            
            # List fitur mana saja yang drift
            for col, data in res.get("drift_by_columns", {}).items():
                if data.get("drift_detected"):
                    drift_metrics["drifted_features"].append({
                        "feature": col,
                        "drift_score": data.get("drift_score")
                    })

    with open(output_json, "w") as f:
        json.dump(drift_metrics, f, indent=2)

    print(f"Metrics JSON saved: {output_json}")
    return drift_metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--output-html", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    
    run_drift_report(args.reference, args.current, args.output_html, args.output_json)
