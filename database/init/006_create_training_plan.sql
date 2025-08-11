-- 006_create_training_plan.sql
-- Tables for generated training plans and individual sessions

CREATE TABLE IF NOT EXISTS training_plan (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    race_date DATE NOT NULL,
    race_type TEXT NOT NULL,
    max_workouts_per_week INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS training_session (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES training_plan(id) ON DELETE CASCADE,
    athlete_id UUID REFERENCES athlete(id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    workout_type TEXT NOT NULL,
    description TEXT,
    phase TEXT,
    planned_tss FLOAT
);
