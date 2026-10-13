
"""
Profile the raw e-commerce dataset stored in PostgreSQL.

Outputs:
    reports/dataset_profile.csv
    reports/numeric_statistics.csv
    reports/categorical_distributions.csv

The script is read-only. It does not modify database tables or records.
"""

from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql.sqltypes import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    SmallInteger,
)


# ------------------------------------------------------------
# 1. Configuration
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

PROFILE_FILE = REPORTS_DIR / "dataset_profile.csv"
NUMERIC_FILE = REPORTS_DIR / "numeric_statistics.csv"
CATEGORICAL_FILE = REPORTS_DIR / "categorical_distributions.csv"

load_dotenv(PROJECT_ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")

# Fixed allowlist: the script profiles only these raw tables.
RAW_TABLES = [
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "returns",
    "reviews",
]

SCHEMA_NAME = "raw"
MAX_CATEGORICAL_VALUES = 30
TOP_CATEGORIES = 10

PROFILE_FIELDS = [
    "run_timestamp_utc",
    "schema_name",
    "table_name",
    "row_count",
    "column_name",
    "data_type",
    "null_count",
    "non_null_count",
    "completeness_pct",
    "distinct_non_null_values",
    "uniqueness_pct",
]

NUMERIC_FIELDS = [
    "run_timestamp_utc",
    "schema_name",
    "table_name",
    "column_name",
    "data_type",
    "non_null_count",
    "minimum",
    "maximum",
    "average",
    "standard_deviation",
]

CATEGORICAL_FIELDS = [
    "run_timestamp_utc",
    "schema_name",
    "table_name",
    "column_name",
    "value",
    "value_count",
    "percentage_of_non_null_values",
]


# ------------------------------------------------------------
# 2. CSV helpers
# ------------------------------------------------------------

def csv_value(value: Any) -> str:
    """Convert a Python or database value into a CSV-safe string."""
    if value is None:
        return ""

    if isinstance(value, Decimal):
        return format(value, "f")

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, Any]],
) -> None:
    """Write rows to a UTF-8 CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                field: csv_value(row.get(field))
                for field in fieldnames
            })


# ------------------------------------------------------------
# 3. Profiling helpers
# ------------------------------------------------------------

def quote_identifier(engine: Engine, identifier: str) -> str:
    """Safely quote a database identifier."""
    return engine.dialect.identifier_preparer.quote(identifier)


def is_numeric_type(column_type: Any) -> bool:
    """Return True for supported numeric SQLAlchemy column types."""
    return isinstance(
        column_type,
        (Integer, SmallInteger, Float, Numeric),
    )


def is_categorical_type(column_type: Any) -> bool:
    """Identify types suitable for value-distribution profiling."""
    return isinstance(column_type, (Boolean, Date))


def profile_table(
    engine: Engine,
    table_name: str,
    run_timestamp: str,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Profile one raw table and return three sets of results."""

    inspector = inspect(engine)

    if not inspector.has_table(table_name, schema=SCHEMA_NAME):
        raise RuntimeError(
            f"Required table {SCHEMA_NAME}.{table_name} does not exist."
        )

    columns = inspector.get_columns(table_name, schema=SCHEMA_NAME)

    if not columns:
        raise RuntimeError(
            f"No columns found for {SCHEMA_NAME}.{table_name}."
        )

    schema_sql = quote_identifier(engine, SCHEMA_NAME)
    table_sql = quote_identifier(engine, table_name)
    qualified_table = f"{schema_sql}.{table_sql}"

    profile_rows: list[dict[str, Any]] = []
    numeric_rows: list[dict[str, Any]] = []
    categorical_rows: list[dict[str, Any]] = []

    with engine.connect() as connection:
        row_count = int(
            connection.execute(
                text(f"SELECT COUNT(*) FROM {qualified_table}")
            ).scalar_one()
        )

        print(
            f"Profiling {SCHEMA_NAME}.{table_name}: "
            f"{row_count} rows, {len(columns)} columns"
        )

        for column in columns:
            column_name = column["name"]
            column_type = column["type"]

            column_sql = quote_identifier(engine, column_name)

            # Count nulls and distinct non-null values.
            column_stats = connection.execute(
                text(
                    f"""
                    SELECT
                        COUNT(*) FILTER (
                            WHERE {column_sql} IS NULL
                        ) AS null_count,
                        COUNT(DISTINCT {column_sql})
                            AS distinct_non_null_values
                    FROM {qualified_table}
                    """
                )
            ).mappings().one()

            null_count = int(column_stats["null_count"])
            distinct_count = int(
                column_stats["distinct_non_null_values"]
            )
            non_null_count = row_count - null_count

            completeness_pct = (
                round(non_null_count * 100 / row_count, 2)
                if row_count
                else 0.0
            )

            uniqueness_pct = (
                round(distinct_count * 100 / non_null_count, 2)
                if non_null_count
                else 0.0
            )

            profile_rows.append({
                "run_timestamp_utc": run_timestamp,
                "schema_name": SCHEMA_NAME,
                "table_name": table_name,
                "row_count": row_count,
                "column_name": column_name,
                "data_type": str(column_type),
                "null_count": null_count,
                "non_null_count": non_null_count,
                "completeness_pct": completeness_pct,
                "distinct_non_null_values": distinct_count,
                "uniqueness_pct": uniqueness_pct,
            })

            # Numeric descriptive statistics.
            if is_numeric_type(column_type):
                numeric_stats = connection.execute(
                    text(
                        f"""
                        SELECT
                            MIN({column_sql}) AS minimum,
                            MAX({column_sql}) AS maximum,
                            AVG({column_sql}) AS average,
                            STDDEV_POP({column_sql})
                                AS standard_deviation
                        FROM {qualified_table}
                        """
                    )
                ).mappings().one()

                numeric_rows.append({
                    "run_timestamp_utc": run_timestamp,
                    "schema_name": SCHEMA_NAME,
                    "table_name": table_name,
                    "column_name": column_name,
                    "data_type": str(column_type),
                    "non_null_count": non_null_count,
                    "minimum": numeric_stats["minimum"],
                    "maximum": numeric_stats["maximum"],
                    "average": numeric_stats["average"],
                    "standard_deviation":
                        numeric_stats["standard_deviation"],
                })

            # Profile distributions only for selected low-cardinality
            # categorical types. Avoid exporting high-cardinality text
            # values such as customer names or identifiers.
            should_profile_categories = (
                is_categorical_type(column_type)
                or (
                    distinct_count <= MAX_CATEGORICAL_VALUES
                    and not is_numeric_type(column_type)
                    and column_name.lower()
                    not in {
                        "customer_id",
                        "product_id",
                        "order_id",
                        "order_item_id",
                        "payment_id",
                        "return_id",
                        "review_id",
                    }
                )
            )

            if (
                should_profile_categories
                and distinct_count > 0
                and distinct_count <= MAX_CATEGORICAL_VALUES
            ):
                distribution = connection.execute(
                    text(
                        f"""
                        SELECT
                            {column_sql} AS value,
                            COUNT(*) AS value_count
                        FROM {qualified_table}
                        WHERE {column_sql} IS NOT NULL
                        GROUP BY {column_sql}
                        ORDER BY COUNT(*) DESC, {column_sql}
                        LIMIT :top_n
                        """
                    ),
                    {"top_n": TOP_CATEGORIES},
                ).mappings().all()

                for item in distribution:
                    value_count = int(item["value_count"])

                    categorical_rows.append({
                        "run_timestamp_utc": run_timestamp,
                        "schema_name": SCHEMA_NAME,
                        "table_name": table_name,
                        "column_name": column_name,
                        "value": item["value"],
                        "value_count": value_count,
                        "percentage_of_non_null_values": (
                            round(
                                value_count * 100 / non_null_count,
                                2,
                            )
                            if non_null_count
                            else 0.0
                        ),
                    })

    return profile_rows, numeric_rows, categorical_rows


