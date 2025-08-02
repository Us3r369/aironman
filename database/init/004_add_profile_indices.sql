-- 004_add_profile_indices.sql
-- Adds performance index and unique constraint for active profiles

-- Speed up active profile look-ups
CREATE INDEX IF NOT EXISTS idx_athlete_profile_active
    ON athlete_profile (json_athlete_id)
    WHERE valid_to IS NULL;

-- Ensure at most one active profile per athlete
CREATE UNIQUE INDEX IF NOT EXISTS uq_athlete_profile_one_active
    ON athlete_profile (json_athlete_id)
    WHERE valid_to IS NULL; 