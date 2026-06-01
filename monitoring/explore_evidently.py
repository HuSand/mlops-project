"""
============================================================
EXPLORASI EVIDENTLY AI - Insurance Cross-Sell Prediction
============================================================
Jalankan file ini di laptop kamu: python explore_evidently.py
Nanti akan muncul 4 file HTML yang bisa dibuka di browser.
"""

import pandas as pd
import numpy as np
try:
    from evidently.report import Report
    from evidently.metric_preset import (
        DataDriftPreset,
        TargetDriftPreset,
        DataQualityPreset,
        ClassificationPreset,
    )
    from evidently.metrics import ColumnDriftMetric
except ImportError:
    from evidently.legacy.report import Report
    from evidently.legacy.metric_preset import (
        DataDriftPreset,
        TargetDriftPreset,
        DataQualityPreset,
        ClassificationPreset,
    )
    from evidently.legacy.metrics import ColumnDriftMetric

# ============================================================
# STEP 1: Siapkan data simulasi (sesuai fitur project kalian)
# ============================================================
# Di project asli, data ini akan ditarik dari BigQuery (production)
# dan GCS via DVC (training). Sekarang kita simulasikan dulu.

np.random.seed(42)

# Data REFERENCE = data training (1000 row)
# Ini baseline, distribusi "normal" yang model sudah pelajari
reference = pd.DataFrame({
    'Gender':            np.random.choice(['Male', 'Female'], 1000, p=[0.54, 0.46]),
    'Age':               np.random.normal(38, 12, 1000).clip(18, 85).astype(int),
    'HasDrivingLicense':  np.random.choice([0, 1], 1000, p=[0.01, 0.99]),
    'RegionID':          np.random.randint(1, 53, 1000),
    'Switch':            np.random.choice([0, 1], 1000, p=[0.74, 0.26]),
    'PastAccident':      np.random.choice(['Yes', 'No'], 1000, p=[0.44, 0.56]),
    'AnnualPremium':     np.random.lognormal(10.2, 0.5, 1000).clip(2000, 100000),
    'target':            np.random.choice([0, 1], 1000, p=[0.88, 0.12]),
})

# Data CURRENT = data production 24 jam terakhir (200 row)
# Sengaja dibuat BERBEDA supaya drift terdeteksi
current = pd.DataFrame({
    'Gender':            np.random.choice(['Male', 'Female'], 200, p=[0.30, 0.70]),  # berubah!
    'Age':               np.random.normal(28, 8, 200).clip(18, 85).astype(int),       # lebih muda!
    'HasDrivingLicense':  np.random.choice([0, 1], 200, p=[0.02, 0.98]),
    'RegionID':          np.random.randint(1, 53, 200),
    'Switch':            np.random.choice([0, 1], 200, p=[0.50, 0.50]),              # berubah!
    'PastAccident':      np.random.choice(['Yes', 'No'], 200, p=[0.20, 0.80]),       # berubah!
    'AnnualPremium':     np.random.lognormal(9.5, 0.7, 200).clip(2000, 100000),      # lebih rendah!
    'target':            np.random.choice([0, 1], 200, p=[0.65, 0.35]),              # berubah!
})

# Tambah missing values (simulasi data kotor dari production)
current.loc[current.sample(5).index, 'Age'] = np.nan
current.loc[current.sample(3).index, 'AnnualPremium'] = np.nan

print("Data siap!")
print(f"  Reference (training): {len(reference)} rows")
print(f"  Current (production): {len(current)} rows")
print()

# ============================================================
# EXPLORASI 1: DataDriftPreset
# Fungsi: Cek apakah distribusi data input bergeser
# INI YANG PALING PENTING untuk monitoring kalian
# ============================================================
print("=" * 60)
print("EXPLORASI 1: DataDriftPreset")
print("Cek apakah distribusi fitur bergeser dari training")
print("=" * 60)

report1 = Report(metrics=[DataDriftPreset()])
report1.run(reference_data=reference, current_data=current)
report1.save_html("1_data_drift.html")

# Baca hasilnya secara programmatic
result = report1.as_dict()
for m in result['metrics']:
    res = m.get('result', {})
    if 'dataset_drift' in res:
        print(f"  Drift terdeteksi?  : {res['dataset_drift']}")
        print(f"  Fitur yang drift   : {res['number_of_drifted_columns']}/{res['number_of_columns']}")
        print(f"  Skor drift (share) : {res['share_of_drifted_columns']:.2f}")
        print()
        print("  Detail per fitur:")
        for col, data in res.get('drift_by_columns', {}).items():
            score = data.get('drift_score', 0)
            detected = data.get('drift_detected', False)
            method = data.get('stattest_name', '?')
            tag = "DRIFT!" if detected else "ok"
            print(f"    {col:22s} score={score:.4f}  metode={method}  [{tag}]")
        break

print()
print("  >> Buka 1_data_drift.html di browser untuk lihat visualnya")
print()

# ============================================================
# EXPLORASI 2: TargetDriftPreset
# Fungsi: Cek apakah distribusi prediksi model bergeser
# Misal: dulu 12% diprediksi tertarik, sekarang 35%
# ============================================================
print("=" * 60)
print("EXPLORASI 2: TargetDriftPreset")
print("Cek apakah output prediksi model bergeser")
print("=" * 60)

report2 = Report(metrics=[TargetDriftPreset()])
report2.run(reference_data=reference, current_data=current)
report2.save_html("2_target_drift.html")

result2 = report2.as_dict()
for m in result2['metrics']:
    res = m.get('result', {})
    if 'drift_score' in res:
        print(f"  Target drift score : {res['drift_score']:.4f}")
        print(f"  Drift terdeteksi?  : {res.get('drift_detected', 'N/A')}")
        break

