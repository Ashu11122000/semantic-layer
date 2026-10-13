-- File: 01_data_quality.sql
-- Purpose: Validate raw data quality and relationships
-- Database: semantic_layer_db

-- 1. Source table row counts
SELECT 'customers' AS table_name, COUNT(*) AS row_count
FROM raw.customers
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

-- 2. Duplicate primary-key checks
SELECT 'customers' AS table_name, COUNT(*) AS duplicate_key_groups
FROM (
    SELECT customer_id
    FROM raw.customers
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) AS d
UNION ALL
SELECT 'products', COUNT(*)
FROM (
    SELECT product_id
    FROM raw.products
    GROUP BY product_id
    HAVING COUNT(*) > 1
) AS d
UNION ALL
SELECT 'orders', COUNT(*)
FROM (
    SELECT order_id
    FROM raw.orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
) AS d
UNION ALL
SELECT 'order_items', COUNT(*)
FROM (
    SELECT order_item_id
    FROM raw.order_items
    GROUP BY order_item_id
    HAVING COUNT(*) > 1
) AS d
UNION ALL
SELECT 'payments', COUNT(*)
FROM (
    SELECT payment_id
    FROM raw.payments
    GROUP BY payment_id
    HAVING COUNT(*) > 1
) AS d
UNION ALL
SELECT 'returns', COUNT(*)
FROM (
    SELECT return_id
    FROM raw.returns
    GROUP BY return_id
    HAVING COUNT(*) > 1
) AS d
UNION ALL
SELECT 'reviews', COUNT(*)
FROM (
    SELECT review_id
    FROM raw.reviews
    GROUP BY review_id
    HAVING COUNT(*) > 1
) AS d
ORDER BY table_name;

-- 3. Missing required identifiers
SELECT 'customers.customer_id' AS check_name, COUNT(*) AS issue_count
FROM raw.customers
WHERE customer_id IS NULL OR BTRIM(customer_id) = ''
UNION ALL
SELECT 'products.product_id', COUNT(*)
FROM raw.products
WHERE product_id IS NULL OR BTRIM(product_id) = ''
UNION ALL
SELECT 'orders.order_id', COUNT(*)
FROM raw.orders
WHERE order_id IS NULL OR BTRIM(order_id) = ''
UNION ALL
SELECT 'order_items.order_item_id', COUNT(*)
FROM raw.order_items
WHERE order_item_id IS NULL OR BTRIM(order_item_id) = ''
UNION ALL
SELECT 'payments.payment_id', COUNT(*)
FROM raw.payments
WHERE payment_id IS NULL OR BTRIM(payment_id) = ''
UNION ALL
SELECT 'returns.return_id', COUNT(*)
FROM raw.returns
WHERE return_id IS NULL OR BTRIM(return_id) = ''
UNION ALL
SELECT 'reviews.review_id', COUNT(*)
FROM raw.reviews
WHERE review_id IS NULL OR BTRIM(review_id) = ''
ORDER BY check_name;

-- 4. Invalid quantities and negative transaction amounts
SELECT 'non_positive_quantity' AS check_name, COUNT(*) AS issue_count
FROM raw.order_items
WHERE quantity IS NULL OR quantity <= 0
UNION ALL
SELECT 'negative_unit_price', COUNT(*)
FROM raw.order_items
WHERE unit_price_at_sale < 0
UNION ALL
SELECT 'negative_unit_cost', COUNT(*)
FROM raw.order_items
WHERE unit_cost_at_sale < 0
UNION ALL
SELECT 'negative_discount', COUNT(*)
FROM raw.order_items
WHERE discount_amount < 0
UNION ALL
SELECT 'negative_shipping_fee', COUNT(*)
FROM raw.orders
WHERE shipping_fee < 0
ORDER BY check_name;

-- 5. Review score validation (expected scale: 1 through 5)
SELECT COUNT(*) AS invalid_review_scores
FROM raw.reviews
WHERE review_score IS NULL
   OR review_score NOT BETWEEN 1 AND 5;

-- 6. Referential-integrity checks
SELECT 'orders_missing_customer' AS check_name, COUNT(*) AS issue_count
FROM raw.orders o
LEFT JOIN raw.customers c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'order_items_missing_order', COUNT(*)
FROM raw.order_items oi
LEFT JOIN raw.orders o ON o.order_id = oi.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'order_items_missing_product', COUNT(*)
FROM raw.order_items oi
LEFT JOIN raw.products p ON p.product_id = oi.product_id
WHERE p.product_id IS NULL
UNION ALL
SELECT 'payments_missing_order', COUNT(*)
FROM raw.payments p
LEFT JOIN raw.orders o ON o.order_id = p.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'returns_missing_order', COUNT(*)
FROM raw.returns r
LEFT JOIN raw.orders o ON o.order_id = r.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'reviews_missing_order', COUNT(*)
FROM raw.reviews r
LEFT JOIN raw.orders o ON o.order_id = r.order_id
WHERE o.order_id IS NULL
ORDER BY check_name;
