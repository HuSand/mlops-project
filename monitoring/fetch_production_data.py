"""
Fetch production prediction logs dari BigQuery.
Digunakan oleh monitor.yml untuk mendapatkan data 'current' untuk drift detection.
"""

import argparse
import pandas as pd
from google.cloud import bigquery


def fetch_data(project_id: str, output_path: str, days: int = 1):
    """
    Query prediction logs dari BigQuery.
    Mengambil data dari tabel mlops.prediction_logs.
    """
    client = bigquery.Client(project=project_id)

    # Query untuk mengambil logs terbaru
    # Sesuaikan nama kolom dengan schema di BigQuery kalian
    query = f"""
        SELECT 
            input_payload
        FROM 
            `{project_id}.mlops.prediction_logs`
        WHERE 
            timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
    """

    print(f"Executing query on {project_id}...")
    query_job = client.query(query)
    results = query_job.to_dataframe()

    if results.empty:
        print("No production data found in the last 24 hours.")
        # Buat dummy data agar pipeline tidak crash (opsional, tergantung kebijakan)
        # Atau raise error
        return

    # input_payload biasanya disimpan sebagai string JSON di BQ
    # Kita perlu unpack menjadi kolom-kolom dataframe
    import json
    
    # Unpack JSON strings
    rows = []
    for _, row in results.iterrows():
        payload = row['input_payload']
        if isinstance(payload, str):
            rows.append(json.loads(payload))
        else:
            rows.append(payload)
            
    df = pd.DataFrame(rows)

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Fetched {len(df)} rows and saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--days", type=int, default=1)
    args = parser.parse_args()
    fetch_data(args.project_id, args.output, args.days)
