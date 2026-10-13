"""Automated tests for semantic-layer views."""

from decimal import Decimal

import pytest
from sqlalchemy import Engine, text


MONEY_TOLERANCE = Decimal("0.01")

EXPECTED_VIEW_ROW_COUNTS = {
    "semantic.vw_order_line_metrics": 2908,
    "semantic.vw_sales_metrics": 749,
    "semantic.vw_customer_summary": 350,
    "semantic.vw_product_performance": 26,
    "semantic.vw_return_analysis": 42,
}


def fetch_scalar(db_engine: Engine, query: str):
    """Execute a SQL query and return its single result."""
    with db_engine.connect() as connection:
        return connection.execute(text(query)).scalar_one()


def as_decimal(value) -> Decimal:
    """Convert a database numeric value to Decimal safely."""
    return Decimal(str(value))


# ---------------------------------------------------------
# 1. Semantic view row counts
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("view_name", "expected_count"),
    EXPECTED_VIEW_ROW_COUNTS.items(),
)
def test_semantic_view_row_counts(
    db_engine: Engine,
    view_name: str,
    expected_count: int,
):
    """Verify that each semantic view returns the expected row count."""
    actual_count = fetch_scalar(
        db_engine,
        f"SELECT COUNT(*) FROM {view_name}",
    )

    assert actual_count == expected_count, (
        f"{view_name}: expected {expected_count} rows, "
        f"found {actual_count}"
    )


# ---------------------------------------------------------
# 2. Uniqueness of entity summaries
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("view_name", "identifier"),
    [
        ("semantic.vw_customer_summary", "customer_id"),
        ("semantic.vw_product_performance", "product_id"),
    ],
)
def test_entity_summary_identifiers_are_unique(
    db_engine: Engine,
    view_name: str,
    identifier: str,
):
    """Customer and product summary views should have unique entity IDs."""
    duplicate_count = fetch_scalar(
        db_engine,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT {identifier}
            FROM {view_name}
            GROUP BY {identifier}
            HAVING {identifier} IS NULL OR COUNT(*) > 1
        ) duplicate_groups
        """,
    )

    assert duplicate_count == 0, (
        f"{view_name} contains {duplicate_count} duplicate/null "
        f"{identifier} groups"
    )


# ---------------------------------------------------------
# 3. Revenue reconciliation
# ---------------------------------------------------------

def test_revenue_reconciles_across_semantic_views(db_engine: Engine):
    """Eligible net item revenue must agree across line, customer,
    and product views.
    """
    result = fetch_scalar(
        db_engine,
        """
        WITH line_totals AS (
            SELECT COALESCE(SUM(net_item_revenue), 0) AS revenue
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        ),
        customer_totals AS (
            SELECT COALESCE(SUM(net_item_revenue), 0) AS revenue
            FROM semantic.vw_customer_summary
        ),
        product_totals AS (
            SELECT COALESCE(SUM(net_item_revenue), 0) AS revenue
            FROM semantic.vw_product_performance
        )
        SELECT
            GREATEST(
                ABS(line_totals.revenue - customer_totals.revenue),
                ABS(line_totals.revenue - product_totals.revenue)
            )
        FROM line_totals
        CROSS JOIN customer_totals
        CROSS JOIN product_totals
        """,
    )

    difference = as_decimal(result)

    assert difference <= MONEY_TOLERANCE, (
        f"Revenue reconciliation difference: {difference}"
    )


# ---------------------------------------------------------
# 4. Profit reconciliation
# ---------------------------------------------------------

def test_profit_reconciles_across_semantic_views(db_engine: Engine):
    """Eligible estimated gross profit must agree across summaries."""
    result = fetch_scalar(
        db_engine,
        """
        WITH line_totals AS (
            SELECT COALESCE(SUM(estimated_gross_profit), 0) AS profit
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
        ),
        customer_totals AS (
            SELECT COALESCE(SUM(estimated_gross_profit), 0) AS profit
            FROM semantic.vw_customer_summary
        ),
        product_totals AS (
            SELECT COALESCE(SUM(estimated_gross_profit), 0) AS profit
            FROM semantic.vw_product_performance
        )
        SELECT
            GREATEST(
                ABS(line_totals.profit - customer_totals.profit),
                ABS(line_totals.profit - product_totals.profit)
            )
        FROM line_totals
        CROSS JOIN customer_totals
        CROSS JOIN product_totals
        """,
    )

    difference = as_decimal(result)

    assert difference <= MONEY_TOLERANCE, (
        f"Profit reconciliation difference: {difference}"
    )


# ---------------------------------------------------------
# 5. Cancelled-order business rule
# ---------------------------------------------------------

def test_cancelled_order_lines_are_not_sales_eligible(
    db_engine: Engine,
):
    """Cancelled order lines must not be marked as eligible for sales."""
    count = fetch_scalar(
        db_engine,
        """
        SELECT COUNT(*)
        FROM semantic.vw_order_line_metrics
        WHERE LOWER(order_status) = 'cancelled'
          AND is_sales_eligible
        """,
    )

    assert count == 0, (
        f"Found {count} cancelled order lines marked as sales-eligible"
    )


def test_cancelled_order_lines_are_excluded_from_sales_totals(
    db_engine: Engine,
):
    """All cancelled order lines must be excluded by the eligibility flag."""
    result = fetch_scalar(
        db_engine,
        """
        SELECT COUNT(*)
        FROM semantic.vw_order_line_metrics
        WHERE LOWER(order_status) = 'cancelled'
          AND NOT is_sales_eligible
        """,
    )

    assert result == 167, (
        f"Expected 167 cancelled order lines to be excluded, found {result}"
    )


# ---------------------------------------------------------
# 6. Customer and product coverage
# ---------------------------------------------------------

def test_customer_summary_includes_all_customers(db_engine: Engine):
    """The customer summary should retain customers with no eligible orders."""
    total_customers = fetch_scalar(
        db_engine,
        "SELECT COUNT(*) FROM raw.customers",
    )

    summary_customers = fetch_scalar(
        db_engine,
        "SELECT COUNT(*) FROM semantic.vw_customer_summary",
    )

    assert summary_customers == total_customers, (
        f"Expected {total_customers} customer records in the summary, "
        f"found {summary_customers}"
    )


def test_product_performance_includes_all_products(db_engine: Engine):
    """The product view should contain every source product."""
    total_products = fetch_scalar(
        db_engine,
        "SELECT COUNT(*) FROM raw.products",
    )

    summary_products = fetch_scalar(
        db_engine,
        "SELECT COUNT(*) FROM semantic.vw_product_performance",
    )

    assert summary_products == total_products, (
        f"Expected {total_products} products in the performance view, "
        f"found {summary_products}"
    )


# ---------------------------------------------------------
# 7. Return-analysis coverage
# ---------------------------------------------------------

def test_return_analysis_covers_all_return_records(db_engine: Engine):
    """Every source return record should appear in return analysis."""
    source_returns = fetch_scalar(
        db_engine,
        "SELECT COUNT(*) FROM raw.returns",
    )

    analyzed_returns = fetch_scalar(
        db_engine,
        "SELECT COUNT(*) FROM semantic.vw_return_analysis",
    )

    assert analyzed_returns == source_returns, (
        f"Expected {source_returns} return records, "
        f"found {analyzed_returns}"
    )