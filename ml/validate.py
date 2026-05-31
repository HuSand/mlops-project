import argparse
import sys
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema, Check


def build_schema(include_target: bool = True) -> DataFrameSchema:
    feature_columns = {
        f"feature_{i}": Column(float, nullable=False)
        for i in range(10)
    }

    target_column = {
    "target": Column(
        float,
        nullable=False,
        checks=[Check.ge(0), Check.le(1)],
    )
}

    schema = DataFrameSchema(
        {
            **feature_columns,
            **(target_column if include_target else {}),
        },
        strict=True if include_target else False,
        coerce=True,
    )
    return schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate dataset CSV using Pandera schema checks."
    )
    parser.add_argument("csv_path", help="Path to the CSV file to validate.")
    parser.add_argument(
        "--no-target",
        action="store_true",
        help="Skip validation of the target column (use for test data).",
    )
    return parser.parse_args()


def print_summary(df: pd.DataFrame) -> None:
    print("Validation succeeded.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {', '.join(df.columns.tolist())}")
    print("\nColumn summary:")
    dtype_info = df.dtypes.astype(str).to_dict()
    null_counts = df.isna().sum().to_dict()
    for column in df.columns:
        print(f"  - {column}: dtype={dtype_info[column]}, nulls={null_counts[column]}")


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv_path)

    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        return 1

    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        print(f"ERROR: Failed to read CSV: {csv_path}\n{exc}")
        return 1

    # Konversi semua kolom ke numeric dulu sebelum validasi
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop baris yang tidak bisa dikonversi
    df = df.dropna().reset_index(drop=True)

    # Pastikan target bertipe int
    if 'target' in df.columns:
        df['target'] = df['target'].astype(int)

    include_target = not args.no_target
    schema = build_schema(include_target=include_target)

    try:
        schema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as exc:
        print("Validation failed with schema errors:")
        for _, row in exc.failure_cases.iterrows():
            print(f"  - Column: {row.get('column')}, Check: {row.get('check')}, "
                  f"Failure: {row.get('failure_case')}")
        return 1
    except pa.errors.SchemaError as exc:
        print(f"Validation failed:\n{exc}")
        return 1
    except Exception as exc:
        print(f"Unexpected error:\n{exc}")
        return 1

    print_summary(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())