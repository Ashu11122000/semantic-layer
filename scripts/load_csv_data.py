
"""
Load the seven e-commerce CSV files into PostgreSQL raw tables.

Run from the project root:
    uv run python scripts/load_csv_data.py

By default, this script refuses to load if any target table
already contains data. Use --replace to reload all tables
from the CSV source files.
"""

import argparse
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

TABLES = {
    "customers": [
        "customer_id", "customer_name", "segment",
        "city", "region", "signup_date",
    ],
    "products": [
        "product_id", "product_name", "category",
        "unit_price", "unit_cost", "active_flag",
    ],
    "orders": [
        "order_id", "customer_id", "order_date",
        "order_status", "shipping_fee", "ship_date",
        "delivery_date",
    ],
    "order_items": [
        "order_item_id", "order_id", "product_id",
        "quantity", "unit_price_at_sale",
        "unit_cost_at_sale", "discount_amount",
    ],
    "payments": [
        "payment_id", "order_id", "payment_method",
        "payment_status", "payment_date",
    ],
    "returns": [
        "return_id", "order_id", "return_date",
        "return_reason",
    ],
    "reviews": [
        "review_id", "order_id", "review_score",
        "review_date",
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing raw-table contents from the CSV files.",
    )
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Check your project .env file."
        )

    # Validate the URL format without printing credentials.
    url = make_url(database_url)
    if url.database != "semantic_layer_db":
        raise RuntimeError(
            "DATABASE_URL must point to semantic_layer_db."
        )

    engine = create_engine(database_url)

    try:
        with engine.connect() as connection:
            current_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if current_database != "semantic_layer_db":
                raise RuntimeError(
                    "Connected to an unexpected database."
                )

            counts = {}
            for table_name in TABLES:
                count = connection.execute(
                    text(f"SELECT COUNT(*) FROM raw.{table_name}")
                ).scalar_one()
                counts[table_name] = count

        existing_tables = [
            table for table, count in counts.items() if count > 0
        ]

        if existing_tables and not args.replace:
            raise RuntimeError(
                "Some raw tables already contain data: "
                + ", ".join(existing_tables)
                + ". No data was changed. To reload all tables from "
                "the CSVs, rerun with --replace."
            )

        # Validate the source files before changing database contents.
        for table_name, columns in TABLES.items():
            csv_path = DATA_DIR / f"{table_name}.csv"

            if not csv_path.is_file():
                raise FileNotFoundError(
                    f"CSV file not found: {csv_path}"
                )

            with csv_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                reader = csv.reader(file)
                header = next(reader, None)

                if header != columns:
                    raise ValueError(
                        f"Unexpected headers in {csv_path.name}.\n"
                        f"Expected: {columns}\n"
                        f"Found:    {header}"
                    )

                for line_number, row in enumerate(reader, start=2):
                    if len(row) != len(columns):
                        raise ValueError(
                            f"{csv_path.name}, line {line_number}: "
                            f"expected {len(columns)} fields, "
                            f"found {len(row)}."
                        )

        # Load all tables in one transaction. Any failure rolls back
        # the replacement and all COPY operations.
        raw_connection = engine.raw_connection()

        try:
            cursor = raw_connection.cursor()

            try:
                if args.replace:
                    cursor.execute(
                        "TRUNCATE TABLE "
                        "raw.reviews, raw.returns, raw.payments, "
                        "raw.order_items, raw.orders, "
                        "raw.products, raw.customers"
                    )

                loaded_counts = {}

                for table_name, columns in TABLES.items():
                    csv_path = DATA_DIR / f"{table_name}.csv"
                    column_list = ", ".join(
                        f'"{column}"' for column in columns
                    )

                    copy_sql = (
                        f"COPY raw.{table_name} ({column_list}) "
                        "FROM STDIN WITH "
                        "(FORMAT CSV, HEADER TRUE, NULL '')"
                    )

                    with csv_path.open("rb") as file:
                        with cursor.copy(copy_sql) as copy:
                            copy.write(file.read())

                    cursor.execute(
                        f"SELECT COUNT(*) FROM raw.{table_name}"
                    )
                    loaded_counts[table_name] = cursor.fetchone()[0]

                raw_connection.commit()

            except Exception:
                raw_connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            raw_connection.close()

        print("CSV loading completed successfully.")
        print(f"Database: {current_database}")
        print("\nRows in raw tables:")

        for table_name, count in loaded_counts.items():
            print(f"  raw.{table_name}: {count:,}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
