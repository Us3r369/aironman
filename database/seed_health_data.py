#!/usr/bin/env python3
"""
Seed sample health data for testing the health analysis features.
"""

import os
import uuid
import json
import logging
import psycopg2
from datetime import datetime, timedelta
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# DB connection from environment
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'aironman_db'),
    'user': os.getenv('POSTGRES_USER', 'user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    'host': os.getenv('POSTGRES_HOST', 'db'),
    'port': os.getenv('POSTGRES_PORT', 5432),
}

def get_athlete_uuid(conn, athlete_name):
    """Get athlete UUID by name."""
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM athlete WHERE name = %s', (athlete_name,))
        row = cur.fetchone()
        if row:
            return row[0]
        else:
            logging.error(f"Athlete '{athlete_name}' not found")
            return None

def seed_health_data():
    """Seed sample health data for testing."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Get athlete UUID
        athlete_uuid = get_athlete_uuid(conn, 'Jan')
        if not athlete_uuid:
            logging.error("Athlete not found, cannot seed health data")
            return
        
        # Generate sample data for the last 30 days
        base_date = datetime.now() - timedelta(days=30)
        
        with conn.cursor() as cur:
            # Clear existing data for this athlete
            cur.execute('DELETE FROM sleep WHERE athlete_id = %s', (athlete_uuid,))
            cur.execute('DELETE FROM hrv WHERE athlete_id = %s', (athlete_uuid,))
            cur.execute('DELETE FROM rhr WHERE athlete_id = %s', (athlete_uuid,))
            
            # Generate sample data
            for i in range(30):
                current_date = base_date + timedelta(days=i)
                
                # Sleep data (quality score 0-100)
                sleep_quality = 70 + (i % 7) * 5  # Varies by day of week
                cur.execute('''
                    INSERT INTO sleep (id, athlete_id, timestamp, json_file, synced_at)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()),
                    athlete_uuid,
                    current_date.date(),
                    json.dumps({'sleepQuality': sleep_quality}),
                    datetime.now()
                ))
                
                # HRV data (ms)
                hrv_value = 95 + (i % 5) * 2  # Varies slightly
                cur.execute('''
                    INSERT INTO hrv (id, athlete_id, timestamp, json_file, synced_at)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()),
                    athlete_uuid,
                    current_date.date(),
                    json.dumps({'hrv': hrv_value}),
                    datetime.now()
                ))
                
                # RHR data (bpm)
                rhr_value = 38 + (i % 3)  # Varies slightly
                cur.execute('''
                    INSERT INTO rhr (id, athlete_id, timestamp, json_file, synced_at)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()),
                    athlete_uuid,
                    current_date.date(),
                    json.dumps({'restingHeartRate': rhr_value}),
                    datetime.now()
                ))
            
            conn.commit()
            logging.info("Successfully seeded sample health data")
            
    except Exception as e:
        logging.error(f"Error seeding health data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_health_data() 