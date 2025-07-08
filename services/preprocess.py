"""
Workout file preprocessing service.
Handles extraction, parsing, and processing of workout files from various formats.
"""

import logging
import json
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from fitparse import FitFile
import xml.etree.ElementTree as ET
from dateutil import parser as dtparser
import pandas as pd
from utils.config import settings
from utils.file_utils import sanitize_filename, save_json_data, load_json_data
import csv

logger = logging.getLogger("preprocess")
logging.basicConfig(level=logging.INFO)

# Constants
PROFILE_PATH = Path("data/athlete_profile/profile.json")
PAUSE_THRESHOLD = settings.PAUSE_THRESHOLD


def extract_power_time_series_from_fit(fit_file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract power time series data from FIT file.
    
    Args:
        fit_file_path: Path to FIT file
        
    Returns:
        List of power data points
    """
    power_series = []
    try:
        fitfile = FitFile(str(fit_file_path))
        for record in fitfile.get_messages("record"):
            fields = {f.name: f.value for f in record.fields}
            timestamp = fields.get("timestamp")
            power_fields = {
                name: value for name, value in fields.items() if "power" in name.lower()
            }
            if timestamp is not None and power_fields:
                if hasattr(timestamp, "isoformat"):
                    timestamp = timestamp.isoformat()
                entry = {"timestamp": timestamp}
                entry.update(power_fields)
                power_series.append(entry)
    except Exception as e:
        logger.error(f"Failed to extract power from FIT: {e}")
    return power_series


def parse_tcx_file(tcx_path: Path) -> List[Dict[str, Any]]:
    """
    Parse TCX file and extract trackpoint data.
    
    Args:
        tcx_path: Path to TCX file
        
    Returns:
        List of trackpoint dictionaries
    """
    trackpoints = []
    try:
        tree = ET.parse(str(tcx_path))
        root = tree.getroot()
        ns = {
            "tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
            "ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
        }
        
        for tp in root.findall(".//tcx:Trackpoint", ns):
            entry = {}
            
            # Extract timestamp
            time_elem = tp.find("tcx:Time", ns)
            if time_elem is not None:
                entry["timestamp"] = time_elem.text
            
            # Extract various metrics
            metrics = [
                ("tcx:HeartRateBpm/tcx:Value", "heart_rate", int),
                ("tcx:Extensions/ns3:TPX/ns3:Speed", "speed", float),
                ("tcx:Extensions/ns3:TPX/ns3:RunCadence", "run_cadence", int),
                ("tcx:Cadence", "cadence", int),
                ("tcx:Extensions/ns3:TPX/ns3:Watts", "watts", int),
                ("tcx:AltitudeMeters", "altitude", float),
                ("tcx:DistanceMeters", "distance", float),
            ]
            
            for xpath, key, converter in metrics:
                elem = tp.find(xpath, ns)
                if elem is not None and elem.text:
                    try:
                        entry[key] = converter(elem.text)
                    except (ValueError, TypeError):
                        pass
            
            if "timestamp" in entry:
                trackpoints.append(entry)
                
    except Exception as e:
        logger.error(f"Failed to parse TCX file {tcx_path}: {e}")
    
    return trackpoints


def merge_power_into_tcx(tcx_trackpoints: List[Dict[str, Any]], 
                        power_series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge power data into TCX trackpoints based on timestamp.
    
    Args:
        tcx_trackpoints: TCX trackpoint data
        power_series: Power time series data
        
    Returns:
        Merged trackpoint data
    """
    power_lookup = {}
    for entry in power_series:
        try:
            ts = dtparser.parse(entry["timestamp"]).replace(microsecond=0, tzinfo=None)
            power_lookup[ts] = {k: v for k, v in entry.items() if k != "timestamp"}
        except Exception:
            continue
    
    merged = []
    for tp in tcx_trackpoints:
        try:
            ts = dtparser.parse(tp["timestamp"]).replace(microsecond=0, tzinfo=None)
            merged_tp = dict(tp)
            if ts in power_lookup:
                merged_tp.update(power_lookup[ts])
            merged.append(merged_tp)
        except Exception:
            merged.append(tp)
    
    return merged


def get_tcx_sport(tcx_path: Path) -> str:
    """
    Extract sport type from TCX file.
    
    Args:
        tcx_path: Path to TCX file
        
    Returns:
        Sport type string
    """
    try:
        tree = ET.parse(str(tcx_path))
        root = tree.getroot()
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        activity_elem = root.find(".//tcx:Activity", ns)
        
        if activity_elem is not None:
            sport = activity_elem.attrib.get("Sport", "Other").lower()
            sport_mapping = {
                "running": "run",
                "biking": "bike",
                "cycling": "bike",
                "swimming": "swim",
                "strength": "strength"
            }
            return sport_mapping.get(sport, "other")
    except Exception as e:
        logger.warning(f"Could not extract sport from TCX {tcx_path}: {e}")
    
    return "other"


def get_gpx_type(gpx_path: Path) -> Optional[str]:
    """
    Extract activity type from GPX file.
    
    Args:
        gpx_path: Path to GPX file
        
    Returns:
        Activity type or None
    """
    try:
        tree = ET.parse(str(gpx_path))
        root = tree.getroot()
        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
        type_elem = root.find(".//gpx:type", ns)
        
        if type_elem is not None and type_elem.text and "swim" in type_elem.text.lower():
            return "swim"
    except Exception as e:
        logger.warning(f"Could not extract type from GPX {gpx_path}: {e}")
    
    return None


def extract_start_time_from_tcx(tcx_path: Path) -> Optional[str]:
    """
    Extract start time from TCX file.
    
    Args:
        tcx_path: Path to TCX file
        
    Returns:
        Start time string or None
    """
    try:
        tree = ET.parse(str(tcx_path))
        root = tree.getroot()
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        id_elem = root.find(".//tcx:Activity/tcx:Id", ns)
        
        if id_elem is not None:
            return id_elem.text
    except Exception as e:
        logger.warning(f"Could not extract start_time from TCX {tcx_path}: {e}")
    
    return None


def parse_time_to_seconds(time_str: str) -> float:
    """
    Parse a time string in hh:mm:ss.sss or mm:ss.sss format to seconds (float).
    """
    if not time_str or time_str == '0':
        return 0.0
    try:
        parts = time_str.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(time_str)
    except Exception:
        return 0.0


def calculate_tss_bike(trackpoints: List[Dict[str, Any]], ftp: int) -> Tuple[Optional[float], Optional[int], Optional[float]]:
    """
    Calculate TSS for bike workout.
    
    Args:
        trackpoints: Trackpoint data
        ftp: Functional Threshold Power
        
    Returns:
        Tuple of (TSS, duration_sec, duration_hr)
    """
    df = pd.DataFrame(trackpoints)
    logger.info(f"This is the bike data {df.head()}")
    
    if 'power' not in df.columns or df.empty:
        return None, None, None
    
    df = df.dropna(subset=["power"])
    if df.empty:
        return None, None, None
    
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    
    # Calculate moving time
    time_diffs = df["timestamp"].diff().dt.total_seconds().fillna(0)
    moving_time = time_diffs[time_diffs < PAUSE_THRESHOLD].sum()
    
    duration_sec = moving_time
    duration_hr = duration_sec / 3600
    avg_power = df["power"].mean()
    IF = avg_power / ftp
    tss = duration_hr * (IF ** 2) * 100
    
    return round(tss, 2), int(duration_sec), round(duration_hr, 4)


def calculate_tss_run(trackpoints: List[Dict[str, Any]], critical_power: int) -> Tuple[Optional[float], Optional[int], Optional[float]]:
    """
    Calculate TSS for run workout.
    
    Args:
        trackpoints: Trackpoint data
        critical_power: Critical Power
        
    Returns:
        Tuple of (TSS, duration_sec, duration_hr)
    """
    df = pd.DataFrame(trackpoints)
    logger.info(f"This is the run data {df.head()}")
    
    power_col = 'Power' if 'Power' in df.columns else ('power' if 'power' in df.columns else None)
    if not power_col or df.empty:
        return None, None, None
    
    df = df.dropna(subset=[power_col])
    if df.empty:
        return None, None, None
    
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    
    # Calculate moving time
    time_diffs = df["timestamp"].diff().dt.total_seconds().fillna(0)
    moving_time = time_diffs[time_diffs < PAUSE_THRESHOLD].sum()
    
    duration_sec = moving_time
    duration_hr = duration_sec / 3600
    avg_power = df[power_col].mean()
    IF = avg_power / critical_power
    tss = duration_hr * (IF ** 2) * 100
    
    return round(tss, 2), int(duration_sec), round(duration_hr, 4)


def calculate_tss_swim(csv_file: Path, profile: Dict[str, Any]) -> Tuple[Optional[float], Optional[int], Optional[float]]:
    """
    Calculate TSS for swim workout using the swim CSV file.
    Args:
        csv_file: Path to the swim workout CSV file
        profile: Athlete profile data
    Returns:
        Tuple of (TSS, duration_sec, duration_hr)
    """
    try:
        css = profile["zones"]["swim"].get("css_pace_per_100m")
        if not css:
            return None, None, None
        # Convert CSS (pace per 100m, e.g. "1:40") to m/min
        m, s = map(int, css.split(":"))
        css_seconds = m * 60 + s
        css_speed = 100 / (css_seconds / 60)  # m/min
        total_distance = 0.0
        moving_time = 0.0
        with open(csv_file, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                split_val = row.get("Split", "").strip().lower()
                if split_val not in ("rest", "summary"):
                    try:
                        total_distance += float(row.get("Distance", 0))
                        # Parse time string to seconds
                        moving_time += parse_time_to_seconds(row.get("Time", "0")) / 60  # convert to minutes
                    except Exception:
                        continue
        if moving_time == 0 or css_speed == 0:
            return None, None, None
        nss = total_distance / moving_time  # m/min
        IF = nss / css_speed
        duration_hr = (moving_time / 60)  # moving_time is in minutes
        sTSS = (IF ** 3) * duration_hr * 100
        duration_sec = int(moving_time * 60)
        return round(sTSS, 2), duration_sec, round(duration_hr, 4)
    except Exception as e:
        logger.error(f"Failed to calculate swim TSS: {e}")
        return None, None, None


def extract_fit_from_zip(zip_path: Path, activity_name: str, activity_id: str, 
                        workout_dir: Path) -> Optional[Path]:
    """
    Extract FIT file from ZIP archive.
    
    Args:
        zip_path: Path to ZIP file
        activity_name: Activity name
        activity_id: Activity ID
        workout_dir: Target directory
        
    Returns:
        Path to extracted FIT file or None
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for name in zip_ref.namelist():
                if name.lower().endswith(".fit"):
                    safe_name = sanitize_filename(activity_name)
                    fit_file_path = workout_dir / f"{safe_name}_{activity_id}.fit"
                    with open(fit_file_path, "wb") as fit_out:
                        fit_out.write(zip_ref.read(name))
                    logger.info(f"Extracted FIT file: {fit_file_path}")
                    return fit_file_path
    except Exception as e:
        logger.error(f"Failed to extract FIT from ZIP {zip_path}: {e}")
    return None


def process_activity_files(tcx_path: Path, workout_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Process activity files for a single workout.
    Args:
        tcx_path: Path to TCX file
        workout_dir: Workout directory
    Returns:
        Processed workout data or None
    """
    base = tcx_path.stem
    parts = base.split("_")
    activity_id = parts[-1] if parts else base
    safe_name = "_".join(parts[:-1]) if len(parts) > 1 else base

    # Define file paths
    zip_path = workout_dir / f"{safe_name}_{activity_id}.zip"
    power_json_file = workout_dir / f"{safe_name}_{activity_id}_power.json"
    processed_json_file = workout_dir / f"{safe_name}_{activity_id}_processed.json"
    csv_file = workout_dir / f"{safe_name}_{activity_id}.csv"

    # Extract workout type
    workout_type = get_tcx_sport(tcx_path)
    if workout_type == "other":
        gpx_path = workout_dir / f"{safe_name}_{activity_id}.gpx"
        if gpx_path.exists():
            gpx_type = get_gpx_type(gpx_path)
            if gpx_type:
                workout_type = gpx_type

    # Extract FIT and power data if available
    if zip_path.exists():
        fit_file_path = extract_fit_from_zip(zip_path, safe_name, activity_id, workout_dir)
        if fit_file_path:
            power_series = extract_power_time_series_from_fit(fit_file_path)
            if power_series:
                save_json_data(power_series, power_json_file)
            # Clean up FIT file
            try:
                fit_file_path.unlink()
                logger.info(f"Deleted FIT file: {fit_file_path}")
            except Exception as e:
                logger.warning(f"Could not delete FIT file: {e}")
        # Clean up ZIP file
        try:
            zip_path.unlink()
            logger.info(f"Deleted ZIP file: {zip_path}")
        except Exception as e:
            logger.warning(f"Could not delete ZIP file: {e}")

    # Load athlete profile to get athlete_id (name)
    profile = load_json_data(PROFILE_PATH)
    athlete_id = profile.get("athlete_id") if profile else None

    # Parse TCX and merge power data
    try:
        start_time = extract_start_time_from_tcx(tcx_path)
        trackpoints = parse_tcx_file(tcx_path)
        # Merge power data if available
        merged = None
        if power_json_file.exists():
            power_series = load_json_data(power_json_file)
            if power_series:
                merged = merge_power_into_tcx(trackpoints, power_series)
        # Create processed data
        processed_data = {
            "athlete_id": athlete_id,
            "workout_type": workout_type,
            "activity_id": activity_id,
            "start_time": start_time,
            "data": merged if merged is not None else trackpoints,
            "csv_file": str(csv_file) if csv_file.exists() else None
        }
        return processed_data
    except Exception as e:
        logger.error(f"Failed to process activity files for {tcx_path}: {e}")
        return None


def calculate_workout_metrics(processed_data: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate TSS and duration metrics for workout.
    Args:
        processed_data: Processed workout data
        profile: Athlete profile data
    Returns:
        Updated processed data with metrics
    """
    workout_type = processed_data.get("workout_type")
    trackpoints = processed_data.get("data", [])
    tss = None
    duration_sec = None
    duration_hr = None
    if workout_type == "bike":
        ftp = profile["zones"]["bike_power"].get("ftp")
        if ftp:
            tss, duration_sec, duration_hr = calculate_tss_bike(trackpoints, ftp)
    elif workout_type == "run":
        critical_power = profile["zones"]["run_power"].get("critical_power")
        if critical_power:
            tss, duration_sec, duration_hr = calculate_tss_run(trackpoints, critical_power)
    elif workout_type == "swim":
        csv_file = processed_data.get("csv_file")
        if csv_file and Path(csv_file).exists():
            tss, duration_sec, duration_hr = calculate_tss_swim(Path(csv_file), profile)
        else:
            logger.warning(f"Swim CSV file not found for activity_id {processed_data.get('activity_id')}")
    processed_data.update({
        "tss": tss,
        "total_time": duration_sec,
        "duration_sec": duration_sec,
        "duration_hr": duration_hr
    })
    return processed_data


def process_downloaded_files(date_dir: Path):
    """
    Process all downloaded workout files in a date directory.
    
    Args:
        date_dir: Date directory containing workout files
    """
    date_dir = Path(date_dir)
    
    # Load athlete profile
    profile_path = Path("data/athlete_profile/profile.json")
    profile = load_json_data(profile_path)
    if not profile:
        logger.error("Failed to load athlete profile")
        return
    
    # Process each TCX file
    for tcx_path in date_dir.glob("*.tcx"):
        logger.info(f"Processing {tcx_path}")
        
        # Process activity files
        processed_data = process_activity_files(tcx_path, date_dir)
        if not processed_data:
            continue
        
        # Calculate metrics
        processed_data = calculate_workout_metrics(processed_data, profile)
        
        # Save processed data
        base = tcx_path.stem
        parts = base.split("_")
        activity_id = parts[-1] if parts else base
        safe_name = "_".join(parts[:-1]) if len(parts) > 1 else base
        processed_json_file = date_dir / f"{safe_name}_{activity_id}_processed.json"
        
        if save_json_data(processed_data, processed_json_file):
            logger.info(f"Successfully processed {tcx_path}")
        else:
            logger.error(f"Failed to save processed data for {tcx_path}")