# ------------------------------------------------------------
# 4. Main program
# ------------------------------------------------------------

def main() -> int:
    """Profile all configured raw tables and export CSV reports."""

    if not DATABASE_URL:
        print(
            "ERROR: DATABASE_URL is missing. "
            "Check the .env file in the project root."
        )
        return 2

    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )
    except Exception as exc:
        print(f"ERROR: Could not configure database connection: {exc}")
        return 2

    profile_rows: list[dict[str, Any]] = []
    numeric_rows: list[dict[str, Any]] = []
    categorical_rows: list[dict[str, Any]] = []

    run_timestamp = datetime.now(timezone.utc).isoformat()

    try:
        with engine.connect() as connection:
            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        print(f"Connected to database: {database_name}")
        print(f"Profiling schema: {SCHEMA_NAME}")

        for table_name in RAW_TABLES:
            table_profile, table_numeric, table_categorical = (
                profile_table(engine, table_name, run_timestamp)
            )

            profile_rows.extend(table_profile)
            numeric_rows.extend(table_numeric)
            categorical_rows.extend(table_categorical)

    except Exception as exc:
        print(f"ERROR: Dataset profiling failed: {exc}")
        return 1

    finally:
        engine.dispose()

    try:
        write_csv(PROFILE_FILE, PROFILE_FIELDS, profile_rows)
        write_csv(NUMERIC_FILE, NUMERIC_FIELDS, numeric_rows)
        write_csv(CATEGORICAL_FILE, CATEGORICAL_FIELDS, categorical_rows)

    except OSError as exc:
        print(f"ERROR: Could not write profiling reports: {exc}")
        return 2

    total_rows = sum(
        1 for row in profile_rows if row["column_name"]
    )
    columns_with_nulls = sum(
        int(row["null_count"]) > 0 for row in profile_rows
    )
    columns_with_missing_data = [
        f"{row['table_name']}.{row['column_name']}"
        for row in profile_rows
        if int(row["null_count"]) > 0
    ]

    print("\n========== DATASET PROFILE SUMMARY ==========")
    print(f"Tables profiled            : {len(RAW_TABLES)}")
    print(f"Columns profiled            : {total_rows}")
    print(f"Numeric columns profiled    : {len(numeric_rows)}")
    print(f"Categorical values exported : {len(categorical_rows)}")
    print(f"Columns containing NULLs    : {columns_with_nulls}")

    print("\nReports created:")
    print(f"- {PROFILE_FILE}")
    print(f"- {NUMERIC_FILE}")
    print(f"- {CATEGORICAL_FILE}")

    if columns_with_missing_data:
        print("\nColumns containing NULL values:")
        for column in columns_with_missing_data:
            print(f"- {column}")
    else:
        print("\nNo NULL values found in the profiled columns.")

    print("\nDataset profiling completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
