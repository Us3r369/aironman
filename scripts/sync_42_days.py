#!/usr/bin/env python3
"""
AIronman 42-Day Data Sync Script

This script pulls the last 42 days of workouts and health data from Garmin Connect
to establish the foundation for CTL (Chronic Training Load) calculation.

Usage:
    python scripts/sync_42_days.py

Requirements:
    - Garmin Connect authentication tokens in ~/.garminconnect/
    - Database connection configured
    - All dependencies installed
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
setup_logging(log_level="INFO", log_file="logs/sync_42_days.log")
logger = get_logger("sync_42_days")

# Constants
DATA_DIR = Path("data")
DAYS_TO_SYNC = 42


def sync_42_days_of_data():
    """
    Sync the last 42 days of workouts and health data.
    
    This function:
    1. Downloads health metrics (sleep, HRV, RHR) for the last 42 days
    2. Downloads workout activities for the last 42 days
    3. Processes workout files and calculates TSS
    4. Stores all data in the database
    5. Updates sync timestamps
    
    Returns:
        dict: Summary of sync results
    """
    logger.info(f"Starting 42-day data sync...")
    
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
    
    # Update final sync timestamps
    try:
        latest_date = today - timedelta(days=DAYS_TO_SYNC - 1)
        for metric in ['sleep', 'hrv', 'rhr']:
            update_sync_timestamp(athlete_uuid, metric, datetime.combine(latest_date, datetime.min.time()))
        logger.info("Updated sync timestamps for all data types")
    except Exception as e:
        error_msg = f"Failed to update sync timestamps: {e}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
    
    return stats


def print_summary(stats: dict):
    """Print a summary of the sync results."""
    print("\n" + "="*60)
    print("42-DAY DATA SYNC SUMMARY")
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
    print("✅ 42-day data sync completed!")
    print("This provides the foundation for CTL calculation.")
    print("="*60)


def verify_data_integrity():
    """
    Verify that we have sufficient data for CTL calculation.
    
    Returns:
        bool: True if we have enough data, False otherwise
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Check how many workouts we have in the last 42 days
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM workout 
                    WHERE timestamp >= NOW() - INTERVAL '42 days'
                """)
                workout_count = cur.fetchone()[0]
                
                # Check health metrics
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM sleep 
                    WHERE timestamp >= NOW() - INTERVAL '42 days'
                """)
                sleep_count = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM hrv 
                    WHERE timestamp >= NOW() - INTERVAL '42 days'
                """)
                hrv_count = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM rhr 
                    WHERE timestamp >= NOW() - INTERVAL '42 days'
                """)
                rhr_count = cur.fetchone()[0]
                
                print(f"\nData Integrity Check:")
                print(f"  Workouts (last 42 days): {workout_count}")
                print(f"  Sleep records: {sleep_count}")
                print(f"  HRV records: {hrv_count}")
                print(f"  RHR records: {rhr_count}")
                
                # Recommend minimum thresholds
                if workout_count >= 10:
                    print("✅ Sufficient workout data for CTL calculation")
                else:
                    print("⚠️  Limited workout data - CTL may be less accurate")
                
                if sleep_count >= 20 and hrv_count >= 20:
                    print("✅ Sufficient health data for recovery analysis")
                else:
                    print("⚠️  Limited health data - recovery analysis may be limited")
                
                return True
                
    except Exception as e:
        logger.error(f"Failed to verify data integrity: {e}")
        return False


def main():
    """Main function to run the 42-day sync."""
    print("🚀 AIronman 42-Day Data Sync")
    print("This will download the last 42 days of workouts and health data")
    print("to establish the foundation for CTL calculation.\n")
    
    try:
        # Run the sync
        stats = sync_42_days_of_data()
        
        # Print summary
        print_summary(stats)
        
        # Verify data integrity
        verify_data_integrity()
        
        print("\n🎉 Sync completed successfully!")
        print("You can now implement CTL calculation with this data foundation.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        logger.error(f"Sync failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 