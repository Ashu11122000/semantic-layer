
-- File: sql/01_raw/04_validate_relationships.sql
-- Purpose: Identify missing and unmatched relationships
-- before creating semantic views.

-- 1. Orders whose customer does not exist
SELECT
    'orders -> customers' AS relationship,
    COUNT(*) AS unmatched_rows
FROM raw.orders o
LEFT JOIN raw.customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- 2. Order items whose order does not exist
SELECT
    'order_items -> orders' AS relationship,
    COUNT(*) AS unmatched_rows
FROM raw.order_items oi
LEFT JOIN raw.orders o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 3. Order items whose product does not exist
SELECT
    'order_items -> products' AS relationship,
    COUNT(*) AS unmatched_rows
FROM raw.order_items oi
LEFT JOIN raw.products p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;

-- 4. Payments whose order does not exist
SELECT
    'payments -> orders' AS relationship,
    COUNT(*) AS unmatched_rows
FROM raw.payments p
LEFT JOIN raw.orders o
    ON p.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 5. Returns whose order does not exist
SELECT
    'returns -> orders' AS relationship,
    COUNT(*) AS unmatched_rows
FROM raw.returns r
LEFT JOIN raw.orders o
    ON r.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 6. Reviews whose order does not exist
SELECT
    'reviews -> orders' AS relationship,
    COUNT(*) AS unmatched_rows
FROM raw.reviews rv
LEFT JOIN raw.orders o
    ON rv.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 7. Null relationship keys
SELECT
    'orders.customer_id' AS relationship,
    COUNT(*) AS null_keys
FROM raw.orders
WHERE customer_id IS NULL

UNION ALL

SELECT
    'order_items.order_id',
    COUNT(*)
FROM raw.order_items
WHERE order_id IS NULL

UNION ALL

SELECT
    'order_items.product_id',
    COUNT(*)
FROM raw.order_items
WHERE product_id IS NULL

UNION ALL

SELECT
    'payments.order_id',
    COUNT(*)
FROM raw.payments
WHERE order_id IS NULL

UNION ALL

SELECT
    'returns.order_id',
    COUNT(*)
FROM raw.returns
WHERE order_id IS NULL

UNION ALL

SELECT
    'reviews.order_id',
    COUNT(*)
FROM raw.reviews
WHERE order_id IS NULL;
