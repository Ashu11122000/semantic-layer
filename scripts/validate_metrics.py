
"""
Validate governed business metrics in the PostgreSQL semantic layer.

Checks:
- Gross sales, discounts, and net item revenue
- Estimated product cost, gross profit, and gross margin
- Average order value and customer counts
- Eligible order counts and order return rate
- Revenue and profit reconciliation across semantic views
- Cancelled-order exclusion rules

Exit codes:
    0 = All checks passed
    1 = One or more checks failed
    2 = Configuration or database connection error

This script performs read-only database queries.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# ------------------------------------------------------------
# 1. Configuration
# ------------------------------------------------------------

PROJECT_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")

# Monetary metrics are compared to two decimal places.
# Percentages are compared to two decimal places.
DEFAULT_TOLERANCE = Decimal("0.01")


# ------------------------------------------------------------
# 2. Validation check definition
# ------------------------------------------------------------

@dataclass(frozen=True)
class MetricCheck:
    """Definition of one metric validation check."""

    name: str
    category: str
    sql: str
    expected: Any
    description: str
    tolerance: Decimal = DEFAULT_TOLERANCE


CHECKS: list[MetricCheck] = [
    # --------------------------------------------------------
    # A. Governed revenue metrics
    # --------------------------------------------------------
    MetricCheck(
        name="gross_sales",
        category="revenue",
        sql="""
            SELECT ROUND(SUM(gross_sales), 2)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("48236547.60"),
        description="Eligible gross sales before discounts.",
    ),
    MetricCheck(
        name="total_discounts",
        category="revenue",
        sql="""
            SELECT ROUND(SUM(total_discount), 2)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("3863139.42"),
        description="Total discounts on eligible order lines.",
    ),
    MetricCheck(
        name="net_item_revenue",
        category="revenue",
        sql="""
            SELECT ROUND(SUM(net_item_revenue), 2)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("44373408.18"),
        description="Gross sales minus discounts, excluding shipping.",
    ),

    # --------------------------------------------------------
    # B. Estimated profit metrics
    # --------------------------------------------------------
    MetricCheck(
        name="estimated_product_cost",
        category="profit",
        sql="""
            SELECT ROUND(SUM(estimated_product_cost), 2)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("30185799.68"),
        description="Estimated cost of products sold.",
    ),
    MetricCheck(
        name="estimated_gross_profit",
        category="profit",
        sql="""
            SELECT ROUND(SUM(estimated_gross_profit), 2)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("14187608.50"),
        description="Net item revenue minus estimated product cost.",
    ),
    MetricCheck(
        name="estimated_gross_margin_pct",
        category="profit",
        sql="""
            SELECT ROUND(
                100.0 * SUM(estimated_gross_profit)
                / NULLIF(SUM(net_item_revenue), 0),
                2
            )
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("31.97"),
        description="Estimated gross profit divided by net item revenue.",
    ),

    # --------------------------------------------------------
    # C. Customer metrics
    # --------------------------------------------------------
    MetricCheck(
        name="average_order_value",
        category="customer",
        sql="""
            SELECT ROUND(
                SUM(net_item_revenue)
                / NULLIF(COUNT(DISTINCT order_id), 0),
                2
            )
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("39338.13"),
        description="Net item revenue divided by eligible distinct orders.",
    ),
    MetricCheck(
        name="customers_with_eligible_orders",
        category="customer",
        sql="""
            SELECT COUNT(*)
            FROM semantic.vw_customer_summary
            WHERE order_count > 0
        """,
        expected=338,
        description="Customers with at least one eligible order.",
    ),
    MetricCheck(
        name="total_customers",
        category="customer",
        sql="""
            SELECT COUNT(*)
            FROM semantic.vw_customer_summary
        """,
        expected=350,
        description="All customers, including customers without eligible orders.",
    ),
    MetricCheck(
        name="eligible_orders",
        category="customer",
        sql="""
            SELECT COUNT(DISTINCT order_id)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=1128,
        description="Distinct orders included in sales metrics.",
    ),

    # --------------------------------------------------------
    # D. Return metrics
    # --------------------------------------------------------
    MetricCheck(
        name="distinct_returned_orders",
        category="returns",
        sql="""
            SELECT COUNT(DISTINCT r.order_id)
            FROM raw.returns r
            INNER JOIN raw.orders o
                ON o.order_id = r.order_id
            WHERE LOWER(TRIM(o.order_status)) <> 'cancelled'
        """,
        expected=42,
        description="Distinct eligible orders represented in return records.",
    ),
    MetricCheck(
        name="order_return_rate_pct",
        category="returns",
        sql="""
            WITH eligible_orders AS (
                SELECT DISTINCT order_id
                FROM semantic.vw_order_line_metrics
                WHERE is_sales_eligible
            ),
            returned_orders AS (
                SELECT DISTINCT r.order_id
                FROM raw.returns r
                INNER JOIN eligible_orders eo
                    ON eo.order_id = r.order_id
            )
            SELECT ROUND(
                100.0 * (SELECT COUNT(*) FROM returned_orders)
                / NULLIF(
                    (SELECT COUNT(*) FROM eligible_orders),
                    0
                ),
                2
            )
        """,
        expected=Decimal("3.72"),
        description=(
            "Distinct returned eligible orders divided by all "
            "eligible distinct orders."
        ),
    ),

    # --------------------------------------------------------
    # E. Revenue reconciliation
    # --------------------------------------------------------
    MetricCheck(
        name="sales_customer_revenue_difference",
        category="reconciliation",
        sql="""
            SELECT ROUND(
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_sales_metrics)
                -
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_customer_summary),
                2
            )
        """,
        expected=Decimal("0.00"),
        description="Sales-view revenue must match customer-view revenue.",
    ),
    MetricCheck(
        name="sales_product_revenue_difference",
        category="reconciliation",
        sql="""
            SELECT ROUND(
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_sales_metrics)
                -
                (SELECT SUM(net_item_revenue)
                 FROM semantic.vw_product_performance),
                2
            )
        """,
        expected=Decimal("0.00"),
        description="Sales-view revenue must match product-view revenue.",
    ),

    # --------------------------------------------------------
    # F. Profit reconciliation
    # --------------------------------------------------------
    MetricCheck(
        name="sales_customer_profit_difference",
        category="reconciliation",
        sql="""
            SELECT ROUND(
                (SELECT SUM(estimated_gross_profit)
                 FROM semantic.vw_sales_metrics)
                -
                (SELECT SUM(estimated_gross_profit)
                 FROM semantic.vw_customer_summary),
                2
            )
        """,
        expected=Decimal("0.00"),
        description="Sales-view profit must match customer-view profit.",
    ),
    MetricCheck(
        name="sales_product_profit_difference",
        category="reconciliation",
        sql="""
            SELECT ROUND(
                (SELECT SUM(estimated_gross_profit)
                 FROM semantic.vw_sales_metrics)
                -
                (SELECT SUM(estimated_gross_profit)
                 FROM semantic.vw_product_performance),
                2
            )
        """,
        expected=Decimal("0.00"),
        description="Sales-view profit must match product-view profit.",
    ),

    # --------------------------------------------------------
    # G. Business rules
    # --------------------------------------------------------
    MetricCheck(
        name="revenue_formula_difference",
        category="business_rules",
        sql="""
            SELECT ROUND(
                SUM(gross_sales)
                - SUM(total_discount)
                - SUM(net_item_revenue),
                2
            )
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("0.00"),
        description="Gross sales minus discounts must equal net revenue.",
    ),
    MetricCheck(
        name="profit_formula_difference",
        category="business_rules",
        sql="""
            SELECT ROUND(
                SUM(net_item_revenue)
                - SUM(estimated_product_cost)
                - SUM(estimated_gross_profit),
                2
            )
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        """,
        expected=Decimal("0.00"),
        description="Net revenue minus cost must equal estimated profit.",
    ),
    MetricCheck(
        name="eligible_cancelled_order_lines",
        category="business_rules",
        sql="""
            SELECT COUNT(*)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
              AND LOWER(TRIM(order_status)) = 'cancelled'
        """,
        expected=0,
        description="Cancelled order lines must not be sales-eligible.",
    ),
    MetricCheck(
        name="excluded_cancelled_order_lines",
        category="business_rules",
        sql="""
            SELECT COUNT(*)
            FROM semantic.vw_order_line_metrics
            WHERE NOT is_sales_eligible
              AND LOWER(TRIM(order_status)) = 'cancelled'
        """,
        expected=167,
        description="Expected cancelled order lines excluded from sales.",
    ),
]


