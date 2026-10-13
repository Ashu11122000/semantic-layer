
-- File: sql/00_setup/01_create_database.sql
-- Purpose: Create the project database if it does not already exist.
-- Execute this file using psql while connected to the "postgres" database.

SELECT 'CREATE DATABASE semantic_layer_db'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'semantic_layer_db'
)
\gexec
