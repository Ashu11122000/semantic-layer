
"""
Export semantic-layer validation results to CSV reports.

Project: PostgreSQL Semantic Layer
Outputs:
    reports/validation_results.csv
    reports/validation_discrepancies.csv

The script performs read-only SQL checks against the existing database.
It does not modify source tables, semantic views, or security policies.
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# ------------------------------------------------------------
# 1. Project configuration
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

RESULTS_FILE = REPORTS_DIR / "validation_results.csv"
DISCREPANCIES_FILE = REPORTS_DIR / "validation_discrepancies.csv"

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = __import__("os").getenv("DATABASE_URL")

CSV_FIELDS = [
    "run_timestamp_utc",
    "category",
    "check_name",
    "actual_value",
    "expected_value",
    "difference",
    "status",
    "details",
]


# ------------------------------------------------------------
# 2. SQL validation checks
# ------------------------------------------------------------

CHECKS: list[dict[str, Any]] = [
    # --------------------------------------------------------
    # A. Raw table row counts
    # --------------------------------------------------------
    {
        "category": "row_counts",
        "name": "customers_row_count",
        "sql": "SELECT COUNT(*) FROM raw.customers",
        "expected": 350,
        "details": "Expected number of customer records.",
    },
    {
        "category": "row_counts",
        "name": "products_row_count",
        "sql": "SELECT COUNT(*) FROM raw.products",
        "expected": 26,
        "details": "Expected number of product records.",
    },
    {
        "category": "row_counts",
        "name": "orders_row_count",
        "sql": "SELECT COUNT(*) FROM raw.orders",
        "expected": 1200,
        "details": "Expected number of order records.",
    },
    {
        "category": "row_counts",
        "name": "order_items_row_count",
        "sql": "SELECT COUNT(*) FROM raw.order_items",
        "expected": 2908,
        "details": "Expected number of order-line records.",
    },
    {
        "category": "row_counts",
        "name": "payments_row_count",
        "sql": "SELECT COUNT(*) FROM raw.payments",
        "expected": 1200,
        "details": "Expected number of payment records.",
    },
    {
        "category": "row_counts",
        "name": "returns_row_count",
        "sql": "SELECT COUNT(*) FROM raw.returns",
        "expected": 42,
        "details": "Expected number of return records.",
    },
    {
        "category": "row_counts",
        "name": "reviews_row_count",
        "sql": "SELECT COUNT(*) FROM raw.reviews",
        "expected": 650,
        "details": "Expected number of review records.",
    },

    # --------------------------------------------------------
    # B. Primary-key uniqueness
    # --------------------------------------------------------
    {
        "category": "data_quality",
        "name": "duplicate_customer_ids",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT customer_id
                FROM raw.customers
                GROUP BY customer_id
                HAVING COUNT(*) > 1
            ) AS duplicates
        """,
        "expected": 0,
        "details": "Duplicate customer identifier groups.",
    },
    {
        "category": "data_quality",
        "name": "duplicate_product_ids",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT product_id
                FROM raw.products
                GROUP BY product_id
                HAVING COUNT(*) > 1
            ) AS duplicates
        """,
        "expected": 0,
        "details": "Duplicate product identifier groups.",
    },
    {
        "category": "data_quality",
        "name": "duplicate_order_ids",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT order_id
                FROM raw.orders
                GROUP BY order_id
                HAVING COUNT(*) > 1
            ) AS duplicates
        """,
        "expected": 0,
        "details": "Duplicate order identifier groups.",
    },
    {
        "category": "data_quality",
        "name": "duplicate_order_item_ids",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT order_item_id
                FROM raw.order_items
                GROUP BY order_item_id
                HAVING COUNT(*) > 1
            ) AS duplicates
        """,
        "expected": 0,
        "details": "Duplicate order-item identifier groups.",
    },
    {
        "category": "data_quality",
        "name": "duplicate_payment_ids",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT payment_id
                FROM raw.payments
                GROUP BY payment_id
                HAVING COUNT(*) > 1
            ) AS duplicates
        """,
        "expected": 0,
        "details": "Duplicate payment identifier groups.",
    },
    {
        "category": "data_quality",
        "name": "duplicate_return_ids",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT return_id
                FROM raw.returns
                GROUP BY return_id
                HAVING COUNT(*) > 1
            ) AS duplicates
        """,
        "expected": 0,
        "details": "Duplicate return identifier groups.",
    },
    {
        "category": "data_quality",
        "name": "duplicate_review_ids",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT review_id
                FROM raw.reviews
                GROUP BY review_id
                HAVING COUNT(*) > 1
            ) AS duplicates
        """,
        "expected": 0,
        "details": "Duplicate review identifier groups.",
    },

    # --------------------------------------------------------
    # C. Required identifiers
    # --------------------------------------------------------
    {
        "category": "data_quality",
        "name": "missing_customer_ids",
        "sql": """
            SELECT COUNT(*) FROM raw.customers
            WHERE customer_id IS NULL OR BTRIM(customer_id) = ''
        """,
        "expected": 0,
        "details": "Customers with missing identifiers.",
    },
    {
        "category": "data_quality",
        "name": "missing_product_ids",
        "sql": """
            SELECT COUNT(*) FROM raw.products
            WHERE product_id IS NULL OR BTRIM(product_id) = ''
        """,
        "expected": 0,
        "details": "Products with missing identifiers.",
    },
    {
        "category": "data_quality",
        "name": "missing_order_ids",
        "sql": """
            SELECT COUNT(*) FROM raw.orders
            WHERE order_id IS NULL OR BTRIM(order_id) = ''
        """,
        "expected": 0,
        "details": "Orders with missing identifiers.",
    },
    {
        "category": "data_quality",
        "name": "missing_order_item_ids",
        "sql": """
            SELECT COUNT(*) FROM raw.order_items
            WHERE order_item_id IS NULL
               OR BTRIM(order_item_id) = ''
        """,
        "expected": 0,
        "details": "Order items with missing identifiers.",
    },
    {
        "category": "data_quality",
        "name": "missing_payment_ids",
        "sql": """
            SELECT COUNT(*) FROM raw.payments
            WHERE payment_id IS NULL OR BTRIM(payment_id) = ''
        """,
        "expected": 0,
        "details": "Payments with missing identifiers.",
    },
    {
        "category": "data_quality",
        "name": "missing_return_ids",
        "sql": """
            SELECT COUNT(*) FROM raw.returns
            WHERE return_id IS NULL OR BTRIM(return_id) = ''
        """,
        "expected": 0,
        "details": "Returns with missing identifiers.",
    },
    {
        "category": "data_quality",
        "name": "missing_review_ids",
        "sql": """
            SELECT COUNT(*) FROM raw.reviews
            WHERE review_id IS NULL OR BTRIM(review_id) = ''
        """,
        "expected": 0,
        "details": "Reviews with missing identifiers.",
    },

    # --------------------------------------------------------
    # D. Business-value checks
    # --------------------------------------------------------
    {
        "category": "data_quality",
        "name": "invalid_quantities",
        "sql": """
            SELECT COUNT(*) FROM raw.order_items
            WHERE quantity IS NULL OR quantity <= 0
        """,
        "expected": 0,
        "details": "Order items with null or non-positive quantities.",
    },
    {
        "category": "data_quality",
        "name": "negative_unit_prices",
        "sql": """
            SELECT COUNT(*) FROM raw.order_items
            WHERE unit_price_at_sale < 0
        """,
        "expected": 0,
        "details": "Order items with negative historical unit prices.",
    },
    {
        "category": "data_quality",
        "name": "negative_unit_costs",
        "sql": """
            SELECT COUNT(*) FROM raw.order_items
            WHERE unit_cost_at_sale < 0
        """,
        "expected": 0,
        "details": "Order items with negative historical unit costs.",
    },
    {
        "category": "data_quality",
        "name": "negative_discounts",
        "sql": """
            SELECT COUNT(*) FROM raw.order_items
            WHERE discount_amount < 0
        """,
        "expected": 0,
        "details": "Order items with negative discounts.",
    },
    {
        "category": "data_quality",
        "name": "negative_shipping_fees",
        "sql": """
            SELECT COUNT(*) FROM raw.orders
            WHERE shipping_fee < 0
        """,
        "expected": 0,
        "details": "Orders with negative shipping fees.",
    },
    {
        "category": "data_quality",
        "name": "invalid_review_scores",
        "sql": """
            SELECT COUNT(*) FROM raw.reviews
            WHERE review_score IS NULL
               OR review_score NOT BETWEEN 1 AND 5
        """,
        "expected": 0,
        "details": "Reviews with scores outside the 1-5 scale.",
    },

    # --------------------------------------------------------
    # E. Referential integrity
    # --------------------------------------------------------
    {
        "category": "relationships",
        "name": "orders_missing_customers",
        "sql": """
            SELECT COUNT(*)
            FROM raw.orders o
            LEFT JOIN raw.customers c
                ON c.customer_id = o.customer_id
            WHERE c.customer_id IS NULL
        """,
        "expected": 0,
        "details": "Orders without a matching customer.",
    },
    {
        "category": "relationships",
        "name": "order_items_missing_orders",
        "sql": """
            SELECT COUNT(*)
            FROM raw.order_items oi
            LEFT JOIN raw.orders o ON o.order_id = oi.order_id
            WHERE o.order_id IS NULL
        """,
        "expected": 0,
        "details": "Order items without a matching order.",
    },
    {
        "category": "relationships",
        "name": "order_items_missing_products",
        "sql": """
            SELECT COUNT(*)
            FROM raw.order_items oi
            LEFT JOIN raw.products p ON p.product_id = oi.product_id
            WHERE p.product_id IS NULL
        """,
        "expected": 0,
        "details": "Order items without a matching product.",
    },
    {
        "category": "relationships",
        "name": "payments_missing_orders",
        "sql": """
            SELECT COUNT(*)
            FROM raw.payments p
            LEFT JOIN raw.orders o ON o.order_id = p.order_id
            WHERE o.order_id IS NULL
        """,
        "expected": 0,
        "details": "Payments without a matching order.",
    },
    {
        "category": "relationships",
        "name": "returns_missing_orders",
        "sql": """
            SELECT COUNT(*)
            FROM raw.returns r
            LEFT JOIN raw.orders o ON o.order_id = r.order_id
            WHERE o.order_id IS NULL
        """,
        "expected": 0,
        "details": "Returns without a matching order.",
    },
    {
        "category": "relationships",
        "name": "reviews_missing_orders",
        "sql": """
            SELECT COUNT(*)
            FROM raw.reviews r
            LEFT JOIN raw.orders o ON o.order_id = r.order_id
            WHERE o.order_id IS NULL
        """,
        "expected": 0,
        "details": "Reviews without a matching order.",
    },

    # --------------------------------------------------------
    # F. Semantic view row counts
    # --------------------------------------------------------
    {
        "category": "semantic_views",
        "name": "order_line_view_row_count",
        "sql": "SELECT COUNT(*) FROM semantic.vw_order_line_metrics",
        "expected": 2908,
        "details": "Expected rows in the order-line metrics view.",
    },
    {
        "category": "semantic_views",
        "name": "sales_view_row_count",
        "sql": "SELECT COUNT(*) FROM semantic.vw_sales_metrics",
        "expected": 749,
        "details": "Expected daily sales/status summary rows.",
    },
    {
        "category": "semantic_views",
        "name": "customer_view_row_count",
        "sql": "SELECT COUNT(*) FROM semantic.vw_customer_summary",
        "expected": 350,
        "details": "Expected customer summary rows.",
    },
    {
        "category": "semantic_views",
        "name": "product_view_row_count",
        "sql": "SELECT COUNT(*) FROM semantic.vw_product_performance",
        "expected": 26,
        "details": "Expected product performance rows.",
    },
    {
        "category": "semantic_views",
        "name": "return_view_row_count",
        "sql": "SELECT COUNT(*) FROM semantic.vw_return_analysis",
        "expected": 42,
        "details": "Expected return analysis rows.",
    },
    {
        "category": "semantic_views",
        "name": "duplicate_customer_summary_ids",
        "sql": """
            SELECT COUNT(*) FROM (
                SELECT customer_id
                FROM semantic.vw_customer_summary
                GROUP BY customer_id
                HAVING COUNT(*) > 1
            ) d
        """,
        "expected": 0,
        "details": "Duplicate customer IDs in customer summary.",
    },
    {
        "category": "semantic_views",
        "name": "duplicate_product_performance_ids",
        "sql": """
            SELECT COUNT(*) FROM (
                SELECT product_id
                FROM semantic.vw_product_performance
                GROUP BY product_id
                HAVING COUNT(*) > 1
            ) d
        """,
        "expected": 0,
        "details": "Duplicate product IDs in product performance.",
    },

    # --------------------------------------------------------
    # G. Revenue reconciliation
    # --------------------------------------------------------
    {
        "category": "revenue",
        "name": "gross_sales_reconciliation",
        "sql": """
            SELECT ROUND(
                COALESCE(
                    (SELECT SUM(gross_sales)
                     FROM semantic.vw_order_line_metrics
                     WHERE is_sales_eligible), 0
                )
                -
                COALESCE(
                    (SELECT SUM(gross_sales)
                     FROM semantic.vw_sales_metrics), 0
                ), 2
            )
        """,
        "expected": Decimal("0.00"),
        "details": "Order-line gross sales minus sales-view gross sales.",
    },
    {
        "category": "revenue",
        "name": "discount_reconciliation",
        "sql": """
            SELECT ROUND(
                COALESCE(
                    (SELECT SUM(total_discount)
                     FROM semantic.vw_order_line_metrics
                     WHERE is_sales_eligible), 0
                )
                -
                COALESCE(
                    (SELECT SUM(total_discounts)
                     FROM semantic.vw_sales_metrics), 0
                ), 2
            )
        """,
        "expected": Decimal("0.00"),
        "details": "Order-line discounts minus sales-view discounts.",
    },
    {
        "category": "revenue",
        "name": "net_revenue_reconciliation",
        "sql": """
            SELECT ROUND(
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_order_line_metrics
                 WHERE is_sales_eligible)
                -
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_sales_metrics), 2
            )
        """,
        "expected": Decimal("0.00"),
        "details": "Order-line net revenue minus sales-view net revenue.",
    },
    {
        "category": "revenue",
        "name": "customer_revenue_reconciliation",
        "sql": """
            SELECT ROUND(
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_sales_metrics)
                -
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_customer_summary), 2
            )
        """,
        "expected": Decimal("0.00"),
        "details": "Sales-view revenue minus customer-view revenue.",
    },
    {
        "category": "revenue",
        "name": "product_revenue_reconciliation",
        "sql": """
            SELECT ROUND(
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_sales_metrics)
                -
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_product_performance), 2
            )
        """,
        "expected": Decimal("0.00"),
        "details": "Sales-view revenue minus product-view revenue.",
    },

    # --------------------------------------------------------
    # H. Profit reconciliation
    # --------------------------------------------------------
    {
        "category": "profit",
        "name": "product_cost_reconciliation",
        "sql": """
            SELECT ROUND(
                (SELECT SUM(estimated_product_cost)
                 FROM semantic.vw_order_line_metrics
                 WHERE is_sales_eligible)
                -
                (SELECT SUM(estimated_product_cost)
                 FROM semantic.vw_product_performance), 2
            )
        """,
        "expected": Decimal("0.00"),
        "details": "Order-line cost minus product-view cost.",
    },
    {
        "category": "profit",
        "name": "customer_profit_reconciliation",
        "sql": """
            SELECT ROUND(
                (SELECT SUM(estimated_gross_profit)
                 FROM semantic.vw_sales_metrics)
                -
                (SELECT SUM(estimated_gross_profit)
                 FROM semantic.vw_customer_summary), 2
            )
        """,
        "expected": Decimal("0.00"),
        "details": "Sales-view profit minus customer-view profit.",
    },
    {
        "category": "profit",
        "name": "product_profit_reconciliation",
        "sql": """
            SELECT ROUND(
                (SELECT SUM(estimated_gross_profit)
                 FROM semantic.vw_sales_metrics)
                -
                (SELECT SUM(estimated_gross_profit)
                 FROM semantic.vw_product_performance), 2
            )
        """,
        "expected": Decimal("0.00"),
        "details": "Sales-view profit minus product-view profit.",
    },
    {
        "category": "profit",
        "name": "profit_formula_difference",
        "sql": """
            SELECT ROUND(
                SUM(net_item_revenue)
                - SUM(estimated_product_cost)
                - SUM(estimated_gross_profit), 2
            )
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        "expected": Decimal("0.00"),
        "details": "Revenue minus cost minus estimated gross profit.",
    },
    {
        "category": "profit",
        "name": "estimated_gross_margin_pct",
        "sql": """
            SELECT ROUND(
                100.0 * SUM(estimated_gross_profit)
                / NULLIF(SUM(net_item_revenue), 0), 2
            )
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        "expected": Decimal("31.97"),
        "details": "Estimated gross margin percentage, rounded to two decimals.",
    },

    # --------------------------------------------------------
    # I. Cancelled-order policy
    # --------------------------------------------------------
    {
        "category": "business_rules",
        "name": "eligible_cancelled_order_lines",
        "sql": """
            SELECT COUNT(*)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
              AND LOWER(TRIM(order_status)) = 'cancelled'
        """,
        "expected": 0,
        "details": "Cancelled order lines must not be sales-eligible.",
    },
    {
        "category": "business_rules",
        "name": "excluded_cancelled_order_lines",
        "sql": """
            SELECT COUNT(*)
            FROM semantic.vw_order_line_metrics
            WHERE NOT is_sales_eligible
              AND LOWER(TRIM(order_status)) = 'cancelled'
        """,
        "expected": 167,
        "details": "Expected cancelled order lines excluded from sales.",
    },
]


