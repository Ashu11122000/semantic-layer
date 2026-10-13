"""Shared pytest fixtures for the semantic layer project."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Create and share a database engine across all tests."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        pytest.fail(
            "DATABASE_URL is missing. Check the project's .env file."
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        engine.dispose()
        raise

    yield engine

    engine.dispose()