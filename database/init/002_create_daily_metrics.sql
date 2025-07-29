-- Create daily_metrics table for PMC calculations
CREATE TABLE IF NOT EXISTS daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athlete(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    ctl DECIMAL(5,2),
    atl DECIMAL(5,2),
    tsb DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(athlete_id, date)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_daily_metrics_athlete_date ON daily_metrics(athlete_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);

-- Add comment for documentation
COMMENT ON TABLE daily_metrics IS 'Daily Performance Management Chart metrics (CTL, ATL, TSB) for each athlete';
COMMENT ON COLUMN daily_metrics.ctl IS 'Chronic Training Load - 42-day exponentially weighted average of TSS';
COMMENT ON COLUMN daily_metrics.atl IS 'Acute Training Load - 7-day exponentially weighted average of TSS';
COMMENT ON COLUMN daily_metrics.tsb IS 'Training Stress Balance - CTL - ATL (fitness - fatigue)'; 