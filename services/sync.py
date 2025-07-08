"""
Garmin data synchronization service.
Handles downloading and syncing health metrics and workouts from Garmin Connect.
"""

import logging
import datetime
import uuid
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from services.garmin_auth import get_garmin_client
from services.preprocess import process_downloaded_files
from utils.models import Workout
from utils.database import (
    get_db_conn, execute_query, check_record_exists, 
    get_athlete_uuid, get_last_sync_timestamp, update_sync_timestamp
)
from utils.file_utils import (
    sanitize_filename, ensure_directory, save_json_data, load_json_data,
    extract_date_from_file, parse_datetime_safe, parse_iso_datetime_safe,
    ensure_naive_datetime, find_csv_file, get_workout_type_from_data
)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sync_debug.log")
    ]
)
logger = logging.getLogger("sync")

# Constants
DATA_DIR = Path("data")
PROFILE_PATH = Path("data/athlete_profile/profile.json")


def get_seed_athlete_uuid() -> str:
    """
    Get the athlete UUID by reading the athlete name from profile.json and looking it up in the database.
    Returns:
        Athlete UUID string
    Raises:
        ValueError if athlete not found or name missing
    """
    try:
        with open(PROFILE_PATH) as f:
            profile = json.load(f)
        athlete_name = profile.get("athlete_id")
        if not athlete_name:
            raise ValueError("athlete_id (name) missing in profile.json")
        return get_athlete_uuid(athlete_name)
    except Exception as e:
        raise ValueError(f"Failed to get athlete UUID from profile.json: {e}")


def download_activity_file(garmin, activity_id: str, activity_name: str, 
                          fmt, ext: str, workout_dir: Path) -> Optional[Path]:
    """
    Download a single activity file in specified format.
    
    Args:
        garmin: Garmin client instance
        activity_id: Activity ID
        activity_name: Activity name
        fmt: Download format
        ext: File extension
        workout_dir: Target directory
        
    Returns:
        Path to downloaded file or None
    """
    safe_name = sanitize_filename(activity_name)
    out_path = workout_dir / f"{safe_name}_{activity_id}.{ext}"
    
    if out_path.exists():
        logger.info(f"{out_path} already exists, skipping.")
        return None
    
    try:
        data = garmin.download_activity(activity_id, fmt)
        with open(out_path, "wb") as f:
            f.write(data)
        logger.info(f"Downloaded {out_path}")
        return out_path
    except Exception as e:
        logger.error(f"Failed to download {activity_id} as {ext}: {e}")
        return None


def fetch_and_save_activities(garmin, date_dir: Path, start_date, end_date) -> List[Path]:
    """
    Download all activity files for a date range.
    
    Args:
        garmin: Garmin client instance
        date_dir: Date directory
        start_date: Start date
        end_date: End date
        
    Returns:
        List of downloaded file paths
    """
    workout_dir = ensure_directory(date_dir / "workout")
    activities = garmin.get_activities_by_date(start_date, end_date)
    downloaded_files = []
    
    for activity in activities:
        activity_id = activity["activityId"]
        activity_name = activity.get("activityName", f"activity_{activity_id}")
        
        # Download in multiple formats
        formats = [
            (garmin.ActivityDownloadFormat.ORIGINAL, "zip"),
            (garmin.ActivityDownloadFormat.TCX, "tcx"),
            (garmin.ActivityDownloadFormat.GPX, "gpx"),
            (garmin.ActivityDownloadFormat.CSV, "csv"),
        ]
        
        for fmt, ext in formats:
            file_path = download_activity_file(garmin, activity_id, activity_name, fmt, ext, workout_dir)
            if file_path:
                downloaded_files.append(file_path)
    
    return downloaded_files


def extract_health_metric_timestamp(data: Dict[str, Any], metric: str) -> Optional[datetime]:
    """
    Extract timestamp from health metric data.
    
    Args:
        data: Health metric data
        metric: Metric type (sleep, hrv, rhr)
        
    Returns:
        Parsed datetime or None
    """
    calendar_date = None
    if metric == "hrv":
        # hrvSummary.calendarDate
        calendar_date = data.get("hrvSummary", {}).get("calendarDate")
    elif metric == "rhr":
        # allMetrics.metricsMap.WELLNESS_RESTING_HEART_RATE[0].calendarDate
        try:
            calendar_date = data["allMetrics"]["metricsMap"]["WELLNESS_RESTING_HEART_RATE"][0]["calendarDate"]
        except (KeyError, IndexError, TypeError):
            calendar_date = None
    elif metric == "sleep":
        # dailySleepDTO.calendarDate
        calendar_date = data.get("calendarDate")
        if not calendar_date:
            calendar_date = data.get("dailySleepDTO", {}).get("calendarDate")
    # Fallback: try to extract from file or other means if needed
    if calendar_date:
        return parse_datetime_safe(calendar_date)
    return None


