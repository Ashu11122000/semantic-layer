
-- File: sql/00_setup/02_create_schemas.sql
-- Purpose: Create schemas for raw data, semantic views, and metrics.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS semantic;
CREATE SCHEMA IF NOT EXISTS metrics;

COMMENT ON SCHEMA raw IS
'Contains source data loaded from the original CSV files.';

COMMENT ON SCHEMA semantic IS
'Contains business-friendly SQL views for analytics and BI.';

COMMENT ON SCHEMA metrics IS
'Contains governed business metric definitions and related objects.';
