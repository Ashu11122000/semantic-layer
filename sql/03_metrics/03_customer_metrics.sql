-- File: 03_customer_metrics.sql
-- Purpose: Define and validate customer performance metrics.
-- Source: semantic.vw_customer_summary

-- Metric 1: Total Customers
-- Includes all customers, including those without eligible orders.

SELECT
    'total_customers' AS metric_name,
    'Count of distinct customers in the customer summary'
        AS metric_definition,
    COUNT(DISTINCT customer_id)::NUMERIC AS metric_value
FROM semantic.vw_customer_summary

UNION ALL

-- Metric 2: Customers with Eligible Orders

SELECT
    'customers_with_eligible_orders',
    'Count of customers with at least one eligible order',
    COUNT(*) FILTER (
        WHERE order_count > 0
    )::NUMERIC
FROM semantic.vw_customer_summary

UNION ALL

-- Metric 3: Average Order Value
-- Weighted correctly using total revenue divided by total orders.

SELECT
    'average_order_value',
    'Eligible net item revenue divided by eligible distinct orders',
    ROUND(
        SUM(net_item_revenue)
        / NULLIF(SUM(order_count), 0),
        2
    )
FROM semantic.vw_customer_summary

UNION ALL

-- Metric 4: Total Customer Net Item Revenue

SELECT
    'total_customer_net_item_revenue',
    'Sum of net item revenue across customer summaries',
    ROUND(SUM(net_item_revenue), 2)
FROM semantic.vw_customer_summary

ORDER BY metric_name;