print()
print("  >> Buka 2_target_drift.html di browser")
print()

# ============================================================
# EXPLORASI 3: DataQualityPreset
# Fungsi: Cek kualitas data (missing values, duplikat, outlier)
# ============================================================
print("=" * 60)
print("EXPLORASI 3: DataQualityPreset")
print("Cek kualitas data: missing, duplikat, outlier")
print("=" * 60)

report3 = Report(metrics=[DataQualityPreset()])
report3.run(reference_data=reference, current_data=current)
report3.save_html("3_data_quality.html")

result3 = report3.as_dict()
for m in result3['metrics']:
    res = m.get('result', {})
    curr = res.get('current', {})
    if 'number_of_rows' in curr:
        print(f"  Jumlah rows        : {curr.get('number_of_rows', 'N/A')}")
        print(f"  Missing values     : {curr.get('number_of_missing_values', 'N/A')}")
        print(f"  Duplicated rows    : {curr.get('number_of_duplicated_rows', 'N/A')}")
        break

print()
print("  >> Buka 3_data_quality.html di browser")
print()

# ============================================================
# EXPLORASI 4: ColumnDriftMetric (per fitur individual)
# Fungsi: Monitor fitur tertentu saja yang paling penting
# ============================================================
print("=" * 60)
print("EXPLORASI 4: ColumnDriftMetric (monitor fitur spesifik)")
print("Bisa pilih fitur mana yang mau dimonitor")
print("=" * 60)

report4 = Report(metrics=[
    ColumnDriftMetric(column_name='Age'),
    ColumnDriftMetric(column_name='AnnualPremium'),
    ColumnDriftMetric(column_name='Gender'),
])
report4.run(reference_data=reference, current_data=current)
report4.save_html("4_per_fitur.html")

result4 = report4.as_dict()
for m in result4['metrics']:
    res = m.get('result', {})
    col = res.get('column_name', '')
    score = res.get('drift_score')
    if score is not None:
        detected = res.get('drift_detected', False)
        tag = "DRIFT!" if detected else "ok"
        print(f"  {col:22s} score={score:.4f}  [{tag}]")

print()
print("  >> Buka 4_per_fitur.html di browser")
print()

# ============================================================
# EXPLORASI 5: Combined report (yang akan dipakai di monitor.yml)
# Ini gabungan dari preset 1 + 2 + 3
# ============================================================
print("=" * 60)
print("EXPLORASI 5: Combined Report (REKOMENDASI untuk monitor.yml)")
print("Gabungan DataDrift + TargetDrift + DataQuality")
print("=" * 60)

report5 = Report(metrics=[
    DataDriftPreset(),
    TargetDriftPreset(),
    DataQualityPreset(),
])
report5.run(reference_data=reference, current_data=current)
report5.save_html("5_combined_monitoring.html")

print("  >> Buka 5_combined_monitoring.html di browser")
print("  >> INI yang nanti dihasilkan monitor.yml setiap hari")
print()

# ============================================================
# EXPLORASI 6: Threshold check (logika di monitor.yml)
# ============================================================
print("=" * 60)
print("EXPLORASI 6: Simulasi threshold check")
print("Ini logika yang jalan di monitor.yml untuk decide retrain")
print("=" * 60)

THRESHOLD = 0.3  # sesuai kesepakatan tim

for m in result['metrics']:
    res = m.get('result', {})
    share = res.get('share_of_drifted_columns')
    if share is not None:
        print(f"  Drift score : {share:.2f}")
        print(f"  Threshold   : {THRESHOLD}")
        print()
        if share > THRESHOLD:
            print("  KEPUTUSAN: DRIFT TERDETEKSI!")
            print("  Yang terjadi otomatis di monitor.yml:")
            print("    1. Upload report HTML ke GCS")
            print("    2. Simpan drift metrics ke BigQuery")
            print("    3. Buat GitHub Issue label 'drift-alert'")
            print("    4. Kirim alert ke Discord")
            print("    5. Trigger ct-train.yml untuk retrain model")
        else:
            print("  KEPUTUSAN: Model masih sehat")
            print("  Report tetap di-upload ke GCS untuk dokumentasi")
        break

print()
print("=" * 60)
print("SELESAI! File HTML yang dihasilkan:")
print("=" * 60)
print("  1_data_drift.html        <- distribusi fitur bergeser?")
print("  2_target_drift.html      <- distribusi prediksi bergeser?")
print("  3_data_quality.html      <- ada data kotor?")
print("  4_per_fitur.html         <- monitor fitur spesifik")
print("  5_combined_monitoring.html <- GABUNGAN (dipakai monitor.yml)")
print()
print("Buka semua file HTML di browser untuk lihat visualisasinya!")
print()
print("=" * 60)
print("YANG RELEVAN UNTUK PROJECT KALIAN:")
print("=" * 60)
print()
print("  WAJIB PAKAI:")
print("    1. DataDriftPreset     -> inti monitoring harian")
print("    2. TargetDriftPreset   -> cek output model berubah")
print("    3. DataQualityPreset   -> cek data kotor")
print()
print("  OPSIONAL:")
print("    4. ColumnDriftMetric   -> monitor fitur tertentu saja")
print("    5. ClassificationPreset -> evaluasi model (butuh ground truth)")
print()
print("  TIDAK RELEVAN:")
print("    - RegressionPreset     -> project kalian classification")
print("    - RecsysPreset         -> bukan recommendation system")
print("    - Text/Embedding       -> bukan NLP project")
