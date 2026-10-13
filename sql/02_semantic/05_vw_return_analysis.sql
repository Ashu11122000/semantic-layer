-- ============================================================
-- File: 05_vw_return_analysis.sql
-- Purpose: Analyze returns by date and reason.
-- Grain: One row per return record.
-- ============================================================

CREATE OR REPLACE VIEW semantic.vw_return_analysis AS
SELECT
    r.return_id,
    r.order_id,
    r.return_date,
    r.return_reason,

    o.customer_id,
    o.order_date,
    o.order_status,

    c.segment,
    c.region,

    -- Each return record identifies one returned order in this dataset.
    1 AS return_count,

    -- The dataset does not contain refund amounts or returned quantities.
    'Refund amount unavailable'::TEXT AS refund_amount_status

FROM raw.returns AS r
INNER JOIN raw.orders AS o
    ON o.order_id = r.order_id
INNER JOIN raw.customers AS c
    ON c.customer_id = o.customer_id;

COMMENT ON VIEW semantic.vw_return_analysis IS
    'Return-level analysis with customer and order context. '
    'The source dataset does not provide refund amounts or returned '
    'quantities, so this view does not calculate monetary refunds.';
