"""
Fetch production prediction logs dari BigQuery.
Digunakan oleh monitor.yml untuk mendapatkan data 'current' untuk drift detection.
"""

import argparse
import json
import pandas as pd
from google.cloud import bigquery


def fetch_data(project_id: str, output_path: str, days: int = 1):
    """
    Query prediction logs dari BigQuery.
    Mengambil data dari tabel mlops.prediction_logs.
    """
    client = bigquery.Client(project=project_id)

    # Query untuk mengambil logs terbaru termasuk kolom prediction
    query = f"""
        SELECT 
            input_payload,
            prediction,
            model_version,
            timestamp
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
        return

    # Unpack JSON strings dari input_payload dan gabungkan dengan kolom lainnya
    rows = []
    for _, row in results.iterrows():
        payload = row['input_payload']
        # Parse payload
        if isinstance(payload, str):
            data_row = json.loads(payload)
        else:
            data_row = payload.copy() if payload else {}
            
        # Tambahkan metadata penting untuk monitoring
        data_row['prediction'] = row['prediction']
        data_row['model_version'] = row['model_version']
        data_row['timestamp'] = str(row['timestamp'])
        
        rows.append(data_row)
            
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
