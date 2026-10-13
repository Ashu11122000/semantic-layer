-- File: 04_semantic_view_validation.sql
-- Purpose: Validate semantic view structure and consistency

-- 1. Verify expected row counts.
SELECT 'vw_order_line_metrics' AS view_name, COUNT(*) AS row_count
FROM semantic.vw_order_line_metrics
UNION ALL
SELECT 'vw_sales_metrics', COUNT(*)
FROM semantic.vw_sales_metrics
UNION ALL
SELECT 'vw_customer_summary', COUNT(*)
FROM semantic.vw_customer_summary
UNION ALL
SELECT 'vw_product_performance', COUNT(*)
FROM semantic.vw_product_performance
UNION ALL
SELECT 'vw_return_analysis', COUNT(*)
FROM semantic.vw_return_analysis
ORDER BY view_name;

-- 2. Check unique customer and product identifiers.
SELECT
    'customer_summary_duplicate_ids' AS check_name,
    COUNT(*) AS issue_count
FROM (
    SELECT customer_id
    FROM semantic.vw_customer_summary
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) AS duplicates

UNION ALL

SELECT
    'product_performance_duplicate_ids',
    COUNT(*)
FROM (
    SELECT product_id
    FROM semantic.vw_product_performance
    GROUP BY product_id
    HAVING COUNT(*) > 1
) AS duplicates;

-- 3. Reconcile revenue and estimated profit across views.
SELECT
    'sales_vs_customer_revenue' AS check_name,
    ROUND(
        (SELECT SUM(net_item_revenue)
         FROM semantic.vw_sales_metrics)
        -
        (SELECT SUM(net_item_revenue)
         FROM semantic.vw_customer_summary),
        2
    ) AS difference

UNION ALL

SELECT
    'sales_vs_product_revenue',
    ROUND(
        (SELECT SUM(net_item_revenue)
         FROM semantic.vw_sales_metrics)
        -
        (SELECT SUM(net_item_revenue)
         FROM semantic.vw_product_performance),
        2
    )

UNION ALL

SELECT
    'sales_vs_customer_profit',
    ROUND(
        (SELECT SUM(estimated_gross_profit)
         FROM semantic.vw_sales_metrics)
        -
        (SELECT SUM(estimated_gross_profit)
         FROM semantic.vw_customer_summary),
        2
    )

UNION ALL

SELECT
    'sales_vs_product_profit',
    ROUND(
        (SELECT SUM(estimated_gross_profit)
         FROM semantic.vw_sales_metrics)
        -
        (SELECT SUM(estimated_gross_profit)
         FROM semantic.vw_product_performance),
        2
    );

-- 4. Confirm cancelled orders are excluded from eligible sales.
SELECT
    COUNT(*) FILTER (
        WHERE is_sales_eligible
          AND LOWER(TRIM(order_status)) = 'cancelled'
    ) AS eligible_cancelled_lines,
    COUNT(*) FILTER (
        WHERE NOT is_sales_eligible
          AND LOWER(TRIM(order_status)) = 'cancelled'
    ) AS excluded_cancelled_lines
FROM semantic.vw_order_line_metrics;
