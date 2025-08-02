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

# ---------------------------------------------------------------------------
# Athlete Profile helpers
# ---------------------------------------------------------------------------


def _parse_profile_row(row) -> Dict[str, Any]:
    """Convert a SELECT * row from athlete_profile into the nested profile dict
    structure expected throughout the codebase (matches the schema used for
    profile.json). This mirrors the response of the GET /api/profile endpoint
    but can be used anywhere in the backend (services, agents, etc.).

    Args:
        row: Sequence returned by cursor.fetchone() using the column order of
             the comprehensive SELECT in api.main.get_profile.

    Returns:
        Dict[str, Any] ready for downstream consumers (zones, test_dates, etc.)
    """
    import datetime as dt

    def to_str(val):
        if isinstance(val, dt.date):
            return val.strftime('%Y-%m-%d')
        elif val is not None:
            return str(val)
        return None

    # Keep the same column order as api.main.get_profile – easier maintenance.
    profile = {
        "athlete_id": row[0],
        "last_updated": to_str(row[1]),
        "zones": {
            "heart_rate": {
                "lt_hr": row[2],
                "zones": {
                    "z1": [row[3], row[4]],
                    "z2": [row[5], row[6]],
                    "zx": [row[7], row[8]],
                    "z3": [row[9], row[10]],
                    "zy": [row[11], row[12]],
                    "z4": [row[13], row[14]],
                    "z5": [row[15], row[16]],
                },
            },
            "bike_power": {
                "ftp": row[17],
                "zones": {
                    "z1": [row[18], row[19]],
                    "z2": [row[20], row[21]],
                    "zx": [row[22], row[23]],
                    "z3": [row[24], row[25]],
                    "zy": [row[26], row[27]],
                    "z4": [row[28], row[29]],
                    "z5": [row[30], row[31]],
                },
            },
            "run_power": {
                "ltp": row[32],
                "critical_power": row[33],
                "zones": {
                    "z1": [row[34], row[35]],
                    "z2": [row[36], row[37]],
                    "zx": [row[38], row[39]],
                    "z3": [row[40], row[41]],
                    "zy": [row[42], row[43]],
                    "z4": [row[44], row[45]],
                    "z5": [row[46], row[47]],
                },
            },
            "run_pace": {
                "threshold_pace_per_km": to_str(row[48]),
                "zones": {
                    "z1": [to_str(row[49]), to_str(row[50])],
                    "z2": [to_str(row[51]), to_str(row[52])],
                    "zx": [to_str(row[53]), to_str(row[54])],
                    "z3": [to_str(row[55]), to_str(row[56])],
                    "zy": [to_str(row[57]), to_str(row[58])],
                    "z4": [to_str(row[59]), to_str(row[60])],
                    "z5": [to_str(row[61]), to_str(row[62])],
                },
            },
            "swim": {
                "css_pace_per_100m": to_str(row[63]),
                "zones": {
                    "z1": [to_str(row[64]), to_str(row[65])],
                    "z2": [to_str(row[66]), to_str(row[67])],
                    "zx": [to_str(row[68]), to_str(row[69])],
                    "z3": [to_str(row[70]), to_str(row[71])],
                    "zy": [to_str(row[72]), to_str(row[73])],
                    "z4": [to_str(row[74]), to_str(row[75])],
                    "z5": [to_str(row[76]), to_str(row[77])],
                },
            },
        },
        "test_dates": {
            "bike_ftp_test": to_str(row[78]),
            "run_ltp_test": to_str(row[79]),
            "swim_css_test": to_str(row[80]),
        },
    }

    return profile


