-- 003_create_workout_zones.sql
-- Create workout_zones table for storing zone analysis results

CREATE TABLE IF NOT EXISTS workout_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id UUID NOT NULL REFERENCES workout(id) ON DELETE CASCADE,
    athlete_id UUID NOT NULL REFERENCES athlete(id) ON DELETE CASCADE,
    
    -- Heart Rate Zone Times (in minutes)
    hr_z1_minutes DECIMAL(8,2) DEFAULT 0,
    hr_z2_minutes DECIMAL(8,2) DEFAULT 0,
    hr_zx_minutes DECIMAL(8,2) DEFAULT 0,
    hr_z3_minutes DECIMAL(8,2) DEFAULT 0,
    hr_zy_minutes DECIMAL(8,2) DEFAULT 0,
    hr_z4_minutes DECIMAL(8,2) DEFAULT 0,
    hr_z5_minutes DECIMAL(8,2) DEFAULT 0,
    
    -- Power Zone Times (in minutes) - for bike and run only
    power_z1_minutes DECIMAL(8,2) DEFAULT 0,
    power_z2_minutes DECIMAL(8,2) DEFAULT 0,
    power_zx_minutes DECIMAL(8,2) DEFAULT 0,
    power_z3_minutes DECIMAL(8,2) DEFAULT 0,
    power_zy_minutes DECIMAL(8,2) DEFAULT 0,
    power_z4_minutes DECIMAL(8,2) DEFAULT 0,
    power_z5_minutes DECIMAL(8,2) DEFAULT 0,
    
    -- Total duration and availability flags
    total_duration_minutes DECIMAL(8,2) DEFAULT 0,
    hr_zones_available BOOLEAN DEFAULT FALSE,
    power_zones_available BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(workout_id),
    CHECK (total_duration_minutes >= 0),
    CHECK (hr_z1_minutes >= 0),
    CHECK (hr_z2_minutes >= 0),
    CHECK (hr_zx_minutes >= 0),
    CHECK (hr_z3_minutes >= 0),
    CHECK (hr_zy_minutes >= 0),
    CHECK (hr_z4_minutes >= 0),
    CHECK (hr_z5_minutes >= 0),
    CHECK (power_z1_minutes >= 0),
    CHECK (power_z2_minutes >= 0),
    CHECK (power_zx_minutes >= 0),
    CHECK (power_z3_minutes >= 0),
    CHECK (power_zy_minutes >= 0),
    CHECK (power_z4_minutes >= 0),
    CHECK (power_z5_minutes >= 0)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_workout_zones_workout_id ON workout_zones(workout_id);
CREATE INDEX IF NOT EXISTS idx_workout_zones_athlete_id ON workout_zones(athlete_id);
CREATE INDEX IF NOT EXISTS idx_workout_zones_created_at ON workout_zones(created_at);

-- Add comments for documentation
COMMENT ON TABLE workout_zones IS 'Zone analysis results for each workout, storing time spent in each heart rate and power zone';
COMMENT ON COLUMN workout_zones.hr_z1_minutes IS 'Time spent in heart rate zone 1 (minutes)';
COMMENT ON COLUMN workout_zones.hr_z2_minutes IS 'Time spent in heart rate zone 2 (minutes)';
COMMENT ON COLUMN workout_zones.hr_zx_minutes IS 'Time spent in heart rate zone x (minutes)';
COMMENT ON COLUMN workout_zones.hr_z3_minutes IS 'Time spent in heart rate zone 3 (minutes)';
COMMENT ON COLUMN workout_zones.hr_zy_minutes IS 'Time spent in heart rate zone y (minutes)';
COMMENT ON COLUMN workout_zones.hr_z4_minutes IS 'Time spent in heart rate zone 4 (minutes)';
COMMENT ON COLUMN workout_zones.hr_z5_minutes IS 'Time spent in heart rate zone 5 (minutes)';
COMMENT ON COLUMN workout_zones.power_z1_minutes IS 'Time spent in power zone 1 (minutes)';
COMMENT ON COLUMN workout_zones.power_z2_minutes IS 'Time spent in power zone 2 (minutes)';
COMMENT ON COLUMN workout_zones.power_zx_minutes IS 'Time spent in power zone x (minutes)';
COMMENT ON COLUMN workout_zones.power_z3_minutes IS 'Time spent in power zone 3 (minutes)';
COMMENT ON COLUMN workout_zones.power_zy_minutes IS 'Time spent in power zone y (minutes)';
COMMENT ON COLUMN workout_zones.power_z4_minutes IS 'Time spent in power zone 4 (minutes)';
COMMENT ON COLUMN workout_zones.power_z5_minutes IS 'Time spent in power zone 5 (minutes)';
COMMENT ON COLUMN workout_zones.total_duration_minutes IS 'Total workout duration in minutes';
COMMENT ON COLUMN workout_zones.hr_zones_available IS 'Whether heart rate data was available for zone analysis';
COMMENT ON COLUMN workout_zones.power_zones_available IS 'Whether power data was available for zone analysis'; 