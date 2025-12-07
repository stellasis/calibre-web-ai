# -*- coding: utf-8 -*-

"""
Shared database utilities for AI modules.
Provides a centralized database connection context manager to eliminate code duplication.
"""

import os
from contextlib import contextmanager
from typing import Optional, Generator, Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from .. import logger, ub

log = logger.create()


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """
    Context manager for database connections.
    Automatically handles connection creation, cleanup, and error handling.

    Usage:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT * FROM table"))

    Yields:
        SQLAlchemy Connection object

    Raises:
        RuntimeError: If database path is not configured or doesn't exist
    """
    db_path = getattr(ub, 'app_DB_path', None)
    if not db_path:
        raise RuntimeError("Database path not configured")

    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        raise RuntimeError(f"Database file does not exist: {db_path}")

    engine = create_engine(
        f'sqlite:///{db_path}',
        echo=False,
        connect_args={'check_same_thread': False}
    )

    conn = None
    try:
        conn = engine.connect()
        yield conn
    finally:
        if conn:
            conn.close()
        engine.dispose()


def get_db_path() -> Optional[str]:
    """
    Get the absolute path to the application database.

    Returns:
        Absolute path to database, or None if not configured
    """
    db_path = getattr(ub, 'app_DB_path', None)
    if db_path:
        return os.path.abspath(db_path)
    return None


def ensure_table_exists(conn: Connection, table_sql: str, index_sql: Optional[str] = None) -> None:
    """
    Ensure a table exists in the database.

    Args:
        conn: Database connection
        table_sql: CREATE TABLE IF NOT EXISTS SQL statement
        index_sql: Optional CREATE INDEX IF NOT EXISTS SQL statement
    """
    conn.execute(text(table_sql))
    if index_sql:
        conn.execute(text(index_sql))
    conn.commit()


def load_sqlite_vec(conn: Connection) -> bool:
    """
    Load the sqlite-vec extension for vector similarity search.

    Args:
        conn: SQLAlchemy connection

    Returns:
        True if extension loaded successfully, False otherwise
    """
    try:
        import sqlite_vec
        raw_conn = conn.connection.dbapi_connection
        raw_conn.enable_load_extension(True)
        sqlite_vec.load(raw_conn)
        raw_conn.enable_load_extension(False)
        log.debug("sqlite-vec extension loaded successfully")
        return True
    except ImportError:
        log.error("sqlite-vec package not installed. Install with: pip install sqlite-vec")
        return False
    except Exception as e:
        log.error("Failed to load sqlite-vec extension: %s", e)
        return False