# ------------------------------------------------------------
# 3. Utility functions
# ------------------------------------------------------------

def display_value(value: Any) -> str:
    """Convert database values into CSV-safe strings."""
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def values_equal(actual: Any, expected: Any) -> bool:
    """Compare SQL results to expected values."""
    if actual is None:
        return expected is None

    if isinstance(expected, Decimal):
        try:
            return Decimal(str(actual)) == expected
        except Exception:
            return False

    return actual == expected


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write validation rows to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# ------------------------------------------------------------
# 4. Run validations
# ------------------------------------------------------------

def run_validations(engine: Engine) -> list[dict[str, Any]]:
    """Execute all SQL checks and collect results."""
    results: list[dict[str, Any]] = []
    run_timestamp = datetime.now(timezone.utc).isoformat()

    with engine.connect() as connection:
        for check in CHECKS:
            try:
                actual = connection.execute(
                    text(check["sql"])
                ).scalar_one()

                expected = check["expected"]
                passed = values_equal(actual, expected)

                results.append({
                    "run_timestamp_utc": run_timestamp,
                    "category": check["category"],
                    "check_name": check["name"],
                    "actual_value": display_value(actual),
                    "expected_value": display_value(expected),
                    "difference": (
                        display_value(
                            Decimal(str(actual)) - expected
                        )
                        if isinstance(expected, Decimal)
                        and actual is not None
                        else ""
                    ),
                    "status": "PASS" if passed else "FAIL",
                    "details": check["details"],
                })

            except Exception as exc:
                results.append({
                    "run_timestamp_utc": run_timestamp,
                    "category": check["category"],
                    "check_name": check["name"],
                    "actual_value": "",
                    "expected_value": display_value(check["expected"]),
                    "difference": "",
                    "status": "ERROR",
                    "details": f"{check['details']} Error: {exc}",
                })

    return results


