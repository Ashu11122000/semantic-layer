-- File: sql/01_raw/05_validate_dates.sql
-- Purpose: Identify missing or inconsistent dates in raw data.
-- Note: These checks report potential issues; they do not modify data.

-- 1. Customers with missing signup dates
SELECT
    'customers.signup_date missing' AS validation_check,
    COUNT(*) AS issue_count
FROM raw.customers
WHERE signup_date IS NULL;

-- 2. Orders with missing order dates
SELECT
    'orders.order_date missing' AS validation_check,
    COUNT(*) AS issue_count
FROM raw.orders
WHERE order_date IS NULL;

-- 3. Shipment dates before order dates
SELECT
    'ship_date before order_date' AS validation_check,
    COUNT(*) AS issue_count
FROM raw.orders
WHERE ship_date IS NOT NULL
  AND order_date IS NOT NULL
  AND ship_date < order_date;

-- 4. Delivery dates before shipment dates
SELECT
    'delivery_date before ship_date' AS validation_check,
    COUNT(*) AS issue_count
FROM raw.orders
WHERE delivery_date IS NOT NULL
  AND ship_date IS NOT NULL
  AND delivery_date < ship_date;

-- 5. Delivery dates before order dates
SELECT
    'delivery_date before order_date' AS validation_check,
    COUNT(*) AS issue_count
FROM raw.orders
WHERE delivery_date IS NOT NULL
  AND order_date IS NOT NULL
  AND delivery_date < order_date;

-- 6. Payments dated before their associated orders
SELECT
    'payment_date before order_date' AS validation_check,
    COUNT(*) AS issue_count
FROM raw.payments p
JOIN raw.orders o
    ON o.order_id = p.order_id
WHERE p.payment_date IS NOT NULL
  AND o.order_date IS NOT NULL
  AND p.payment_date < o.order_date;

-- 7. Returns dated before their associated orders
SELECT
    'return_date before order_date' AS validation_check,
    COUNT(*) AS issue_count
FROM raw.returns r
JOIN raw.orders o
    ON o.order_id = r.order_id
WHERE r.return_date IS NOT NULL
  AND o.order_date IS NOT NULL
  AND r.return_date < o.order_date;

-- 8. Reviews dated before their associated orders
SELECT
    'review_date before order_date' AS validation_check,
    COUNT(*) AS issue_count
FROM raw.reviews rv
JOIN raw.orders o
    ON o.order_id = rv.order_id
WHERE rv.review_date IS NOT NULL
  AND o.order_date IS NOT NULL
  AND rv.review_date < o.order_date;
