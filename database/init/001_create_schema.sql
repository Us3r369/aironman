-- 001_create_schema.sql
-- Endurance Training Database Schema (PostgreSQL)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS athlete (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS athlete_profile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    json_athlete_id TEXT,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    -- Heart Rate Zones
    lt_heartrate INTEGER,
    hr_zone_z1_lower INTEGER, hr_zone_z1_upper INTEGER,
    hr_zone_z2_lower INTEGER, hr_zone_z2_upper INTEGER,
    hr_zone_zx_lower INTEGER, hr_zone_zx_upper INTEGER,
    hr_zone_z3_lower INTEGER, hr_zone_z3_upper INTEGER,
    hr_zone_zy_lower INTEGER, hr_zone_zy_upper INTEGER,
    hr_zone_z4_lower INTEGER, hr_zone_z4_upper INTEGER,
    hr_zone_z5_lower INTEGER, hr_zone_z5_upper INTEGER,
    -- Bike Power Zones
    bike_ftp_power INTEGER,
    bike_power_zone_z1_lower INTEGER, bike_power_zone_z1_upper INTEGER,
    bike_power_zone_z2_lower INTEGER, bike_power_zone_z2_upper INTEGER,
    bike_power_zone_zx_lower INTEGER, bike_power_zone_zx_upper INTEGER,
    bike_power_zone_z3_lower INTEGER, bike_power_zone_z3_upper INTEGER,
    bike_power_zone_zy_lower INTEGER, bike_power_zone_zy_upper INTEGER,
    bike_power_zone_z4_lower INTEGER, bike_power_zone_z4_upper INTEGER,
    bike_power_zone_z5_lower INTEGER, bike_power_zone_z5_upper INTEGER,
    -- Run Power Zones
    run_ltp_power INTEGER,
    run_critical_power INTEGER,
    run_power_zone_z1_lower INTEGER, run_power_zone_z1_upper INTEGER,
    run_power_zone_z2_lower INTEGER, run_power_zone_z2_upper INTEGER,
    run_power_zone_zx_lower INTEGER, run_power_zone_zx_upper INTEGER,
    run_power_zone_z3_lower INTEGER, run_power_zone_z3_upper INTEGER,
    run_power_zone_zy_lower INTEGER, run_power_zone_zy_upper INTEGER,
    run_power_zone_z4_lower INTEGER, run_power_zone_z4_upper INTEGER,
    run_power_zone_z5_lower INTEGER, run_power_zone_z5_upper INTEGER,
    -- Run Pace Zones
    run_threshold_pace INTEGER,
    run_pace_zone_z1_lower INTEGER, run_pace_zone_z1_upper INTEGER,
    run_pace_zone_z2_lower INTEGER, run_pace_zone_z2_upper INTEGER,
    run_pace_zone_zx_lower INTEGER, run_pace_zone_zx_upper INTEGER,
    run_pace_zone_z3_lower INTEGER, run_pace_zone_z3_upper INTEGER,
    run_pace_zone_zy_lower INTEGER, run_pace_zone_zy_upper INTEGER,
    run_pace_zone_z4_lower INTEGER, run_pace_zone_z4_upper INTEGER,
    run_pace_zone_z5_lower INTEGER, run_pace_zone_z5_upper INTEGER,
    -- Swim CSS & Zones
    swim_css_pace_per_100 INTEGER,
    swim_zone_z1_lower INTEGER, swim_zone_z1_upper INTEGER,
    swim_zone_z2_lower INTEGER, swim_zone_z2_upper INTEGER,
    swim_zone_zx_lower INTEGER, swim_zone_zx_upper INTEGER,
    swim_zone_z3_lower INTEGER, swim_zone_z3_upper INTEGER,
    swim_zone_zy_lower INTEGER, swim_zone_zy_upper INTEGER,
    swim_zone_z4_lower INTEGER, swim_zone_z4_upper INTEGER,
    swim_zone_z5_lower INTEGER, swim_zone_z5_upper INTEGER,
    -- Test Dates
    bike_ftp_test DATE,
    run_ltp_test DATE,
    swim_css_test DATE
);

CREATE TABLE IF NOT EXISTS sleep (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    timestamp DATE NOT NULL,
    json_file JSONB NOT NULL,
    synced_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rhr (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    timestamp DATE NOT NULL,
    json_file JSONB NOT NULL,
    synced_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hrv (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    timestamp DATE NOT NULL,
    json_file JSONB NOT NULL,
    synced_at TIMESTAMP DEFAULT now()
);

CREATE TYPE workout_type_enum AS ENUM ('swim', 'bike', 'run', 'strength', 'other');

CREATE TABLE IF NOT EXISTS workout (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    workout_type workout_type_enum NOT NULL,
    json_file JSONB,
    csv_file TEXT,
    tss FLOAT,
    synced_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS training_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    ctl FLOAT,
    atl FLOAT,
    tsb FLOAT
);

CREATE TABLE IF NOT EXISTS sync (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    data_type VARCHAR(32) NOT NULL,
    last_synced_timestamp TIMESTAMP,
    UNIQUE (athlete_id, data_type)
); 