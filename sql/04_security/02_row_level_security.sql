
-- File: 02_row_level_security.sql
-- Purpose: Configure region-based row-level security
-- Database: semantic_layer_db

-- 1. Create a dedicated schema for security configuration.
CREATE SCHEMA IF NOT EXISTS security;

-- 2. Store the regions each authenticated database login may access.
CREATE TABLE IF NOT EXISTS security.user_region_access (
    login_name TEXT NOT NULL,
    region TEXT NOT NULL,
    PRIMARY KEY (login_name, region)
);

COMMENT ON TABLE security.user_region_access IS
    'Maps authenticated PostgreSQL login names to the regions they may access.';

-- 3. Create a reporting table protected by row-level security.
-- This table contains customer metrics but excludes customer names
-- and city details, which can be controlled separately later.
CREATE TABLE IF NOT EXISTS semantic.secured_customer_metrics (
    customer_id TEXT PRIMARY KEY,
    segment TEXT,
    region TEXT,
    order_count BIGINT NOT NULL,
    net_item_revenue NUMERIC(14, 2) NOT NULL,
    estimated_gross_profit NUMERIC(14, 2) NOT NULL
);

-- 4. Populate or refresh the reporting table from the semantic view.
INSERT INTO semantic.secured_customer_metrics (
    customer_id,
    segment,
    region,
    order_count,
    net_item_revenue,
    estimated_gross_profit
)
SELECT
    customer_id,
    segment,
    region,
    order_count,
    net_item_revenue,
    estimated_gross_profit
FROM semantic.vw_customer_summary
ON CONFLICT (customer_id)
DO UPDATE SET
    segment = EXCLUDED.segment,
    region = EXCLUDED.region,
    order_count = EXCLUDED.order_count,
    net_item_revenue = EXCLUDED.net_item_revenue,
    estimated_gross_profit = EXCLUDED.estimated_gross_profit;

COMMENT ON TABLE semantic.secured_customer_metrics IS
    'Customer metrics reporting table with region-based row-level security.';

-- 5. Create a protected helper function.
-- SECURITY DEFINER allows the function to check the mapping table
-- without granting reporting users direct access to that table.
CREATE OR REPLACE FUNCTION security.is_region_authorized(
    requested_region TEXT
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
    SELECT EXISTS (
        SELECT 1
        FROM security.user_region_access AS ura
        WHERE ura.login_name = session_user::TEXT
          AND ura.region = requested_region
    );
$function$;

-- Only the database owner/admin account should manage this function.
REVOKE ALL ON FUNCTION security.is_region_authorized(TEXT) FROM PUBLIC;

-- 6. Enable and force RLS on the reporting table.
ALTER TABLE semantic.secured_customer_metrics
    ENABLE ROW LEVEL SECURITY;

ALTER TABLE semantic.secured_customer_metrics
    FORCE ROW LEVEL SECURITY;

-- 7. Remove existing policies before recreating them.
DROP POLICY IF EXISTS customer_metrics_admin_policy
    ON semantic.secured_customer_metrics;

DROP POLICY IF EXISTS customer_metrics_analyst_policy
    ON semantic.secured_customer_metrics;

DROP POLICY IF EXISTS customer_metrics_regional_policy
    ON semantic.secured_customer_metrics;

-- 8. Administrators can see all rows, provided their login
-- has membership in semantic_admin.
CREATE POLICY customer_metrics_admin_policy
ON semantic.secured_customer_metrics
FOR SELECT
USING (
    pg_has_role(session_user, 'semantic_admin', 'member')
);

-- 9. Analysts can see all rows in this reporting table,
-- provided their login has membership in semantic_analyst.
CREATE POLICY customer_metrics_analyst_policy
ON semantic.secured_customer_metrics
FOR SELECT
USING (
    pg_has_role(session_user, 'semantic_analyst', 'member')
);

-- 10. Regional managers can see only mapped regions.
CREATE POLICY customer_metrics_regional_policy
ON semantic.secured_customer_metrics
FOR SELECT
USING (
    pg_has_role(session_user, 'semantic_regional_manager', 'member')
    AND security.is_region_authorized(region)
);

-- 11. Permit the regional-manager role to call the helper function.
GRANT USAGE ON SCHEMA security TO semantic_regional_manager;

GRANT EXECUTE
ON FUNCTION security.is_region_authorized(TEXT)
TO semantic_regional_manager;
