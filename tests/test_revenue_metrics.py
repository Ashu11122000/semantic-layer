"""Automated tests for governed revenue metrics."""

from decimal import Decimal

import pytest
from sqlalchemy import Engine, text


# Governed expected values validated against the current dataset.
# Change these only when a documented data or business-rule change
# intentionally changes the expected results.
EXPECTED_GROSS_SALES = Decimal("48236547.60")
EXPECTED_TOTAL_DISCOUNTS = Decimal("3863139.42")
EXPECTED_NET_ITEM_REVENUE = Decimal("44373408.18")

MONEY_TOLERANCE = Decimal("0.01")


def fetch_scalar(db_engine: Engine, query: str):
    """Execute a SQL query and return its single result."""
    with db_engine.connect() as connection:
        return connection.execute(text(query)).scalar_one()


def as_decimal(value) -> Decimal:
    """Convert a database numeric result to Decimal safely."""
    return Decimal(str(value))


def test_gross_sales(db_engine: Engine):
    """Gross sales must match the governed expected value."""
    actual = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(gross_sales), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    assert abs(actual - EXPECTED_GROSS_SALES) <= MONEY_TOLERANCE, (
        f"Gross sales mismatch: expected {EXPECTED_GROSS_SALES}, "
        f"found {actual}"
    )


def test_total_discounts(db_engine: Engine):
    """Discounts must match the governed expected value."""
    actual = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(total_discount), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    assert abs(actual - EXPECTED_TOTAL_DISCOUNTS) <= MONEY_TOLERANCE, (
        f"Total discounts mismatch: expected {EXPECTED_TOTAL_DISCOUNTS}, "
        f"found {actual}"
    )


def test_net_item_revenue(db_engine: Engine):
    """Net item revenue must match the governed expected value."""
    actual = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(net_item_revenue), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    assert abs(actual - EXPECTED_NET_ITEM_REVENUE) <= MONEY_TOLERANCE, (
        f"Net item revenue mismatch: expected "
        f"{EXPECTED_NET_ITEM_REVENUE}, found {actual}"
    )


def test_revenue_formula_at_line_level(db_engine: Engine):
    """Net item revenue must equal gross sales minus discounts."""
    result = fetch_scalar(
        db_engine,
        """
        SELECT COALESCE(
            SUM(
                net_item_revenue
                - (gross_sales - total_discount)
            ),
            0
        )
        FROM semantic.vw_order_line_metrics
        WHERE is_sales_eligible
        """,
    )

    difference = as_decimal(result)

    assert abs(difference) <= MONEY_TOLERANCE, (
        f"Revenue formula reconciliation difference: {difference}"
    )


def test_revenue_reconciles_with_customer_summary(db_engine: Engine):
    """Eligible revenue must reconcile with customer summaries."""
    line_revenue = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(net_item_revenue), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    customer_revenue = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(net_item_revenue), 0)
            FROM semantic.vw_customer_summary
            """,
        )
    )

    difference = line_revenue - customer_revenue

    assert abs(difference) <= MONEY_TOLERANCE, (
        f"Revenue differs between order-line and customer views: "
        f"{difference}"
    )


def test_revenue_reconciles_with_product_performance(db_engine: Engine):
    """Eligible revenue must reconcile with product summaries."""
    line_revenue = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(net_item_revenue), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    product_revenue = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(net_item_revenue), 0)
            FROM semantic.vw_product_performance
            """,
        )
    )

    difference = line_revenue - product_revenue

    assert abs(difference) <= MONEY_TOLERANCE, (
        f"Revenue differs between order-line and product views: "
        f"{difference}"
    )


def test_cancelled_orders_are_excluded_from_revenue(db_engine: Engine):
    """Cancelled order lines must not be marked as sales-eligible."""
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


def test_shipping_fees_are_not_included_in_item_revenue(db_engine: Engine):
    """Item revenue must not silently include order shipping fees."""
    item_revenue = as_decimal(
        fetch_scalar(
            db_engine,
            """
            SELECT COALESCE(SUM(net_item_revenue), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
        )
    )

    expected_item_revenue = (
        EXPECTED_GROSS_SALES - EXPECTED_TOTAL_DISCOUNTS
    )

    assert abs(item_revenue - expected_item_revenue) <= MONEY_TOLERANCE, (
        "Net item revenue does not match gross sales minus discounts. "
        "Check whether shipping fees were incorrectly included."
    )


@pytest.mark.parametrize(
    ("metric_name", "query", "expected"),
    [
        (
            "gross_sales",
            """
            SELECT COALESCE(SUM(gross_sales), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
            EXPECTED_GROSS_SALES,
        ),
        (
            "total_discounts",
            """
            SELECT COALESCE(SUM(total_discount), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
            EXPECTED_TOTAL_DISCOUNTS,
        ),
        (
            "net_item_revenue",
            """
            SELECT COALESCE(SUM(net_item_revenue), 0)
            FROM semantic.vw_order_line_metrics
            WHERE is_sales_eligible
            """,
            EXPECTED_NET_ITEM_REVENUE,
        ),
    ],
)
def test_revenue_metrics_are_non_negative(
    db_engine: Engine,
    metric_name: str,
    query: str,
    expected: Decimal,
):
    """Check non-negative governed revenue totals."""
    actual = as_decimal(fetch_scalar(db_engine, query))

    assert actual >= 0, (
        f"{metric_name} must not be negative; found {actual}"
    )

    assert abs(actual - expected) <= MONEY_TOLERANCE, (
        f"{metric_name} differs from its governed expected value: "
        f"expected {expected}, found {actual}"
    )
