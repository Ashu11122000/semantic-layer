-- File: 02_revenue_validation.sql
-- Purpose: Reconcile revenue metrics across the semantic layer

-- 1. Compare eligible order-line totals with the governed
-- revenue metrics.
WITH order_line_totals AS (
    SELECT
        ROUND(SUM(gross_sales), 2) AS gross_sales,
        ROUND(SUM(total_discount), 2) AS total_discounts,
        ROUND(SUM(net_item_revenue), 2) AS net_item_revenue
    FROM semantic.vw_order_line_metrics
    WHERE is_sales_eligible
),
governed_metrics AS (
    SELECT
        ROUND(gross_sales, 2) AS gross_sales,
        ROUND(total_discounts, 2) AS total_discounts,
        ROUND(net_item_revenue, 2) AS net_item_revenue
    FROM (
        SELECT
            SUM(gross_sales) AS gross_sales,
            SUM(total_discounts) AS total_discounts,
            SUM(net_item_revenue) AS net_item_revenue
        FROM semantic.vw_sales_metrics
    ) AS totals
)
SELECT
    'gross_sales' AS metric,
    o.gross_sales AS order_line_value,
    g.gross_sales AS governed_value,
    ROUND(o.gross_sales - g.gross_sales, 2) AS difference,
    o.gross_sales = g.gross_sales AS passed
FROM order_line_totals o
CROSS JOIN governed_metrics g

UNION ALL

SELECT
    'total_discounts',
    o.total_discounts,
    g.total_discounts,
    ROUND(o.total_discounts - g.total_discounts, 2),
    o.total_discounts = g.total_discounts
FROM order_line_totals o
CROSS JOIN governed_metrics g

UNION ALL

SELECT
    'net_item_revenue',
    o.net_item_revenue,
    g.net_item_revenue,
    ROUND(o.net_item_revenue - g.net_item_revenue, 2),
    o.net_item_revenue = g.net_item_revenue
FROM order_line_totals o
CROSS JOIN governed_metrics g
ORDER BY metric;

-- 2. Independently verify the revenue formula:
-- net item revenue = gross sales - discounts.
SELECT
    ROUND(SUM(gross_sales), 2) AS gross_sales,
    ROUND(SUM(total_discount), 2) AS total_discounts,
    ROUND(SUM(net_item_revenue), 2) AS net_item_revenue,
    ROUND(
        SUM(gross_sales) - SUM(total_discount) - SUM(net_item_revenue),
        2
    ) AS formula_difference
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible;
