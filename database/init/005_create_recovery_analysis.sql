-- 005_create_recovery_analysis.sql
-- Creates table for storing daily recovery analysis from intelligent agent

-- Create daily_recovery_analysis table
CREATE TABLE IF NOT EXISTS daily_recovery_analysis (
    id SERIAL PRIMARY KEY,
    athlete_id UUID NOT NULL REFERENCES athlete(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    version INTEGER NOT NULL DEFAULT 1, -- Version number for multiple analyses per day
    status VARCHAR(10) NOT NULL CHECK (status IN ('good', 'medium', 'bad')),
    detailed_reasoning TEXT NOT NULL,
    agent_analysis JSONB, -- Store full agent response
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(athlete_id, analysis_date, version) -- Allow multiple versions per day
);

-- Add indices for performance
CREATE INDEX IF NOT EXISTS idx_daily_recovery_analysis_athlete_date
    ON daily_recovery_analysis (athlete_id, analysis_date);

CREATE INDEX IF NOT EXISTS idx_daily_recovery_analysis_date
    ON daily_recovery_analysis (analysis_date);

CREATE INDEX IF NOT EXISTS idx_daily_recovery_analysis_status
    ON daily_recovery_analysis (status);

CREATE INDEX IF NOT EXISTS idx_daily_recovery_analysis_latest
    ON daily_recovery_analysis (athlete_id, analysis_date, version DESC);

-- Add comment for documentation
COMMENT ON TABLE daily_recovery_analysis IS 'Stores daily recovery analysis results from intelligent agent';
COMMENT ON COLUMN daily_recovery_analysis.status IS 'Recovery status: good, medium, or bad';
COMMENT ON COLUMN daily_recovery_analysis.detailed_reasoning IS 'Detailed explanation from agent analysis';
COMMENT ON COLUMN daily_recovery_analysis.agent_analysis IS 'Full JSON response from CrewAI agent';
COMMENT ON COLUMN daily_recovery_analysis.version IS 'Version number for multiple analyses per day'; 