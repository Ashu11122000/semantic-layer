-- File: 01_revenue_metrics.sql
-- Purpose: Define and validate governed revenue metrics.
-- Source: semantic.vw_order_line_metrics

-- Metric 1: Gross Sales
-- Definition: Item value before discounts, excluding shipping.
-- Formula: SUM(quantity * unit_price_at_sale)

SELECT
    'gross_sales' AS metric_name,
    'Eligible orders: item value before discounts; shipping excluded'
        AS metric_definition,
    ROUND(SUM(gross_sales), 2) AS metric_value
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible

UNION ALL

-- Metric 2: Total Discounts
-- Definition: Total line-level discounts for eligible orders.
-- Formula: SUM(discount_amount)

SELECT
    'total_discounts',
    'Eligible orders: sum of total discounts recorded per order line',
    ROUND(SUM(total_discount), 2)
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible

UNION ALL

-- Metric 3: Net Item Revenue
-- Definition: Gross sales minus discounts, excluding shipping.
-- Formula: Gross Sales - Total Discounts

SELECT
    'net_item_revenue',
    'Eligible orders: gross sales minus discounts; shipping excluded',
    ROUND(SUM(net_item_revenue), 2)
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible

ORDER BY metric_name;
