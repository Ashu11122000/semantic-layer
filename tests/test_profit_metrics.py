"""Automated tests for governed profit metrics."""

from decimal import Decimal

import pytest
from sqlalchemy import Engine, text


# Expected values established during metric validation.
# Update these only when an intentional, documented business/data change
# changes the expected results.
EXPECTED_PRODUCT_COST = Decimal("30185799.68")
EXPECTED_GROSS_PROFIT = Decimal("14187608.50")
EXPECTED_GROSS_MARGIN_PCT = Decimal("31.97")

MONEY_TOLERANCE = Decimal("0.01")
PERCENTAGE_TOLERANCE = Decimal("0.01")


def fetch_scalar(db_engine: Engine, query: str):
    """Execute a SQL query and return its single result."""
    with db_engine.connect() as connection:
        return connection.execute(text(query)).scalar_one()


def as_decimal(value) -> Decimal:
    """Convert a database numeric result to Decimal safely."""
    return Decimal(str(value))


def test_estimated_product_cost(db_engine: Engine):
    """Product cost must match the governed expected value."""
    actual = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(estimated_product_cost), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    assert abs(actual - EXPECTED_PRODUCT_COST) <= MONEY_TOLERANCE, (
        f"Estimated product cost mismatch: "
        f"expected {EXPECTED_PRODUCT_COST}, found {actual}"
    )


def test_estimated_gross_profit(db_engine: Engine):
    """Estimated gross profit must match the governed expected value."""
    actual = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(estimated_gross_profit), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    assert abs(actual - EXPECTED_GROSS_PROFIT) <= MONEY_TOLERANCE, (
        f"Estimated gross profit mismatch: "
        f"expected {EXPECTED_GROSS_PROFIT}, found {actual}"
    )


def test_estimated_gross_margin_percentage(db_engine: Engine):
    """Gross margin must equal gross profit divided by net item revenue."""
    actual = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT
                ROUND(
                    100.0 * SUM(estimated_gross_profit)
                    / NULLIF(SUM(net_item_revenue), 0),
                    2
                )
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    assert abs(actual - EXPECTED_GROSS_MARGIN_PCT) <= (
        PERCENTAGE_TOLERANCE
    ), (
        f"Gross margin mismatch: expected "
        f"{EXPECTED_GROSS_MARGIN_PCT}%, found {actual}%"
    )


def test_profit_formula_at_line_level(db_engine: Engine):
    """Each eligible line must satisfy profit = revenue - product cost."""
    result = fetch_scalar(
        db_engine,
        """
        SELECT COALESCE(
            SUM(
                estimated_gross_profit
                - (net_item_revenue - estimated_product_cost)
            ),
            0
        )
        FROM semantic.vw_order_line_metrics
        WHERE is_sales_eligible
        """,
    )

    difference = as_decimal(result)

    assert abs(difference) <= MONEY_TOLERANCE, (
        f"Line-level profit formula difference: {difference}"
    )


def test_profit_reconciles_with_customer_summary(db_engine: Engine):
    """Eligible gross profit must reconcile across customer summaries."""
    sales_profit = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(estimated_gross_profit), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    customer_profit = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(estimated_gross_profit), 0)
            FROM semantic.vw_customer_summary
            """,
        )
    )

    difference = sales_profit - customer_profit

    assert abs(difference) <= MONEY_TOLERANCE, (
        f"Profit differs between order-line and customer views: "
        f"{difference}"
    )


def test_profit_reconciles_with_product_performance(db_engine: Engine):
    """Eligible gross profit must reconcile across product summaries."""
    sales_profit = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(estimated_gross_profit), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    product_profit = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(estimated_gross_profit), 0)
            FROM semantic.vw_product_performance
            """,
        )
    )

    difference = sales_profit - product_profit

    assert abs(difference) <= MONEY_TOLERANCE, (
        f"Profit differs between order-line and product views: "
        f"{difference}"
    )


def test_cancelled_orders_do_not_contribute_to_profit(db_engine: Engine):
    """Cancelled lines must not be included in eligible profit totals."""
    cancelled_eligible_lines = fetch_scalar(
        db_engine,
        """
        SELECT COUNT(*)
        FROM semantic.vw_order_line_metrics
        WHERE LOWER(order_status) = 'cancelled'
          AND is_sales_eligible
        """,
    )

    assert cancelled_eligible_lines == 0, (
        f"Found {cancelled_eligible_lines} cancelled lines "
        "marked as sales-eligible"
    )


@pytest.mark.parametrize(
    ("metric_name", "query", "expected"),
    [
        (
            "eligible_product_cost",
            """
            SELECT COALESCE(SUM(estimated_product_cost), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
            EXPECTED_PRODUCT_COST,
        ),
        (
            "eligible_gross_profit",
            """
            SELECT COALESCE(SUM(estimated_gross_profit), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
            EXPECTED_GROSS_PROFIT,
        ),
    ],
)
def test_profit_metrics_are_non_negative(
    db_engine: Engine,
    metric_name: str,
    query: str,
    expected: Decimal,
):
    """Validate that the current governed totals are non-negative."""
    actual = as_decimal(fetch_scalar(db_engine, query))

    assert actual >= 0, (
        f"{metric_name} must not be negative; found {actual}"
    )
    assert abs(actual - expected) <= MONEY_TOLERANCE, (
        f"{metric_name} differs from its expected governed value: "
        f"expected {expected}, found {actual}"
    )