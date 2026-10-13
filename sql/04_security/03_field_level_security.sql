-- File: 03_field_level_security.sql
-- Purpose: Restrict access to approved reporting columns
-- Database: semantic_layer_db

-- 1. Remove inherited public access to the reporting objects.
REVOKE ALL ON TABLE semantic.secured_customer_metrics FROM PUBLIC;

-- 2. Remove any previous table-level SELECT grants for reporting
-- roles. Column-level grants will be used instead.
REVOKE SELECT ON TABLE semantic.secured_customer_metrics
FROM semantic_analyst, semantic_regional_manager;

-- 3. Grant analysts access only to approved reporting columns.
GRANT SELECT (
    customer_id,
    segment,
    region,
    order_count,
    net_item_revenue,
    estimated_gross_profit
)
ON semantic.secured_customer_metrics
TO semantic_analyst;

-- 4. Grant regional managers the same approved columns.
-- Row-level restrictions remain enforced by the RLS policies.
GRANT SELECT (
    customer_id,
    segment,
    region,
    order_count,
    net_item_revenue,
    estimated_gross_profit
)
ON semantic.secured_customer_metrics
TO semantic_regional_manager;

-- 5. Create a secure reporting view that exposes only approved fields.
-- security_invoker makes access checks and underlying RLS apply
-- using the querying user's privileges.
CREATE OR REPLACE VIEW semantic.vw_customer_metrics_secure
WITH (security_invoker = true)
AS
SELECT
    customer_id,
    segment,
    region,
    order_count,
    net_item_revenue,
    estimated_gross_profit
FROM semantic.secured_customer_metrics;

COMMENT ON VIEW semantic.vw_customer_metrics_secure IS
    'Approved customer reporting fields. Underlying table privileges and row-level security apply to the querying user.';

-- 6. Remove default public access to the secure view.
REVOKE ALL ON TABLE semantic.vw_customer_metrics_secure FROM PUBLIC;

-- 7. Allow reporting roles to query the approved view.
GRANT SELECT ON semantic.vw_customer_metrics_secure
TO semantic_analyst, semantic_regional_manager;