# ------------------------------------------------------------
# 5. Export reports and print summary
# ------------------------------------------------------------

def main() -> int:
    """Entry point for the validation export script."""
    if not DATABASE_URL:
        print(
            "ERROR: DATABASE_URL was not found. "
            "Check that your project-root .env file defines it."
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

    try:
        with engine.connect() as connection:
            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        print(f"Connected to database: {database_name}")

        results = run_validations(engine)

    except Exception as exc:
        print(f"ERROR: Could not connect to or validate the database: {exc}")
        return 2

    finally:
        engine.dispose()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    discrepancies = [
        row for row in results
        if row["status"] in {"FAIL", "ERROR"}
    ]

    try:
        write_csv(RESULTS_FILE, results)
        write_csv(DISCREPANCIES_FILE, discrepancies)
    except OSError as exc:
        print(f"ERROR: Could not write report files: {exc}")
        return 2

    passed_count = sum(row["status"] == "PASS" for row in results)
    failed_count = sum(row["status"] == "FAIL" for row in results)
    error_count = sum(row["status"] == "ERROR" for row in results)

    print("\n========== VALIDATION SUMMARY ==========")
    print(f"Total checks : {len(results)}")
    print(f"Passed       : {passed_count}")
    print(f"Failed       : {failed_count}")
    print(f"Errors       : {error_count}")
    print(f"Results CSV  : {RESULTS_FILE}")
    print(f"Discrepancies: {DISCREPANCIES_FILE}")

    if discrepancies:
        print("\nChecks requiring attention:")
        for row in discrepancies:
            print(
                f"- [{row['status']}] {row['check_name']}: "
                f"{row['details']}"
            )
        return 1

    print("\nAll validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
