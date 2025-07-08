"""
Database utilities for AIronman app.
Provides connection management, context managers, and common database operations.
"""

import logging
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional, Any, Dict, List
from utils.config import settings

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'dbname': settings.POSTGRES_DB,
    'user': settings.POSTGRES_USER,
    'password': settings.POSTGRES_PASSWORD,
    'host': settings.POSTGRES_HOST,
    'port': settings.POSTGRES_PORT,
}

# Global connection pool
CONN_POOL = None

def init_connection_pool(minconn=1, maxconn=10):
    global CONN_POOL
    if CONN_POOL is None:
        try:
            CONN_POOL = pool.ThreadedConnectionPool(
                minconn,
                maxconn,
                **DB_CONFIG
            )
            logger.info(f"Initialized DB connection pool: min={minconn}, max={maxconn}")
        except Exception as e:
            logger.error(f"Failed to initialize DB connection pool: {e}")
            raise

@contextmanager
def get_db_conn():
    """
    Context manager for getting a DB connection from the pool.
    Yields a connection and ensures it is returned to the pool.
    """
    global CONN_POOL
    if CONN_POOL is None:
        init_connection_pool()
    conn = None
    try:
        conn = CONN_POOL.getconn()
        yield conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    finally:
        if conn:
            CONN_POOL.putconn(conn)


def execute_query(query: str, params: Optional[tuple] = None, fetch_one: bool = False, fetch_all: bool = False):
    """
    Execute a database query with automatic connection management.
    Commits changes for non-SELECT queries.
    Args:
        query: SQL query to execute
        params: Query parameters
        fetch_one: Whether to fetch one result
        fetch_all: Whether to fetch all results
    Returns:
        Query result or None
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            # Commit if not a SELECT query
            if not query.strip().lower().startswith("select"):
                conn.commit()
            if fetch_one:
                return cur.fetchone()
            elif fetch_all:
                return cur.fetchall()
            return None


def check_record_exists(table: str, conditions: Dict[str, Any]) -> bool:
    """
    Check if a record exists in the database.
    
    Args:
        table: Table name
        conditions: Dictionary of column-value pairs for WHERE clause
                   Supports JSON field queries using -> operator (e.g., "json_file->>'activity_id'")
        
    Returns:
        True if record exists, False otherwise
    """
    where_parts = []
    params = []
    
    for key, value in conditions.items():
        if '->' in key:
            # JSON field query - don't parameterize the field name
            where_parts.append(f"{key}=%s")
        else:
            # Regular field query
            where_parts.append(f"{key}=%s")
        params.append(value)
    
    where_clause = " AND ".join(where_parts)
    query = f"SELECT 1 FROM {table} WHERE {where_clause}"
    result = execute_query(query, tuple(params), fetch_one=True)
    return result is not None


def get_athlete_uuid(athlete_id_str: str) -> str:
    """
    Get athlete UUID from database by ID or name.
    
    Args:
        athlete_id_str: Athlete ID or name
        
    Returns:
        Athlete UUID
        
    Raises:
        ValueError: If athlete not found
    """
    import uuid
    
    try:
        # Try to parse as UUID
        val = uuid.UUID(athlete_id_str)
        result = execute_query(
            "SELECT id FROM athlete WHERE id=%s", 
            (str(val),), 
            fetch_one=True
        )
    except ValueError:
        # Not a UUID, treat as name
        result = execute_query(
            "SELECT id FROM athlete WHERE name=%s", 
            (athlete_id_str,), 
            fetch_one=True
        )
    
    if result:
        return result[0]
    raise ValueError(f"No athlete found in DB for id or name: {athlete_id_str}")


def get_last_sync_timestamp(athlete_id: str, data_type: str) -> Optional[Any]:
    """
    Get the last sync timestamp for an athlete and data type.
    
    Args:
        athlete_id: Athlete UUID
        data_type: Type of data (sleep, hrv, rhr, workout)
        
    Returns:
        Last sync timestamp or None
    """
    result = execute_query(
        "SELECT last_synced_timestamp FROM sync WHERE athlete_id=%s AND data_type=%s",
        (athlete_id, data_type),
        fetch_one=True
    )
    return result[0] if result else None


def update_sync_timestamp(athlete_id: str, data_type: str, timestamp: Any):
    """
    Update the sync timestamp for an athlete and data type.
    
    Args:
        athlete_id: Athlete UUID
        data_type: Type of data
        timestamp: New sync timestamp
    """
    query = """
        INSERT INTO sync (athlete_id, data_type, last_synced_timestamp)
        VALUES (%s, %s, %s)
        ON CONFLICT (athlete_id, data_type)
        DO UPDATE SET last_synced_timestamp=EXCLUDED.last_synced_timestamp
    """
    execute_query(query, (athlete_id, data_type, timestamp)) 