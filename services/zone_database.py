"""
Zone analysis database service.
Handles storage and retrieval of workout zone analysis results.
"""

import logging
from typing import Dict, Any, Optional, List
from utils.database import execute_query, get_athlete_uuid
import uuid

logger = logging.getLogger(__name__)

def store_workout_zones(workout_id: str, athlete_id: Optional[str] = None, zone_data: Dict[str, Any] = None) -> bool:
    """
    Store zone analysis results for a workout.
    
    Args:
        workout_id: UUID of the workout
        athlete_id: UUID of the athlete (optional, will be looked up if not provided)
        zone_data: Zone analysis results from the agent
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract zone data
        hr_zones = zone_data.get("heart_rate_zones", {})
        power_zones = zone_data.get("power_zones", {})
        total_duration = zone_data.get("total_duration_minutes", 0)
        zones_available = zone_data.get("zones_available", {})
        
        # First check if the workout exists and get athlete_id if not provided
        check_query = "SELECT id, athlete_id FROM workout WHERE id = %s"
        workout_data = execute_query(check_query, (workout_id,), fetch_one=True)
        
        if not workout_data:
            logger.warning(f"Workout {workout_id} does not exist, skipping zone storage")
            return False
        
        # Use provided athlete_id or get from workout
        if athlete_id is None:
            athlete_id = workout_data[1]  # athlete_id from the query result
        
        query = """
        INSERT INTO workout_zones (
            workout_id, athlete_id,
            hr_z1_minutes, hr_z2_minutes, hr_zx_minutes, hr_z3_minutes, hr_zy_minutes, hr_z4_minutes, hr_z5_minutes,
            power_z1_minutes, power_z2_minutes, power_zx_minutes, power_z3_minutes, power_zy_minutes, power_z4_minutes, power_z5_minutes,
            total_duration_minutes, hr_zones_available, power_zones_available
        ) VALUES (
            %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s
        ) ON CONFLICT (workout_id) DO UPDATE SET
            hr_z1_minutes = EXCLUDED.hr_z1_minutes,
            hr_z2_minutes = EXCLUDED.hr_z2_minutes,
            hr_zx_minutes = EXCLUDED.hr_zx_minutes,
            hr_z3_minutes = EXCLUDED.hr_z3_minutes,
            hr_zy_minutes = EXCLUDED.hr_zy_minutes,
            hr_z4_minutes = EXCLUDED.hr_z4_minutes,
            hr_z5_minutes = EXCLUDED.hr_z5_minutes,
            power_z1_minutes = EXCLUDED.power_z1_minutes,
            power_z2_minutes = EXCLUDED.power_z2_minutes,
            power_zx_minutes = EXCLUDED.power_zx_minutes,
            power_z3_minutes = EXCLUDED.power_z3_minutes,
            power_zy_minutes = EXCLUDED.power_zy_minutes,
            power_z4_minutes = EXCLUDED.power_z4_minutes,
            power_z5_minutes = EXCLUDED.power_z5_minutes,
            total_duration_minutes = EXCLUDED.total_duration_minutes,
            hr_zones_available = EXCLUDED.hr_zones_available,
            power_zones_available = EXCLUDED.power_zones_available,
            updated_at = NOW()
        """
        
        params = (
            workout_id, athlete_id,
            hr_zones.get("z1_minutes", 0), hr_zones.get("z2_minutes", 0), hr_zones.get("zx_minutes", 0),
            hr_zones.get("z3_minutes", 0), hr_zones.get("zy_minutes", 0), hr_zones.get("z4_minutes", 0), hr_zones.get("z5_minutes", 0),
            power_zones.get("z1_minutes", 0), power_zones.get("z2_minutes", 0), power_zones.get("zx_minutes", 0),
            power_zones.get("z3_minutes", 0), power_zones.get("zy_minutes", 0), power_zones.get("z4_minutes", 0), power_zones.get("z5_minutes", 0),
            total_duration, zones_available.get("heart_rate", False), zones_available.get("power", False)
        )
        
        execute_query(query, params)
        logger.info(f"Stored zone analysis for workout {workout_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store zone analysis for workout {workout_id}: {e}")
        return False

def get_workout_zones(workout_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve zone analysis results for a workout.
    
    Args:
        workout_id: UUID of the workout
        
    Returns:
        Zone analysis data or None if not found
    """
    try:
        query = """
        SELECT 
            hr_z1_minutes, hr_z2_minutes, hr_zx_minutes, hr_z3_minutes, hr_zy_minutes, hr_z4_minutes, hr_z5_minutes,
            power_z1_minutes, power_z2_minutes, power_zx_minutes, power_z3_minutes, power_zy_minutes, power_z4_minutes, power_z5_minutes,
            total_duration_minutes, hr_zones_available, power_zones_available
        FROM workout_zones 
        WHERE workout_id = %s
        """
        
        result = execute_query(query, (workout_id,), fetch_one=True)
        
        if not result:
            return None
        
        # Convert to dictionary format
        zone_data = {
            "heart_rate_zones": {
                "z1_minutes": float(result[0]),
                "z2_minutes": float(result[1]),
                "zx_minutes": float(result[2]),
                "z3_minutes": float(result[3]),
                "zy_minutes": float(result[4]),
                "z4_minutes": float(result[5]),
                "z5_minutes": float(result[6])
            },
            "power_zones": {
                "z1_minutes": float(result[7]),
                "z2_minutes": float(result[8]),
                "zx_minutes": float(result[9]),
                "z3_minutes": float(result[10]),
                "zy_minutes": float(result[11]),
                "z4_minutes": float(result[12]),
                "z5_minutes": float(result[13])
            },
            "total_duration_minutes": float(result[14]),
            "zones_available": {
                "heart_rate": bool(result[15]),
                "power": bool(result[16])
            }
        }
        
        return zone_data
        
    except Exception as e:
        logger.error(f"Failed to retrieve zone analysis for workout {workout_id}: {e}")
        return None

