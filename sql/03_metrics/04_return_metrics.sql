-- File: 04_return_metrics.sql
-- Purpose: Define and validate governed return metrics.
-- Sources: semantic.vw_return_analysis,
--          semantic.vw_order_line_metrics

-- Metric 1: Distinct Returned Orders
-- Definition: Eligible orders associated with a recorded return.

SELECT
    'distinct_returned_orders' AS metric_name,
    'Count of distinct returned orders within the eligible population'
        AS metric_definition,
    COUNT(DISTINCT r.order_id)::NUMERIC AS metric_value
FROM semantic.vw_return_analysis AS r
INNER JOIN (
    SELECT DISTINCT order_id
    FROM semantic.vw_order_line_metrics
    WHERE is_sales_eligible
) AS eligible
    ON eligible.order_id = r.order_id

UNION ALL

-- Metric 2: Eligible Orders
-- Definition: Distinct orders represented in the eligible sales layer.

SELECT
    'eligible_orders',
    'Count of distinct non-cancelled orders',
    COUNT(DISTINCT order_id)::NUMERIC
FROM semantic.vw_order_line_metrics
WHERE is_sales_eligible

UNION ALL

-- Metric 3: Order-Based Return Rate
-- Definition: Returned eligible orders divided by eligible orders.

SELECT
    'order_return_rate_pct',
    'Distinct returned eligible orders divided by eligible orders, percent',
    ROUND(
        100.0 * (
            SELECT COUNT(DISTINCT r.order_id)
            FROM semantic.vw_return_analysis AS r
            INNER JOIN (
                SELECT DISTINCT order_id
                FROM semantic.vw_order_line_metrics
                WHERE is_sales_eligible
            ) AS eligible
                ON eligible.order_id = r.order_id
        )
        / NULLIF(
            (
                SELECT COUNT(DISTINCT order_id)
                FROM semantic.vw_order_line_metrics
                WHERE is_sales_eligible
            ),
            0
        ),
        2
    )

ORDER BY metric_name;