def should_insert_health_metric(athlete_uuid: str, record_ts: datetime, 
                               last_ts: Optional[datetime], metric: str) -> bool:
    """
    Determine if health metric should be inserted into database.
    
    Args:
        athlete_uuid: Athlete UUID
        record_ts: Record timestamp
        last_ts: Last sync timestamp
        metric: Metric type
        
    Returns:
        True if should insert, False otherwise
    """
    # Check if newer than last sync
    if last_ts is not None and record_ts <= last_ts:
        logger.info(f"{metric} entry for athlete_id={athlete_uuid} and timestamp={record_ts} already synced or not newer, skipping.")
        return False
    
    # Check for duplicate
    if check_record_exists(metric, {"athlete_id": athlete_uuid, "timestamp": record_ts.date()}):
        logger.info(f"{metric} entry for athlete_id={athlete_uuid} and timestamp={record_ts} already exists in database, skipping.")
        return False
    
    return True


def fetch_and_save_health_metrics(garmin, date_dir: Path, date, last_ts: Optional[datetime], 
                                 athlete_uuid: str, metric: str) -> List[Path]:
    """
    Download and save health metrics for a specific date.
    
    Args:
        garmin: Garmin client instance
        date_dir: Date directory
        date: Date to fetch
        last_ts: Last sync timestamp
        athlete_uuid: Athlete UUID
        metric: Metric type (sleep, hrv, rhr)
        
    Returns:
        List of downloaded file paths
    """
    logger.debug(f"fetch_and_save_health_metrics called for date {date}")
    
    health_dir = ensure_directory(date_dir / "health_metrics")
    metrics = {
        "sleep": (garmin.get_sleep_data, "sleep.json"),
        "hrv": (garmin.get_hrv_data, "hrv.json"),
        "rhr": (garmin.get_rhr_day, "rhr.json"),
    }
    
    if metric not in metrics:
        logger.error(f"Unknown metric type: {metric}")
        return []
    
    func, filename = metrics[metric]
    out_path = health_dir / filename
    
    try:
        # Download and save data
        data = func(date)
        if not save_json_data(data, out_path):
            return []
        
        # Extract timestamp
        record_ts = extract_health_metric_timestamp(data, metric)
        if not record_ts:
            calendar_date = extract_date_from_file(out_path, context="health")
            record_ts = parse_datetime_safe(calendar_date) if calendar_date else None
        
        if not athlete_uuid or not record_ts:
            logger.warning(f"Missing athlete_id or timestamp for {metric} on {date}")
            return [out_path]
        
        # Check if should insert
        if not should_insert_health_metric(athlete_uuid, record_ts, last_ts, metric):
            return [out_path]
        
        # Insert into database
        execute_query(
            f"INSERT INTO {metric} (athlete_id, timestamp, json_file, synced_at) VALUES (%s, %s, %s, now())",
            (athlete_uuid, record_ts.date(), json.dumps(data))
        )
        logger.info(f"Inserted {metric} entry for athlete_id={athlete_uuid} and timestamp={record_ts} into DB.")
        
        # Update sync table
        update_sync_timestamp(athlete_uuid, metric, record_ts)
        
    except Exception as e:
        logger.error(f"Failed to fetch or insert {metric} for {date}: {e}")
    
    return [out_path]


def process_single_workout_file(processed_file: Path, athlete_uuid: str, 
                               sync_timestamp: Optional[datetime]) -> Optional[datetime]:
    """
    Process a single workout file and insert into database.
    
    Args:
        processed_file: Path to processed workout file
        athlete_uuid: Athlete UUID
        sync_timestamp: Last sync timestamp
        
    Returns:
        Record timestamp if successful, None otherwise
    """
    try:
        # Extract date and load data
        calendar_date = extract_date_from_file(processed_file, context="workout")
        data = load_json_data(processed_file)
        if not data:
            return None
        
        # Extract workout information
        workout_type = get_workout_type_from_data(data, processed_file.name)
        tss = data.get('tss')
        activity_id = data.get('activity_id')
        
        # Extract timestamp
        record_ts = None
        if 'start_time' in data:
            record_ts = parse_iso_datetime_safe(data['start_time'])
        
        if not record_ts and calendar_date:
            record_ts = parse_datetime_safe(calendar_date)
        
        if not record_ts:
            logger.warning(f"Could not extract timestamp for workout: {processed_file.name}")
            return None
        
        # Check sync timestamp
        if sync_timestamp is not None:
            sync_timestamp = ensure_naive_datetime(sync_timestamp)
            if record_ts <= sync_timestamp:
                logger.info(f"Workout entry for athlete_id={athlete_uuid} and timestamp={record_ts} already synced or not newer, skipping.")
                return None
        
        # Check for duplicate using activity_id if available, otherwise use timestamp
        if activity_id:
            # Use activity_id for more precise duplicate detection
            if check_record_exists("workout", {"athlete_id": athlete_uuid, "json_file->>'activity_id'": activity_id}):
                logger.info(f"Workout with activity_id={activity_id} already exists in database, skipping DB insert.")
                return None
        else:
            # Fallback to timestamp-based duplicate check
            if check_record_exists("workout", {"athlete_id": athlete_uuid, "timestamp": record_ts}):
                logger.info(f"Workout entry for athlete_id={athlete_uuid} and timestamp={record_ts} already exists in database, skipping DB insert.")
                return None
        
        # Find CSV file
        csv_file_content = find_csv_file(processed_file)
        
        # Create and insert workout
        workout = Workout(
            id=str(uuid.uuid4()),
            athlete_id=athlete_uuid,
            timestamp=record_ts.isoformat(sep=' ', timespec='seconds'),
            workout_type=workout_type,
            tss=tss,
            duration_sec=data.get('duration_sec'),
            duration_hr=data.get('duration_hr'),
            json_file=data,
            csv_file=csv_file_content,
            synced_at=datetime.datetime.utcnow().replace(tzinfo=None).isoformat(sep=' ', timespec='seconds')
        )
        
        with get_db_conn() as conn:
            workout.insert(conn)
            conn.commit()
        
        logger.info(f"Successfully inserted workout {processed_file.name}")
        return record_ts
        
    except Exception as e:
        logger.error(f"Failed to sync workout {processed_file}: {e}")
        return None


