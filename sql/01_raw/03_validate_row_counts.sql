
-- File: sql/01_raw/03_validate_row_counts.sql
-- Purpose: Verify row counts and check basic data quality.

-- 1. Row counts
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM raw.customers
UNION ALL
SELECT 'products', COUNT(*) FROM raw.products
UNION ALL
SELECT 'orders', COUNT(*) FROM raw.orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM raw.order_items
UNION ALL
SELECT 'payments', COUNT(*) FROM raw.payments
UNION ALL
SELECT 'returns', COUNT(*) FROM raw.returns
UNION ALL
SELECT 'reviews', COUNT(*) FROM raw.reviews
ORDER BY table_name;

-- 2. Missing primary identifiers
SELECT 'customers' AS table_name, COUNT(*) AS missing_ids
FROM raw.customers WHERE customer_id IS NULL
UNION ALL
SELECT 'products', COUNT(*) FROM raw.products WHERE product_id IS NULL
UNION ALL
SELECT 'orders', COUNT(*) FROM raw.orders WHERE order_id IS NULL
UNION ALL
SELECT 'order_items', COUNT(*) FROM raw.order_items WHERE order_item_id IS NULL
UNION ALL
SELECT 'payments', COUNT(*) FROM raw.payments WHERE payment_id IS NULL
UNION ALL
SELECT 'returns', COUNT(*) FROM raw.returns WHERE return_id IS NULL
UNION ALL
SELECT 'reviews', COUNT(*) FROM raw.reviews WHERE review_id IS NULL
ORDER BY table_name;

-- 3. Invalid quantities
SELECT COUNT(*) AS non_positive_quantities
FROM raw.order_items
WHERE quantity IS NULL OR quantity <= 0;

-- 4. Invalid review scores
SELECT COUNT(*) AS invalid_review_scores
FROM raw.reviews
WHERE review_score IS NULL OR review_score NOT BETWEEN 1 AND 5;

-- 5. Negative prices, costs, or discounts
SELECT
    COUNT(*) FILTER (
        WHERE unit_price_at_sale < 0
    ) AS negative_unit_prices,
    COUNT(*) FILTER (
        WHERE unit_cost_at_sale < 0
    ) AS negative_unit_costs,
    COUNT(*) FILTER (
        WHERE discount_amount < 0
    ) AS negative_discounts
FROM raw.order_items;
