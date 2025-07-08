import os
import uuid
import json
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# DB connection from environment
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'aironman'),
    'user': os.getenv('POSTGRES_USER', 'aironman_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'aironman_pass'),
    'host': os.getenv('POSTGRES_HOST', 'db'),
    'port': os.getenv('POSTGRES_PORT', 5432),
}

PROFILE_PATH = 'data/athlete_profile/profile.json'

# Helper to parse date
parse_date = lambda s: datetime.strptime(s, '%Y-%m-%d') if s else None

def get_or_create_athlete(conn, name):
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM athlete WHERE name = %s', (name,))
        row = cur.fetchone()
        if row:
            logging.info(f"Athlete '{name}' already exists.")
            return row[0]
        athlete_id = str(uuid.uuid4())
        cur.execute('INSERT INTO athlete (id, name) VALUES (%s, %s)', (athlete_id, name))
        logging.info(f"Created athlete '{name}' with id {athlete_id}.")
        return athlete_id

def insert_athlete_profile(conn, athlete_id, profile):
    # Map JSON to DB columns
    zones = profile['zones']
    hr = zones['heart_rate']
    bp = zones['bike_power']
    rp = zones['run_power']
    pace = zones['run_pace']
    swim = zones['swim']
    test_dates = profile.get('test_dates', {})
    
    # Compose insert
    columns = [
        'athlete_id', 'json_athlete_id', 'valid_from', 'valid_to',
        'lt_heartrate',
        # Heart Rate Zones
        'hr_zone_z1_lower', 'hr_zone_z1_upper',
        'hr_zone_z2_lower', 'hr_zone_z2_upper',
        'hr_zone_zx_lower', 'hr_zone_zx_upper',
        'hr_zone_z3_lower', 'hr_zone_z3_upper',
        'hr_zone_zy_lower', 'hr_zone_zy_upper',
        'hr_zone_z4_lower', 'hr_zone_z4_upper',
        'hr_zone_z5_lower', 'hr_zone_z5_upper',
        # Bike Power Zones
        'bike_ftp_power',
        'bike_power_zone_z1_lower', 'bike_power_zone_z1_upper',
        'bike_power_zone_z2_lower', 'bike_power_zone_z2_upper',
        'bike_power_zone_zx_lower', 'bike_power_zone_zx_upper',
        'bike_power_zone_z3_lower', 'bike_power_zone_z3_upper',
        'bike_power_zone_zy_lower', 'bike_power_zone_zy_upper',
        'bike_power_zone_z4_lower', 'bike_power_zone_z4_upper',
        'bike_power_zone_z5_lower', 'bike_power_zone_z5_upper',
        # Run Power Zones
        'run_ltp_power', 'run_critical_power',
        'run_power_zone_z1_lower', 'run_power_zone_z1_upper',
        'run_power_zone_z2_lower', 'run_power_zone_z2_upper',
        'run_power_zone_zx_lower', 'run_power_zone_zx_upper',
        'run_power_zone_z3_lower', 'run_power_zone_z3_upper',
        'run_power_zone_zy_lower', 'run_power_zone_zy_upper',
        'run_power_zone_z4_lower', 'run_power_zone_z4_upper',
        'run_power_zone_z5_lower', 'run_power_zone_z5_upper',
        # Run Pace Zones
        'run_threshold_pace',
        'run_pace_zone_z1_lower', 'run_pace_zone_z1_upper',
        'run_pace_zone_z2_lower', 'run_pace_zone_z2_upper',
        'run_pace_zone_zx_lower', 'run_pace_zone_zx_upper',
        'run_pace_zone_z3_lower', 'run_pace_zone_z3_upper',
        'run_pace_zone_zy_lower', 'run_pace_zone_zy_upper',
        'run_pace_zone_z4_lower', 'run_pace_zone_z4_upper',
        'run_pace_zone_z5_lower', 'run_pace_zone_z5_upper',
        # Swim CSS & Zones
        'swim_css_pace_per_100',
        'swim_zone_z1_lower', 'swim_zone_z1_upper',
        'swim_zone_z2_lower', 'swim_zone_z2_upper',
        'swim_zone_zx_lower', 'swim_zone_zx_upper',
        'swim_zone_z3_lower', 'swim_zone_z3_upper',
        'swim_zone_zy_lower', 'swim_zone_zy_upper',
        'swim_zone_z4_lower', 'swim_zone_z4_upper',
        'swim_zone_z5_lower', 'swim_zone_z5_upper',
        # Test Dates
        'bike_ftp_test', 'run_ltp_test', 'swim_css_test'
    ]
    # Map values
    values = [
        athlete_id,
        profile.get('athlete_id'),
        parse_date(profile.get('last_updated')),
        None,  # valid_to
        hr.get('lt_hr'),
        *(hr['zones']['z1']),
        *(hr['zones']['z2']),
        *(hr['zones']['zx']),
        *(hr['zones']['z3']),
        *(hr['zones']['zy']),
        *(hr['zones']['z4']),
        *(hr['zones']['z5']),
        bp.get('ftp'),
        *(bp['zones']['z1']),
        *(bp['zones']['z2']),
        *(bp['zones']['zx']),
        *(bp['zones']['z3']),
        *(bp['zones']['zy']),
        *(bp['zones']['z4']),
        *(bp['zones']['z5']),
        rp.get('ltp'), rp.get('critical_power'),
        *(rp['zones']['z1']),
        *(rp['zones']['z2']),
        *(rp['zones']['zx']),
        *(rp['zones']['z3']),
        *(rp['zones']['zy']),
        *(rp['zones']['z4']),
        *(rp['zones']['z5']),
        # Run pace: convert mm:ss to int seconds for DB
        _pace_to_seconds(pace.get('threshold_pace_per_km')),
        *[_pace_to_seconds(x) for x in pace['zones']['z1']],
        *[_pace_to_seconds(x) for x in pace['zones']['z2']],
        *[_pace_to_seconds(x) for x in pace['zones']['zx']],
        *[_pace_to_seconds(x) for x in pace['zones']['z3']],
        *[_pace_to_seconds(x) for x in pace['zones']['zy']],
        *[_pace_to_seconds(x) for x in pace['zones']['z4']],
        *[_pace_to_seconds(x) for x in pace['zones']['z5']],
        _pace_to_seconds(swim.get('css_pace_per_100m')),
        *[_pace_to_seconds(x) for x in swim['zones']['z1']],
        *[_pace_to_seconds(x) for x in swim['zones']['z2']],
        *[_pace_to_seconds(x) for x in swim['zones']['zx']],
        *[_pace_to_seconds(x) for x in swim['zones']['z3']],
        *[_pace_to_seconds(x) for x in swim['zones']['zy']],
        *[_pace_to_seconds(x) for x in swim['zones']['z4']],
        *[_pace_to_seconds(x) for x in swim['zones']['z5']],
        # Test Dates
        parse_date(test_dates.get('bike_ftp_test')),
        parse_date(test_dates.get('run_ltp_test')),
        parse_date(test_dates.get('swim_css_test'))
    ]
    placeholders = ','.join(['%s'] * len(values))
    colnames = ','.join(columns)
    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO athlete_profile ({colnames})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """, values)
    logging.info("Inserted athlete profile for athlete_id %s", athlete_id)

def _pace_to_seconds(pace_str):
    if not pace_str:
        return None
    try:
        m, s = pace_str.split(':')
        return int(m) * 60 + int(s)
    except Exception:
        return None

def main():
    try:
        with open(PROFILE_PATH, 'r') as f:
            profile = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load profile.json: {e}")
        return 1
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
    except Exception as e:
        logging.error(f"Failed to connect to DB: {e}")
        return 1
    try:
        athlete_id = get_or_create_athlete(conn, 'Jan')
        insert_athlete_profile(conn, athlete_id, profile)
        # Insert initial sync rows for each data type
        with conn.cursor() as cur:
            for data_type in ['sleep', 'hrv', 'rhr', 'workout']:
                cur.execute('''
                    INSERT INTO sync (athlete_id, data_type, last_synced_timestamp)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (athlete_id, data_type) DO NOTHING
                ''', (athlete_id, data_type, None))
    except Exception as e:
        logging.error(f"Failed to insert athlete/profile: {e}")
        return 1
    finally:
        conn.close()
    logging.info("Seeding complete.")
    return 0

if __name__ == "__main__":
    logging.info("Starting database seeding...")
    try:
        result = main()
        if result == 0:
            logging.info("Seeding complete.")
            sys.exit(0)
        else:
            logging.error("Seeding failed with exit code %s", result)
            sys.exit(result)
    except Exception as e:
        logging.exception(f"Unhandled exception during seeding: {e}")
        sys.exit(1) 