# ------------------------------------------------------------
# 3. Comparison helpers
# ------------------------------------------------------------

def to_decimal(value: Any) -> Decimal:
    """Convert numeric values to Decimal for reliable comparisons."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def values_match(actual: Any, check: MetricCheck) -> bool:
    """Compare actual and expected values with a numeric tolerance."""
    if actual is None:
        return check.expected is None

    if isinstance(check.expected, (int, float, Decimal)):
        try:
            actual_number = to_decimal(actual)
            expected_number = to_decimal(check.expected)
            return abs(actual_number - expected_number) <= check.tolerance
        except (InvalidOperation, ValueError, TypeError):
            return False

    return actual == check.expected


def format_value(value: Any) -> str:
    """Format values for readable console output."""
    if value is None:
        return "NULL"
    if isinstance(value, Decimal):
        return f"{value:,.2f}"
    return f"{value:,}" if isinstance(value, int) else str(value)


# ------------------------------------------------------------
# 4. Run checks
# ------------------------------------------------------------

def run_checks(engine: Engine) -> list[dict[str, Any]]:
    """Run each metric check and return detailed results."""
    results: list[dict[str, Any]] = []

    with engine.connect() as connection:
        for check in CHECKS:
            try:
                actual = connection.execute(
                    text(check.sql)
                ).scalar_one()

                passed = values_match(actual, check)

                if actual is not None and isinstance(
                    check.expected, (int, float, Decimal)
                ):
                    difference = (
                        to_decimal(actual) - to_decimal(check.expected)
                    )
                else:
                    difference = None

                results.append({
                    "name": check.name,
                    "category": check.category,
                    "actual": actual,
                    "expected": check.expected,
                    "difference": difference,
                    "status": "PASS" if passed else "FAIL",
                    "description": check.description,
                })

            except Exception as exc:
                results.append({
                    "name": check.name,
                    "category": check.category,
                    "actual": None,
                    "expected": check.expected,
                    "difference": None,
                    "status": "ERROR",
                    "description": f"{check.description} Error: {exc}",
                })

    return results


# ------------------------------------------------------------
# 5. Display summary
# ------------------------------------------------------------

def main() -> int:
    """Application entry point."""
    if not DATABASE_URL:
        print(
            "ERROR: DATABASE_URL is missing. "
            "Check the project-root .env file."
        )
        return 2

    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )
    except Exception as exc:
        print(f"ERROR: Could not configure the database connection: {exc}")
        return 2

    try:
        with engine.connect() as connection:
            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        print(f"Connected to database: {database_name}")
        print(f"Running {len(CHECKS)} governed metric checks...\n")

        results = run_checks(engine)

    except Exception as exc:
        print(f"ERROR: Could not connect to the database: {exc}")
        return 2

    finally:
        engine.dispose()

    print(
        f"{'STATUS':<8} {'CATEGORY':<18} "
        f"{'CHECK':<43} {'ACTUAL':>18} {'EXPECTED':>18}"
    )
    print("-" * 110)

    for result in results:
        print(
            f"{result['status']:<8} "
            f"{result['category']:<18} "
            f"{result['name']:<43} "
            f"{format_value(result['actual']):>18} "
            f"{format_value(result['expected']):>18}"
        )

    passed = sum(r["status"] == "PASS" for r in results)
    failed = sum(r["status"] == "FAIL" for r in results)
    errors = sum(r["status"] == "ERROR" for r in results)

    print("\n========== METRIC VALIDATION SUMMARY ==========")
    print(f"Total checks : {len(results)}")
    print(f"Passed       : {passed}")
    print(f"Failed       : {failed}")
    print(f"Errors       : {errors}")

    if failed or errors:
        print("\nChecks requiring attention:")
        for result in results:
            if result["status"] in {"FAIL", "ERROR"}:
                print(
                    f"- [{result['status']}] {result['name']}: "
                    f"{result['description']}"
                )

        return 1

    print("\nAll governed metric checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
