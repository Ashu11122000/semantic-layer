"""Automated data-quality tests for the semantic layer project."""

import os
from decimal import Decimal
from pathlib import Path
from typing import Generator

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# Load environment variables from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def get_database_url() -> str:
    """Return the SQLAlchemy-compatible database URL."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        pytest.fail(
            "DATABASE_URL is missing. Check the .env file in the project root."
        )

    return database_url


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """Create one database engine for the test session."""
    engine = create_engine(get_database_url(), pool_pre_ping=True)

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        engine.dispose()
        raise

    yield engine
    engine.dispose()


def scalar(db_engine: Engine, query: str):
    """Execute a query that returns one value."""
    with db_engine.connect() as connection:
        return connection.execute(text(query)).scalar_one()


# ---------------------------------------------------------
# 1. Expected source-table row counts
# ---------------------------------------------------------

EXPECTED_ROW_COUNTS = {
    "raw.customers": 350,
    "raw.products": 26,
    "raw.orders": 1200,
    "raw.order_items": 2908,
    "raw.payments": 1200,
    "raw.returns": 42,
    "raw.reviews": 650,
}


@pytest.mark.parametrize(
    ("table_name", "expected_count"),
    EXPECTED_ROW_COUNTS.items(),
)
def test_source_table_row_counts(
    db_engine: Engine,
    table_name: str,
    expected_count: int,
):
    """Verify that imported source tables contain the expected rows."""
    actual_count = scalar(
        db_engine,
        f"SELECT COUNT(*) FROM {table_name}",
    )

    assert actual_count == expected_count, (
        f"{table_name}: expected {expected_count} rows, "
        f"found {actual_count}"
    )


# ---------------------------------------------------------
# 2. Duplicate primary/business identifiers
# ---------------------------------------------------------

DUPLICATE_ID_QUERIES = {
    "customers": """
        SELECT COUNT(*)
        FROM (
            SELECT customer_id
            FROM raw.customers
            GROUP BY customer_id
            HAVING customer_id IS NULL OR COUNT(*) > 1
        ) duplicates
    """,
    "products": """
        SELECT COUNT(*)
        FROM (
            SELECT product_id
            FROM raw.products
            GROUP BY product_id
            HAVING product_id IS NULL OR COUNT(*) > 1
        ) duplicates
    """,
    "orders": """
        SELECT COUNT(*)
        FROM (
            SELECT order_id
            FROM raw.orders
            GROUP BY order_id
            HAVING order_id IS NULL OR COUNT(*) > 1
        ) duplicates
    """,
    "order_items": """
        SELECT COUNT(*)
        FROM (
            SELECT order_item_id
            FROM raw.order_items
            GROUP BY order_item_id
            HAVING order_item_id IS NULL OR COUNT(*) > 1
        ) duplicates
    """,
    "payments": """
        SELECT COUNT(*)
        FROM (
            SELECT payment_id
            FROM raw.payments
            GROUP BY payment_id
            HAVING payment_id IS NULL OR COUNT(*) > 1
        ) duplicates
    """,
    "returns": """
        SELECT COUNT(*)
        FROM (
            SELECT return_id
            FROM raw.returns
            GROUP BY return_id
            HAVING return_id IS NULL OR COUNT(*) > 1
        ) duplicates
    """,
    "reviews": """
        SELECT COUNT(*)
        FROM (
            SELECT review_id
            FROM raw.reviews
            GROUP BY review_id
            HAVING review_id IS NULL OR COUNT(*) > 1
        ) duplicates
    """,
}


@pytest.mark.parametrize(
    ("table_name", "query"),
    DUPLICATE_ID_QUERIES.items(),
)
def test_no_duplicate_or_null_identifiers(
    db_engine: Engine,
    table_name: str,
    query: str,
):
    """Verify that each source table has unique, non-null identifiers."""
    issue_count = scalar(db_engine, query)

    assert issue_count == 0, (
        f"{table_name} contains {issue_count} duplicate/null identifier groups"
    )


# ---------------------------------------------------------
# 3. Missing required identifiers
# ---------------------------------------------------------

REQUIRED_IDENTIFIER_QUERIES = {
    "customers.customer_id": """
        SELECT COUNT(*) FROM raw.customers
        WHERE customer_id IS NULL
    """,
    "products.product_id": """
        SELECT COUNT(*) FROM raw.products
        WHERE product_id IS NULL
    """,
    "orders.order_id": """
        SELECT COUNT(*) FROM raw.orders
        WHERE order_id IS NULL
    """,
    "orders.customer_id": """
        SELECT COUNT(*) FROM raw.orders
        WHERE customer_id IS NULL
    """,
    "order_items.order_item_id": """
        SELECT COUNT(*) FROM raw.order_items
        WHERE order_item_id IS NULL
    """,
    "order_items.order_id": """
        SELECT COUNT(*) FROM raw.order_items
        WHERE order_id IS NULL
    """,
    "order_items.product_id": """
        SELECT COUNT(*) FROM raw.order_items
        WHERE product_id IS NULL
    """,
    "payments.payment_id": """
        SELECT COUNT(*) FROM raw.payments
        WHERE payment_id IS NULL
    """,
    "payments.order_id": """
        SELECT COUNT(*) FROM raw.payments
        WHERE order_id IS NULL
    """,
    "returns.return_id": """
        SELECT COUNT(*) FROM raw.returns
        WHERE return_id IS NULL
    """,
    "returns.order_id": """
        SELECT COUNT(*) FROM raw.returns
        WHERE order_id IS NULL
    """,
    "reviews.review_id": """
        SELECT COUNT(*) FROM raw.reviews
        WHERE review_id IS NULL
    """,
    "reviews.order_id": """
        SELECT COUNT(*) FROM raw.reviews
        WHERE order_id IS NULL
    """,
}


@pytest.mark.parametrize(
    ("column_name", "query"),
    REQUIRED_IDENTIFIER_QUERIES.items(),
)
def test_required_identifiers_are_not_null(
    db_engine: Engine,
    column_name: str,
    query: str,
):
    """Verify that required identifiers are populated."""
    missing_count = scalar(db_engine, query)

    assert missing_count == 0, (
        f"{column_name} contains {missing_count} NULL values"
    )


# ---------------------------------------------------------
# 4. Referential integrity
# ---------------------------------------------------------

RELATIONSHIP_QUERIES = {
    "orders_without_customers": """
        SELECT COUNT(*)
        FROM raw.orders o
        LEFT JOIN raw.customers c
            ON c.customer_id = o.customer_id
        WHERE c.customer_id IS NULL
    """,
    "order_items_without_orders": """
        SELECT COUNT(*)
        FROM raw.order_items oi
        LEFT JOIN raw.orders o
            ON o.order_id = oi.order_id
        WHERE o.order_id IS NULL
    """,
    "order_items_without_products": """
        SELECT COUNT(*)
        FROM raw.order_items oi
        LEFT JOIN raw.products p
            ON p.product_id = oi.product_id
        WHERE p.product_id IS NULL
    """,
    "payments_without_orders": """
        SELECT COUNT(*)
        FROM raw.payments p
        LEFT JOIN raw.orders o
            ON o.order_id = p.order_id
        WHERE o.order_id IS NULL
    """,
    "returns_without_orders": """
        SELECT COUNT(*)
        FROM raw.returns r
        LEFT JOIN raw.orders o
            ON o.order_id = r.order_id
        WHERE o.order_id IS NULL
    """,
    "reviews_without_orders": """
        SELECT COUNT(*)
        FROM raw.reviews r
        LEFT JOIN raw.orders o
            ON o.order_id = r.order_id
        WHERE o.order_id IS NULL
    """,
}


@pytest.mark.parametrize(
    ("relationship", "query"),
    RELATIONSHIP_QUERIES.items(),
)
def test_referential_integrity(
    db_engine: Engine,
    relationship: str,
    query: str,
):
    """Verify that foreign-key references point to existing records."""
    orphan_count = scalar(db_engine, query)

    assert orphan_count == 0, (
        f"{relationship}: found {orphan_count} orphan records"
    )


# ---------------------------------------------------------
# 5. Invalid business values
# ---------------------------------------------------------

INVALID_VALUE_QUERIES = {
    "non_positive_order_item_quantity": """
        SELECT COUNT(*) FROM raw.order_items
        WHERE quantity IS NULL OR quantity <= 0
    """,
    "negative_order_item_price": """
        SELECT COUNT(*) FROM raw.order_items
        WHERE unit_price_at_sale < 0
    """,
    "negative_order_item_cost": """
        SELECT COUNT(*) FROM raw.order_items
        WHERE unit_cost_at_sale < 0
    """,
    "negative_discount": """
        SELECT COUNT(*) FROM raw.order_items
        WHERE discount_amount < 0
    """,
    "discount_exceeds_gross_line_value": """
        SELECT COUNT(*)
        FROM raw.order_items
        WHERE discount_amount > quantity * unit_price_at_sale
    """,
    "invalid_review_score": """
        SELECT COUNT(*) FROM raw.reviews
        WHERE review_score IS NULL
           OR review_score < 1
           OR review_score > 5
    """,
    "negative_shipping_fee": """
        SELECT COUNT(*) FROM raw.orders
        WHERE shipping_fee < 0
    """,
}


@pytest.mark.parametrize(
    ("rule_name", "query"),
    INVALID_VALUE_QUERIES.items(),
)
def test_business_values_are_valid(
    db_engine: Engine,
    rule_name: str,
    query: str,
):
    """Check numeric and rating values against basic business rules."""
    invalid_count = scalar(db_engine, query)

    assert invalid_count == 0, (
        f"{rule_name}: found {invalid_count} invalid records"
    )


# ---------------------------------------------------------
# 6. Semantic-layer business rules
# ---------------------------------------------------------

def test_cancelled_order_lines_are_excluded_from_sales(db_engine: Engine):
    """Cancelled order lines must not be marked as sales-eligible."""
    count = scalar(
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


def test_order_line_revenue_formula(db_engine: Engine):
    """Net item revenue must equal gross sales minus discounts."""
    difference = scalar(
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
        """,
    )

    assert abs(Decimal(str(difference))) <= Decimal("0.01"), (
        f"Revenue formula reconciliation difference: {difference}"
    )


def test_order_line_profit_formula(db_engine: Engine):
    """Estimated gross profit must equal revenue minus product cost."""
    difference = scalar(
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
        """,
    )

    assert abs(Decimal(str(difference))) <= Decimal("0.01"), (
        f"Profit formula reconciliation difference: {difference}"
    )
