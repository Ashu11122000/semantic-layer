-- ============================================================
-- File: 04_vw_product_performance.sql
-- Purpose: Summarize eligible sales by product.
-- Grain: One row per product.
-- ============================================================

CREATE OR REPLACE VIEW semantic.vw_product_performance AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.active_flag,

    COUNT(DISTINCT olm.order_id) AS order_count,

    COALESCE(SUM(olm.quantity), 0) AS units_sold,

    ROUND(
        COALESCE(SUM(olm.gross_sales), 0),
        2
    ) AS gross_sales,

    ROUND(
        COALESCE(SUM(olm.total_discount), 0),
        2
    ) AS total_discounts,

    ROUND(
        COALESCE(SUM(olm.net_item_revenue), 0),
        2
    ) AS net_item_revenue,

    ROUND(
        COALESCE(SUM(olm.estimated_product_cost), 0),
        2
    ) AS estimated_product_cost,

    ROUND(
        COALESCE(SUM(olm.estimated_gross_profit), 0),
        2
    ) AS estimated_gross_profit

FROM raw.products AS p
LEFT JOIN semantic.vw_order_line_metrics AS olm
    ON olm.product_id = p.product_id
   AND olm.is_sales_eligible
GROUP BY
    p.product_id,
    p.product_name,
    p.category,
    p.active_flag;

COMMENT ON VIEW semantic.vw_product_performance IS
    'Product-level sales and estimated profit metrics for eligible '
    'orders. Products without eligible sales remain in the view. '
    'Historical transaction prices and costs are used.';
