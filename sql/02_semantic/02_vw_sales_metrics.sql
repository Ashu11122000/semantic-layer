-- File: 02_vw_sales_metrics.sql
-- Purpose: Aggregate governed sales metrics.
-- Grain: One row per reporting date and order status.

CREATE OR REPLACE VIEW semantic.vw_sales_metrics AS
SELECT
    order_date,
    order_status,

    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count,
    SUM(quantity) AS units_sold,

    ROUND(SUM(gross_sales), 2) AS gross_sales,
    ROUND(SUM(total_discount), 2) AS total_discounts,
    ROUND(SUM(net_item_revenue), 2) AS net_item_revenue,
    ROUND(SUM(estimated_product_cost), 2) AS estimated_product_cost,
    ROUND(SUM(estimated_gross_profit), 2) AS estimated_gross_profit

FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible
GROUP BY
    order_date,
    order_status;

COMMENT ON VIEW semantic.vw_sales_metrics IS
    'Daily sales summary grouped by order date and status. '
    'Cancelled orders are excluded. Revenue excludes shipping fees. '
    'Order and customer counts are distinct within each group.';
