-- File: 04_grants_and_permissions.sql
-- Purpose: Apply least-privilege access grants
-- Database: semantic_layer_db

-- 1. Remove public access to security configuration.
REVOKE ALL ON SCHEMA security FROM PUBLIC;
REVOKE ALL ON TABLE security.user_region_access FROM PUBLIC;

-- 2. Allow roles to resolve approved semantic objects.
GRANT USAGE ON SCHEMA semantic
TO semantic_admin, semantic_analyst, semantic_regional_manager;

GRANT USAGE ON SCHEMA security
TO semantic_admin, semantic_regional_manager;

-- 3. Administrator: access to semantic reporting objects.
GRANT SELECT ON
    semantic.vw_order_line_metrics,
    semantic.vw_sales_metrics,
    semantic.vw_customer_summary,
    semantic.vw_product_performance,
    semantic.vw_return_analysis,
    semantic.secured_customer_metrics,
    semantic.vw_customer_metrics_secure
TO semantic_admin;

-- Allow administrators to maintain regional access assignments.
GRANT SELECT, INSERT, UPDATE, DELETE
ON security.user_region_access
TO semantic_admin;

-- 4. Analyst: approved reporting views across all regions.
-- The customer-name/city summary is deliberately excluded.
GRANT SELECT ON
    semantic.vw_order_line_metrics,
    semantic.vw_sales_metrics,
    semantic.vw_product_performance,
    semantic.vw_return_analysis,
    semantic.vw_customer_metrics_secure
TO semantic_analyst;

-- 5. Regional manager: only the RLS-protected customer metrics view.
GRANT SELECT ON semantic.vw_customer_metrics_secure
TO semantic_regional_manager;

-- 6. Ensure the regional manager can execute the authorization check.
GRANT EXECUTE
ON FUNCTION security.is_region_authorized(TEXT)
TO semantic_regional_manager;

-- 7. Record the purpose of the access model.
COMMENT ON ROLE semantic_admin IS
    'Administrative group role for semantic reporting and regional access assignments.';

COMMENT ON ROLE semantic_analyst IS
    'Can query approved semantic reporting views across all regions.';

COMMENT ON ROLE semantic_regional_manager IS
    'Can query approved customer metrics restricted by region-level RLS.';
