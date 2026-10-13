
-- File: sql/00_setup/03_verify_environment.sql
-- Purpose: Verify the database connection and required schemas.

-- 1. Confirm the active database and PostgreSQL user.
SELECT
    current_database() AS database_name,
    current_user AS connected_user,
    version() AS postgresql_version;

-- 2. Confirm that the three required schemas exist.
SELECT
    schema_name
FROM information_schema.schemata
WHERE schema_name IN ('raw', 'semantic', 'metrics')
ORDER BY schema_name;

-- 3. Check that the raw schema does not contain tables yet.
-- This is expected before we create and load the source tables.
SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'raw'
ORDER BY table_name;
