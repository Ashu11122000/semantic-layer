-- File: 03_profit_validation.sql
-- Purpose: Validate estimated cost, profit, and margin

-- 1. Reconcile order-line totals with product-level totals.
WITH order_line_totals AS (
    SELECT
        ROUND(SUM(estimated_product_cost), 2) AS estimated_product_cost,
        ROUND(SUM(estimated_gross_profit), 2) AS estimated_gross_profit
    FROM semantic.vw_order_line_metrics
    WHERE is_sales_eligible
),
product_totals AS (
    SELECT
        ROUND(SUM(estimated_product_cost), 2) AS estimated_product_cost,
        ROUND(SUM(estimated_gross_profit), 2) AS estimated_gross_profit
    FROM semantic.vw_product_performance
)
SELECT
    'estimated_product_cost' AS metric,
    o.estimated_product_cost AS order_line_value,
    p.estimated_product_cost AS product_value,
    ROUND(
        o.estimated_product_cost - p.estimated_product_cost, 2
    ) AS difference,
    o.estimated_product_cost = p.estimated_product_cost AS passed
FROM order_line_totals o
CROSS JOIN product_totals p

UNION ALL

SELECT
    'estimated_gross_profit',
    o.estimated_gross_profit,
    p.estimated_gross_profit,
    ROUND(
        o.estimated_gross_profit - p.estimated_gross_profit, 2
    ),
    o.estimated_gross_profit = p.estimated_gross_profit
FROM order_line_totals o
CROSS JOIN product_totals p
ORDER BY metric;

-- 2. Independently validate the profit formula.
SELECT
    ROUND(SUM(net_item_revenue), 2) AS net_item_revenue,
    ROUND(SUM(estimated_product_cost), 2) AS estimated_product_cost,
    ROUND(SUM(estimated_gross_profit), 2) AS estimated_gross_profit,
    ROUND(
        SUM(net_item_revenue)
        - SUM(estimated_product_cost)
        - SUM(estimated_gross_profit),
        2
    ) AS formula_difference,
    ROUND(
        100.0 * SUM(estimated_gross_profit)
        / NULLIF(SUM(net_item_revenue), 0),
        2
    ) AS estimated_gross_margin_pct
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible;
