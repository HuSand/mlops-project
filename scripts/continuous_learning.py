import json
import logging
import pandas as pd
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def fetch_from_bigquery(days: int = 7, project: str = "project-d50e88c7-b681-48d4-b1b") -> pd.DataFrame:
    """Ambil data prediksi dari BigQuery N hari terakhir."""
    client = bigquery.Client(project=project)
    query = f"""
        SELECT input_payload, prediction
        FROM `{project}.mlops.prediction_logs`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        AND JSON_EXTRACT_SCALAR(input_payload, '$.Gender') IS NOT NULL
    """
    logging.info(f"Fetching data from BigQuery ({days} days)...")
    df = client.query(query).to_dataframe()
    logging.info(f"Fetched {len(df)} rows from BigQuery")
    return df


def parse_payload(df: pd.DataFrame) -> pd.DataFrame:
    """Parse kolom input_payload menjadi kolom-kolom terpisah."""
    parsed = pd.json_normalize(df['input_payload'].apply(json.loads))
    parsed['target'] = df['prediction'].values
    return parsed


def merge_with_existing(new_data: pd.DataFrame, train_path: str = "data/train.csv") -> pd.DataFrame:
    """Gabungkan data baru dengan train.csv lama."""
    train = pd.read_csv(train_path)
    logging.info(f"Train size sebelum merge: {len(train)}")
    merged = pd.concat([train, new_data], ignore_index=True)
    merged = merged.drop_duplicates().reset_index(drop=True)
    logging.info(f"Train size setelah merge: {len(merged)}")
    return merged


def main():
    # Fetch dari BigQuery
    raw = fetch_from_bigquery(days=7)
    
    if raw.empty:
        logging.warning("Tidak ada data baru dari BigQuery. Skip.")
        return

    # Parse payload
    new_data = parse_payload(raw)
    logging.info(f"Kolom data baru: {new_data.columns.tolist()}")

    # Merge dengan data lama
    merged = merge_with_existing(new_data, train_path="data/train.csv")

    # Simpan
    merged.to_csv("data/train.csv", index=False)
    logging.info(f"train.csv updated: {len(merged)} rows")


if __name__ == "__main__":
    main()