def get_active_profile(athlete_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch the currently-active athlete profile.

    If *athlete_id* (human-readable name, same as *json_athlete_id* column)
    is provided, we filter by it; otherwise we simply return the most recent
    active profile in the database.  Returns **None** if no row found.
    """

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            base_query = (
                "SELECT json_athlete_id, valid_from, "
                "       lt_heartrate, "
                "       hr_zone_z1_lower, hr_zone_z1_upper, "
                "       hr_zone_z2_lower, hr_zone_z2_upper, "
                "       hr_zone_zx_lower, hr_zone_zx_upper, "
                "       hr_zone_z3_lower, hr_zone_z3_upper, "
                "       hr_zone_zy_lower, hr_zone_zy_upper, "
                "       hr_zone_z4_lower, hr_zone_z4_upper, "
                "       hr_zone_z5_lower, hr_zone_z5_upper, "
                "       bike_ftp_power, "
                "       bike_power_zone_z1_lower, bike_power_zone_z1_upper, "
                "       bike_power_zone_z2_lower, bike_power_zone_z2_upper, "
                "       bike_power_zone_zx_lower, bike_power_zone_zx_upper, "
                "       bike_power_zone_z3_lower, bike_power_zone_z3_upper, "
                "       bike_power_zone_zy_lower, bike_power_zone_zy_upper, "
                "       bike_power_zone_z4_lower, bike_power_zone_z4_upper, "
                "       bike_power_zone_z5_lower, bike_power_zone_z5_upper, "
                "       run_ltp_power, run_critical_power, "
                "       run_power_zone_z1_lower, run_power_zone_z1_upper, "
                "       run_power_zone_z2_lower, run_power_zone_z2_upper, "
                "       run_power_zone_zx_lower, run_power_zone_zx_upper, "
                "       run_power_zone_z3_lower, run_power_zone_z3_upper, "
                "       run_power_zone_zy_lower, run_power_zone_zy_upper, "
                "       run_power_zone_z4_lower, run_power_zone_z4_upper, "
                "       run_power_zone_z5_lower, run_power_zone_z5_upper, "
                "       run_threshold_pace, "
                "       run_pace_zone_z1_lower, run_pace_zone_z1_upper, "
                "       run_pace_zone_z2_lower, run_pace_zone_z2_upper, "
                "       run_pace_zone_zx_lower, run_pace_zone_zx_upper, "
                "       run_pace_zone_z3_lower, run_pace_zone_z3_upper, "
                "       run_pace_zone_zy_lower, run_pace_zone_zy_upper, "
                "       run_pace_zone_z4_lower, run_pace_zone_z4_upper, "
                "       run_pace_zone_z5_lower, run_pace_zone_z5_upper, "
                "       swim_css_pace_per_100, "
                "       swim_zone_z1_lower, swim_zone_z1_upper, "
                "       swim_zone_z2_lower, swim_zone_z2_upper, "
                "       swim_zone_zx_lower, swim_zone_zx_upper, "
                "       swim_zone_z3_lower, swim_zone_z3_upper, "
                "       swim_zone_zy_lower, swim_zone_zy_upper, "
                "       swim_zone_z4_lower, swim_zone_z4_upper, "
                "       swim_zone_z5_lower, swim_zone_z5_upper, "
                "       bike_ftp_test, run_ltp_test, swim_css_test "
                "FROM athlete_profile "
                "WHERE valid_to IS NULL "
            )

            params = []
            if athlete_id:
                base_query += "AND json_athlete_id = %s "
                params.append(athlete_id)

            base_query += "ORDER BY valid_from DESC LIMIT 1"

            cur.execute(base_query, tuple(params) if params else None)
            row = cur.fetchone()
            if not row:
                return None

            return _parse_profile_row(row) 

def test_recovery_analysis_table():
    """Test if the daily_recovery_analysis table exists and is accessible."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'daily_recovery_analysis'
                );
            """)
            exists = cur.fetchone()[0]
            if exists:
                # Test inserting a dummy record
                cur.execute("""
                    INSERT INTO daily_recovery_analysis 
                    (athlete_id, analysis_date, status, detailed_reasoning) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (athlete_id, analysis_date) DO NOTHING
                """, (
                    '1a5d4210-bfcc-4b1a-8b37-8e42e83524e9',  # Test athlete ID
                    '2025-08-02',  # Today's date
                    'good',
                    'Test analysis - table is working'
                ))
                conn.commit()
                return True
            return False 