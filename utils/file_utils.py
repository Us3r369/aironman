"""
File utilities for AIronman app.
Provides common file operations, path construction, and data extraction.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from agents.date_extractor_agent import get_date_from_file_content

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    return "_".join(filename.split()).replace("/", "_")


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json_data(data: Dict[str, Any], file_path: Path) -> bool:
    """
    Save data to JSON file with error handling.
    
    Args:
        data: Data to save
        file_path: Target file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save data to {file_path}: {e}")
        return False


def load_json_data(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load data from JSON file with error handling.
    
    Args:
        file_path: Source file path
        
    Returns:
        Loaded data or None if failed
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load data from {file_path}: {e}")
        return None


def extract_date_from_file(file_path: Path, context: str = "health") -> Optional[str]:
    """
    Extract date from file content using CrewAI agent.
    
    Args:
        file_path: Path to the file
        context: Context for date extraction ('health' or 'workout')
        
    Returns:
        Extracted date string or None
    """
    try:
        with open(file_path) as f:
            lines = ''.join([next(f) for _ in range(50)])
        return get_date_from_file_content(lines, context)
    except Exception as e:
        logger.error(f"Failed to extract date from {file_path}: {e}")
        return None


def parse_datetime_safe(datetime_str: str, format_str: str = "%Y-%m-%d") -> Optional[datetime]:
    """
    Safely parse datetime string with error handling.
    
    Args:
        datetime_str: Datetime string to parse
        format_str: Format string for parsing
        
    Returns:
        Parsed datetime or None
    """
    try:
        return datetime.strptime(datetime_str, format_str)
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{datetime_str}' with format '{format_str}': {e}")
        return None


def parse_iso_datetime_safe(datetime_str: str) -> Optional[datetime]:
    """
    Safely parse ISO datetime string and convert to naive UTC.
    
    Args:
        datetime_str: ISO datetime string
        
    Returns:
        Naive UTC datetime or None
    """
    try:
        # Handle different ISO formats
        if datetime_str.endswith('Z'):
            # Replace Z with +00:00 for proper parsing
            datetime_str = datetime_str.replace('Z', '+00:00')
        
        # Parse as aware datetime
        aware_dt = datetime.fromisoformat(datetime_str)
        
        # Convert to UTC and make naive
        if aware_dt.tzinfo is not None:
            return aware_dt.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            # If no timezone info, assume UTC
            return aware_dt
        
    except Exception as e:
        logger.warning(f"Failed to parse ISO datetime '{datetime_str}': {e}")
        return None


def ensure_naive_datetime(dt: datetime) -> datetime:
    """
    Ensure datetime is naive (no timezone info).
    
    Args:
        dt: Datetime object
        
    Returns:
        Naive datetime object
    """
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def find_csv_file(processed_file_path: Path) -> Optional[str]:
    """
    Find corresponding CSV file for a processed JSON file.
    
    Args:
        processed_file_path: Path to processed JSON file
        
    Returns:
        CSV file content as string or None
    """
    base_name = processed_file_path.stem
    if base_name.endswith('_processed'):
        csv_base = base_name[:-10]  # remove '_processed'
    else:
        csv_base = base_name
    
    csv_path = processed_file_path.parent / f"{csv_base}.csv"
    
    if csv_path.exists():
        try:
            with open(csv_path, 'r') as csvf:
                return csvf.read()
        except Exception as e:
            logger.error(f"Failed to read CSV file {csv_path}: {e}")
    
    return None


def get_workout_type_from_data(data: Dict[str, Any], filename: str) -> str:
    """
    Extract workout type from data or filename.
    
    Args:
        data: Workout data dictionary
        filename: Workout filename
        
    Returns:
        Workout type string
    """
    # Try to get from data first
    workout_type = data.get('workout_type')
    if workout_type:
        return workout_type
    
    # Fallback to filename analysis
    fname = filename.lower()
    for workout_type in ['ride', 'run', 'swim', 'strength']:
        if workout_type in fname:
            return workout_type
    
    return 'other' 