def get_athlete_zone_summary(athlete_id: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Get zone summary for an athlete over a date range.
    
    Args:
        athlete_id: UUID of the athlete
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        
    Returns:
        Summary of zone data
    """
    try:
        # Build date filter
        date_filter = ""
        params = [athlete_id]
        
        if start_date and end_date:
            date_filter = "AND w.timestamp BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        elif start_date:
            date_filter = "AND w.timestamp >= %s"
            params.append(start_date)
        elif end_date:
            date_filter = "AND w.timestamp <= %s"
            params.append(end_date)
        
        query = f"""
        SELECT 
            SUM(wz.hr_z1_minutes) as hr_z1_total,
            SUM(wz.hr_z2_minutes) as hr_z2_total,
            SUM(wz.hr_zx_minutes) as hr_zx_total,
            SUM(wz.hr_z3_minutes) as hr_z3_total,
            SUM(wz.hr_zy_minutes) as hr_zy_total,
            SUM(wz.hr_z4_minutes) as hr_z4_total,
            SUM(wz.hr_z5_minutes) as hr_z5_total,
            SUM(wz.power_z1_minutes) as power_z1_total,
            SUM(wz.power_z2_minutes) as power_z2_total,
            SUM(wz.power_zx_minutes) as power_zx_total,
            SUM(wz.power_z3_minutes) as power_z3_total,
            SUM(wz.power_zy_minutes) as power_zy_total,
            SUM(wz.power_z4_minutes) as power_z4_total,
            SUM(wz.power_z5_minutes) as power_z5_total,
            SUM(wz.total_duration_minutes) as total_duration,
            COUNT(wz.id) as workout_count
        FROM workout_zones wz
        JOIN workout w ON wz.workout_id = w.id
        WHERE wz.athlete_id = %s {date_filter}
        """
        
        result = execute_query(query, tuple(params), fetch_one=True)
        
        if not result:
            return {
                "heart_rate_zones": {"z1_minutes": 0, "z2_minutes": 0, "zx_minutes": 0, "z3_minutes": 0, "zy_minutes": 0, "z4_minutes": 0, "z5_minutes": 0},
                "power_zones": {"z1_minutes": 0, "z2_minutes": 0, "zx_minutes": 0, "z3_minutes": 0, "zy_minutes": 0, "z4_minutes": 0, "z5_minutes": 0},
                "total_duration_minutes": 0,
                "workout_count": 0
            }
        
        return {
            "heart_rate_zones": {
                "z1_minutes": float(result[0] or 0),
                "z2_minutes": float(result[1] or 0),
                "zx_minutes": float(result[2] or 0),
                "z3_minutes": float(result[3] or 0),
                "zy_minutes": float(result[4] or 0),
                "z4_minutes": float(result[5] or 0),
                "z5_minutes": float(result[6] or 0)
            },
            "power_zones": {
                "z1_minutes": float(result[7] or 0),
                "z2_minutes": float(result[8] or 0),
                "zx_minutes": float(result[9] or 0),
                "z3_minutes": float(result[10] or 0),
                "zy_minutes": float(result[11] or 0),
                "z4_minutes": float(result[12] or 0),
                "z5_minutes": float(result[13] or 0)
            },
            "total_duration_minutes": float(result[14] or 0),
            "workout_count": int(result[15] or 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get zone summary for athlete {athlete_id}: {e}")
        return {
            "heart_rate_zones": {"z1_minutes": 0, "z2_minutes": 0, "zx_minutes": 0, "z3_minutes": 0, "zy_minutes": 0, "z4_minutes": 0, "z5_minutes": 0},
            "power_zones": {"z1_minutes": 0, "z2_minutes": 0, "zx_minutes": 0, "z3_minutes": 0, "zy_minutes": 0, "z4_minutes": 0, "z5_minutes": 0},
            "total_duration_minutes": 0,
            "workout_count": 0
        } 