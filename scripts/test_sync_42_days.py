#!/usr/bin/env python3
"""
Test version of AIronman 42-Day Data Sync Script
This version only syncs 3 days for testing purposes.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.sync import (
    get_garmin_client, get_seed_athlete_uuid, 
    fetch_and_save_health_metrics, fetch_and_save_activities,
    process_downloaded_files, sync_processed_workouts_to_db,
    update_sync_timestamp
)
from services.preprocess import process_downloaded_files
from utils.file_utils import ensure_directory
from utils.database import get_db_conn
from utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO", log_file="logs/test_sync_42_days.log")
logger = get_logger("test_sync_42_days")

# Constants - TESTING WITH ONLY 3 DAYS
DATA_DIR = Path("data")
DAYS_TO_SYNC = 3  # Test with only 3 days


def sync_test_days_of_data():
    """
    Sync the last 3 days of workouts and health data (for testing).
    """
    logger.info(f"Starting {DAYS_TO_SYNC}-day test data sync...")
    
    # Initialize Garmin client
    try:
        garmin = get_garmin_client()
        logger.info("Garmin client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Garmin client: {e}")
        raise
    
    # Get athlete UUID
    try:
        athlete_uuid = get_seed_athlete_uuid()
        logger.info(f"Using athlete UUID: {athlete_uuid}")
    except Exception as e:
        logger.error(f"Failed to get athlete UUID: {e}")
        raise
    
    # Initialize counters
    stats = {
        'health_metrics_downloaded': 0,
        'workouts_downloaded': 0,
        'workouts_processed': 0,
        'workouts_inserted': 0,
        'errors': []
    }
    
    today = datetime.date.today()
    
    # Sync data for each day
    for delta in range(DAYS_TO_SYNC):
        date = today - timedelta(days=delta)
        date_dir = ensure_directory(DATA_DIR / str(date))
        
        logger.info(f"Processing date: {date} (day {delta + 1}/{DAYS_TO_SYNC})")
        
        try:
            # Download health metrics for each type
            for metric in ['sleep', 'hrv', 'rhr']:
                try:
                    files = fetch_and_save_health_metrics(
                        garmin, date_dir, date, None, athlete_uuid, metric
                    )
                    if files:
                        stats['health_metrics_downloaded'] += len(files)
                        logger.info(f"Downloaded {len(files)} {metric} files for {date}")
                except Exception as e:
                    error_msg = f"Failed to download {metric} for {date}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            # Download activities
            try:
                activity_files = fetch_and_save_activities(garmin, date_dir, date, date)
                if activity_files:
                    stats['workouts_downloaded'] += len(activity_files)
                    logger.info(f"Downloaded {len(activity_files)} activity files for {date}")
            except Exception as e:
                error_msg = f"Failed to download activities for {date}: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
            
            # Process and sync workouts
            workout_dir = date_dir / "workout"
            if workout_dir.exists():
                try:
                    # Process downloaded files
                    process_downloaded_files(workout_dir)
                    stats['workouts_processed'] += 1
                    logger.info(f"Processed workout files for {date}")
                    
                    # Sync to database
                    inserted = sync_processed_workouts_to_db(
                        date_dir, athlete_uuid, update_sync=True
                    )
                    if inserted:
                        stats['workouts_inserted'] += 1
                        logger.info(f"Inserted workouts into database for {date}")
                        
                except Exception as e:
                    error_msg = f"Failed to process/sync workouts for {date}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            else:
                logger.info(f"No workout directory found for {date}")
                
        except Exception as e:
            error_msg = f"Failed to process date {date}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
    
    return stats


def print_summary(stats: dict):
    """Print a summary of the sync results."""
    print("\n" + "="*60)
    print(f"{DAYS_TO_SYNC}-DAY TEST DATA SYNC SUMMARY")
    print("="*60)
    print(f"Health metrics downloaded: {stats['health_metrics_downloaded']}")
    print(f"Workout files downloaded: {stats['workouts_downloaded']}")
    print(f"Workout files processed: {stats['workouts_processed']}")
    print(f"Workouts inserted into DB: {stats['workouts_inserted']}")
    print(f"Errors encountered: {len(stats['errors'])}")
    
    if stats['errors']:
        print("\nErrors:")
        for error in stats['errors']:
            print(f"  - {error}")
    
    print("\n" + "="*60)
    print(f"✅ {DAYS_TO_SYNC}-day test sync completed!")
    print("="*60)


def main():
    """Main function to run the test sync."""
    print(f"🧪 AIronman {DAYS_TO_SYNC}-Day Test Data Sync")
    print(f"This will download the last {DAYS_TO_SYNC} days of workouts and health data")
    print("for testing the sync functionality.\n")
    
    try:
        # Run the sync
        stats = sync_test_days_of_data()
        
        # Print summary
        print_summary(stats)
        
        print("\n🎉 Test sync completed successfully!")
        print("If this works, you can run the full 42-day sync with:")
        print("  python3 scripts/sync_42_days.py")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test sync failed: {e}")
        logger.error(f"Test sync failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 