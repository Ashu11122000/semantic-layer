-- File: 01_vw_order_line_metrics.sql
-- Purpose: Calculate sales metrics at the order-line grain.
-- Grain: One row per order_item_id.

CREATE OR REPLACE VIEW semantic.vw_order_line_metrics AS
SELECT
    oi.order_item_id,
    oi.order_id,
    o.customer_id,
    o.order_date,
    o.order_status,
    oi.product_id,
    p.product_name,
    p.category,

    oi.quantity,
    oi.unit_price_at_sale,
    oi.unit_cost_at_sale,
    oi.discount_amount,

    -- Gross sales before discounts.
    oi.quantity * oi.unit_price_at_sale
        AS gross_sales,

    -- Total discount already recorded for this order line.
    oi.discount_amount
        AS total_discount,

    -- Net item revenue, excluding shipping.
    (oi.quantity * oi.unit_price_at_sale)
        - oi.discount_amount
        AS net_item_revenue,

    -- Estimated product cost using historical unit cost.
    oi.quantity * oi.unit_cost_at_sale
        AS estimated_product_cost,

    -- Estimated gross profit after discounts and product cost.
    (oi.quantity * oi.unit_price_at_sale)
        - oi.discount_amount
        - (oi.quantity * oi.unit_cost_at_sale)
        AS estimated_gross_profit,

    -- Cancelled orders are not eligible for sales reporting.
    (LOWER(TRIM(o.order_status)) <> 'cancelled')
        AS is_sales_eligible

FROM raw.order_items AS oi
INNER JOIN raw.orders AS o
    ON o.order_id = oi.order_id
INNER JOIN raw.products AS p
    ON p.product_id = oi.product_id;

COMMENT ON VIEW semantic.vw_order_line_metrics IS
    'Order-line sales metrics using historical transaction prices '
    'and costs. Shipping is excluded from item revenue. '
    'The is_sales_eligible flag identifies non-cancelled orders.';
