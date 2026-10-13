
-- File: 01_create_roles.sql
-- Purpose: Create least-privilege PostgreSQL group roles
-- Database: semantic_layer_db

-- Role 1: Administrative access
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'semantic_admin'
    ) THEN
        CREATE ROLE semantic_admin NOLOGIN;
    END IF;
END
$$;

-- Role 2: General business analyst access
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'semantic_analyst'
    ) THEN
        CREATE ROLE semantic_analyst NOLOGIN;
    END IF;
END
$$;

-- Role 3: Region-restricted manager access
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'semantic_regional_manager'
    ) THEN
        CREATE ROLE semantic_regional_manager NOLOGIN;
    END IF;
END
$$;

-- Ensure these roles do not have elevated database privileges.
ALTER ROLE semantic_admin
    NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

ALTER ROLE semantic_analyst
    NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

ALTER ROLE semantic_regional_manager
    NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

-- Document the intended purpose of each role.
COMMENT ON ROLE semantic_admin IS
    'Administrative group role for managing the semantic layer and its security configuration.';

COMMENT ON ROLE semantic_analyst IS
    'Business analyst group role for approved semantic reporting data.';

COMMENT ON ROLE semantic_regional_manager IS
    'Regional manager group role for reporting restricted to authorized regions.';
