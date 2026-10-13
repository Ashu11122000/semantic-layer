-- ============================================================
-- File: 03_vw_customer_summary.sql
-- Purpose: Summarize eligible sales by customer.
-- Grain: One row per customer with eligible order activity.
-- ============================================================

CREATE OR REPLACE VIEW semantic.vw_customer_summary AS
WITH customer_order_metrics AS (
    SELECT
        customer_id,
        order_id,
        order_date,
        order_status,
        SUM(net_item_revenue) AS order_net_item_revenue,
        SUM(estimated_gross_profit) AS order_estimated_gross_profit,
        SUM(quantity) AS order_units_sold
    FROM semantic.vw_order_line_metrics
    WHERE is_sales_eligible
    GROUP BY
        customer_id,
        order_id,
        order_date,
        order_status
)
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    c.city,
    c.region,
    c.signup_date,

    COUNT(DISTINCT o.order_id) AS order_count,

    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS most_recent_order_date,

    COALESCE(SUM(o.order_units_sold), 0) AS units_sold,

    ROUND(
        COALESCE(SUM(o.order_net_item_revenue), 0),
        2
    ) AS net_item_revenue,

    ROUND(
        COALESCE(SUM(o.order_estimated_gross_profit), 0),
        2
    ) AS estimated_gross_profit,

    ROUND(
        COALESCE(SUM(o.order_net_item_revenue), 0)
        / NULLIF(COUNT(DISTINCT o.order_id), 0),
        2
    ) AS average_order_value

FROM raw.customers AS c
LEFT JOIN customer_order_metrics AS o
    ON o.customer_id = c.customer_id
GROUP BY
    c.customer_id,
    c.customer_name,
    c.segment,
    c.city,
    c.region,
    c.signup_date;

COMMENT ON VIEW semantic.vw_customer_summary IS
    'Customer-level summary of eligible orders, net item revenue, '
    'estimated gross profit, units sold, and average order value. '
    'Customers without eligible orders remain in the view with zero '
    'sales metrics.';
