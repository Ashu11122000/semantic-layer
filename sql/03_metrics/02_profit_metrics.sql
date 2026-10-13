-- File: 02_profit_metrics.sql
-- Purpose: Define and validate governed product profit metrics.
-- Source: semantic.vw_order_line_metrics

-- Metric 1: Estimated Product Cost
-- Definition: Historical unit cost multiplied by quantity.
-- Formula: SUM(quantity * unit_cost_at_sale)

SELECT
    'estimated_product_cost' AS metric_name,
    'Eligible orders: quantity multiplied by historical unit cost'
        AS metric_definition,
    ROUND(SUM(estimated_product_cost), 2) AS metric_value
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible

UNION ALL

-- Metric 2: Estimated Gross Profit
-- Definition: Net item revenue minus estimated product cost.
-- Formula: Net Item Revenue - Estimated Product Cost

SELECT
    'estimated_gross_profit',
    'Eligible orders: net item revenue minus estimated product cost',
    ROUND(SUM(estimated_gross_profit), 2)
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible

UNION ALL

-- Metric 3: Estimated Gross Margin Percentage
-- Definition: Estimated gross profit as a percentage of net item revenue.
-- Formula: Estimated Gross Profit / Net Item Revenue * 100

SELECT
    'estimated_gross_margin_pct',
    'Eligible orders: estimated gross profit divided by net item revenue',
    ROUND(
        100.0 * SUM(estimated_gross_profit)
        / NULLIF(SUM(net_item_revenue), 0),
        2
    )
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible

ORDER BY metric_name;