def sync_processed_workouts_to_db(date_dir: Path, athlete_uuid: str, 
                                 update_sync: bool = False, 
                                 sync_timestamp: Optional[datetime] = None) -> bool:
    """
    Sync all processed workout files in a directory to the database.
    
    Args:
        date_dir: Date directory containing workout files
        athlete_uuid: Athlete UUID
        update_sync: Whether to update sync table
        sync_timestamp: Last sync timestamp
        
    Returns:
        True if any workouts were inserted, False otherwise
    """
    workout_dir = date_dir / "workout"
    if not workout_dir.exists():
        return False
    
    inserted_any = False
    latest_ts = sync_timestamp
    
    for processed_file in workout_dir.glob("*_processed.json"):
        record_ts = process_single_workout_file(processed_file, athlete_uuid, sync_timestamp)
        if record_ts:
            inserted_any = True
            if not latest_ts or record_ts > latest_ts:
                latest_ts = record_ts
    
    # Update sync table if requested
    if update_sync and inserted_any and latest_ts:
        update_sync_timestamp(athlete_uuid, 'workout', latest_ts)
    
    return inserted_any


def sync_last_n_days(n: int = 7):
    """
    Sync data for the last n days.
    
    Args:
        n: Number of days to sync
    """
    garmin = get_garmin_client()
    today = datetime.date.today()
    
    for delta in range(n):
        date = today - datetime.timedelta(days=delta)
        date_dir = ensure_directory(DATA_DIR / str(date))
        
        # Download health metrics for each type
        for metric in ['sleep', 'hrv', 'rhr']:
            fetch_and_save_health_metrics(garmin, date_dir, date, None, None, metric)
        
        # Download activities
        fetch_and_save_activities(garmin, date_dir, date, date)
        
        # Process and sync workouts
        workout_dir = date_dir / "workout"
        if workout_dir.exists():
            process_downloaded_files(workout_dir)
            
            # Get athlete UUID and sync to DB with sync table update
            athlete_uuid = get_seed_athlete_uuid()
            sync_processed_workouts_to_db(date_dir, athlete_uuid, update_sync=True)


def sync_since_last_entry():
    """
    Sync data since the last entry for each data type.
    """
    garmin = get_garmin_client()
    athlete_uuid = get_seed_athlete_uuid()
    today = datetime.date.today()
    
    # Sync health metrics
    data_types = ['sleep', 'hrv', 'rhr']
    for data_type in data_types:
        last_ts = get_last_sync_timestamp(athlete_uuid, data_type)
        
        for delta in range(7):
            date = today - datetime.timedelta(days=delta)
            date_dir = ensure_directory(DATA_DIR / str(date))
            fetch_and_save_health_metrics(garmin, date_dir, date, last_ts, athlete_uuid, data_type)
    
    # Sync workouts
    workout_last_ts = get_last_sync_timestamp(athlete_uuid, 'workout')
    for delta in range(7):
        date = today - datetime.timedelta(days=delta)
        date_dir = ensure_directory(DATA_DIR / str(date))
        
        fetch_and_save_activities(garmin, date_dir, date, date)
        workout_dir = date_dir / "workout"
        
        if workout_dir.exists():
            process_downloaded_files(workout_dir)
            sync_processed_workouts_to_db(date_dir, athlete_uuid, update_sync=True, sync_timestamp=workout_last_ts)