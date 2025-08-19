from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import threading
import time
import psycopg2
import os
from datetime import datetime, timedelta
from services.sync import sync_last_n_days, sync_since_last_entry
import json
from pathlib import Path
import datetime as dt
import math

# Import new logging and exception handling
from utils.logging_config import setup_logging, get_logger, get_correlation_id, set_correlation_id, ErrorContext
from utils.exceptions import (
    AIronmanException, DatabaseException, ProfileNotFoundException, 
    ProfileValidationException, SyncException, ValidationException
)
from utils.database import get_db_conn, get_athlete_uuid
from services.pmc_metrics import pmc_metrics
from agents.training_plan_agent import TrainingPlanAgent

# Setup logging
setup_logging(log_level="INFO", log_file="logs/app.log")
logger = get_logger("api")

app = FastAPI(
    title="AIronman Coaching App",
    description="API for AIronman coaching application",
    version="1.0.0"
)

# CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ZoneRange(BaseModel):
    z1: List[Any]
    z2: List[Any]
    zx: List[Any]
    z3: List[Any]
    zy: List[Any]
    z4: List[Any]
    z5: List[Any]

class HeartRateZone(BaseModel):
    lt_hr: int
    zones: ZoneRange

class BikePowerZone(BaseModel):
    ftp: int
    zones: ZoneRange

class RunPowerZone(BaseModel):
    ltp: int
    critical_power: int
    zones: ZoneRange

class RunPaceZone(BaseModel):
    threshold_pace_per_km: str
    zones: ZoneRange

class SwimZone(BaseModel):
    css_pace_per_100m: str
    zones: ZoneRange

class Zones(BaseModel):
    heart_rate: HeartRateZone
    bike_power: BikePowerZone
    run_power: RunPowerZone
    run_pace: RunPaceZone
    swim: SwimZone

class TestDates(BaseModel):
    bike_ftp_test: Optional[str]
    run_ltp_test: Optional[str]
    swim_css_test: Optional[str]

class AthleteProfile(BaseModel):
    athlete_id: str
    last_updated: str
    zones: Zones
    test_dates: TestDates

# --- Error Response Models ---
class ErrorResponse(BaseModel):
    error: str
    message: str
    correlation_id: str
    timestamp: str

# --- Middleware for correlation ID ---
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests."""
    corr_id = get_correlation_id()
    set_correlation_id(corr_id)
    
    with ErrorContext("HTTP Request", logger, 
                     method=request.method, 
                     path=request.url.path,
                     correlation_id=corr_id):
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response

# --- Exception Handlers ---
@app.exception_handler(AIronmanException)
async def aironman_exception_handler(request: Request, exc: AIronmanException):
    """Handle AIronman-specific exceptions."""
    logger.error(f"AIronman exception: {exc.message}", 
                extra={'correlation_id': get_correlation_id(), 'context': exc.context})
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=type(exc).__name__,
            message=exc.message,
            correlation_id=get_correlation_id(),
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )

@app.exception_handler(ProfileNotFoundException)
async def profile_not_found_handler(request: Request, exc: ProfileNotFoundException):
    """Handle profile not found exceptions."""
    logger.warning(f"Profile not found: {exc.message}", 
                  extra={'correlation_id': get_correlation_id(), 'context': exc.context})
    
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="ProfileNotFound",
            message=exc.message,
            correlation_id=get_correlation_id(),
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions."""
    logger.warning(f"Validation error: {exc.message}", 
                  extra={'correlation_id': get_correlation_id(), 'context': exc.context})
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="ValidationError",
            message=exc.message,
            correlation_id=get_correlation_id(),
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )

@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    """Handle database exceptions."""
    logger.error(f"Database error: {exc.message}", 
                extra={'correlation_id': get_correlation_id(), 'context': exc.context})
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="DatabaseError",
            message="An internal database error occurred",
            correlation_id=get_correlation_id(),
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", 
                extra={'correlation_id': get_correlation_id()}, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred",
            correlation_id=get_correlation_id(),
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )

@app.on_event("startup")
def startup_event():
    """Application startup event."""
    with ErrorContext("Application Startup", logger):
        # Run initial sync in a background thread
        threading.Thread(target=sync_last_n_days, daemon=True).start()
        # Start periodic hourly sync in a background thread
        threading.Thread(target=periodic_sync, daemon=True).start()
        logger.info("Application started successfully")

def periodic_sync():
    """Periodic sync function with error handling."""
    while True:
        try:
            with ErrorContext("Periodic Sync", logger):
                sync_since_last_entry()
        except Exception as e:
            logger.error(f"Periodic sync failed: {e}", exc_info=True)
        time.sleep(3600)  # Wait for 1 hour

@app.post("/sync")
def sync_endpoint(background_tasks: BackgroundTasks):
    """Sync endpoint with error handling."""
    with ErrorContext("Manual Sync Request", logger):
        background_tasks.add_task(sync_since_last_entry)
        logger.info("Sync started in background")
        return {"status": "Sync started in background"}

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "AIronman Coaching App is running!"}

# --- GET /api/profile ---
@app.get("/api/profile", response_model=AthleteProfile)
def get_profile():
    print("get_profile called!")
    with get_db_conn() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT json_athlete_id, valid_from, 
                           lt_heartrate,
                           hr_zone_z1_lower, hr_zone_z1_upper,
                           hr_zone_z2_lower, hr_zone_z2_upper,
                           hr_zone_zx_lower, hr_zone_zx_upper,
                           hr_zone_z3_lower, hr_zone_z3_upper,
                           hr_zone_zy_lower, hr_zone_zy_upper,
                           hr_zone_z4_lower, hr_zone_z4_upper,
                           hr_zone_z5_lower, hr_zone_z5_upper,
                           bike_ftp_power,
                           bike_power_zone_z1_lower, bike_power_zone_z1_upper,
                           bike_power_zone_z2_lower, bike_power_zone_z2_upper,
                           bike_power_zone_zx_lower, bike_power_zone_zx_upper,
                           bike_power_zone_z3_lower, bike_power_zone_z3_upper,
                           bike_power_zone_zy_lower, bike_power_zone_zy_upper,
                           bike_power_zone_z4_lower, bike_power_zone_z4_upper,
                           bike_power_zone_z5_lower, bike_power_zone_z5_upper,
                           run_ltp_power, run_critical_power,
                           run_power_zone_z1_lower, run_power_zone_z1_upper,
                           run_power_zone_z2_lower, run_power_zone_z2_upper,
                           run_power_zone_zx_lower, run_power_zone_zx_upper,
                           run_power_zone_z3_lower, run_power_zone_z3_upper,
                           run_power_zone_zy_lower, run_power_zone_zy_upper,
                           run_power_zone_z4_lower, run_power_zone_z4_upper,
                           run_power_zone_z5_lower, run_power_zone_z5_upper,
                           run_threshold_pace,
                           run_pace_zone_z1_lower, run_pace_zone_z1_upper,
                           run_pace_zone_z2_lower, run_pace_zone_z2_upper,
                           run_pace_zone_zx_lower, run_pace_zone_zx_upper,
                           run_pace_zone_z3_lower, run_pace_zone_z3_upper,
                           run_pace_zone_zy_lower, run_pace_zone_zy_upper,
                           run_pace_zone_z4_lower, run_pace_zone_z4_upper,
                           run_pace_zone_z5_lower, run_pace_zone_z5_upper,
                           swim_css_pace_per_100,
                           swim_zone_z1_lower, swim_zone_z1_upper,
                           swim_zone_z2_lower, swim_zone_z2_upper,
                           swim_zone_zx_lower, swim_zone_zx_upper,
                           swim_zone_z3_lower, swim_zone_z3_upper,
                           swim_zone_zy_lower, swim_zone_zy_upper,
                           swim_zone_z4_lower, swim_zone_z4_upper,
                           swim_zone_z5_lower, swim_zone_z5_upper,
                           bike_ftp_test, run_ltp_test, swim_css_test
                    FROM athlete_profile
                    ORDER BY valid_from DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
                if not row:
                    raise ProfileNotFoundException("Profile not found")
                def to_str(val):
                    if isinstance(val, dt.date):
                        return val.strftime('%Y-%m-%d')
                    elif val is not None:
                        return str(val)
                    return None
                # Always convert test_dates fields to string
                bike_ftp_test = to_str(row[78])
                run_ltp_test = to_str(row[79])
                swim_css_test = to_str(row[80])
                profile = {
                    "athlete_id": row[0],
                    "last_updated": to_str(row[1]),
                    "zones": {
                        "heart_rate": {
                            "lt_hr": row[2],
                            "zones": {
                                "z1": [row[3], row[4]],
                                "z2": [row[5], row[6]],
                                "zx": [row[7], row[8]],
                                "z3": [row[9], row[10]],
                                "zy": [row[11], row[12]],
                                "z4": [row[13], row[14]],
                                "z5": [row[15], row[16]],
                            },
                        },
                        "bike_power": {
                            "ftp": row[17],
                            "zones": {
                                "z1": [row[18], row[19]],
                                "z2": [row[20], row[21]],
                                "zx": [row[22], row[23]],
                                "z3": [row[24], row[25]],
                                "zy": [row[26], row[27]],
                                "z4": [row[28], row[29]],
                                "z5": [row[30], row[31]],
                            },
                        },
                        "run_power": {
                            "ltp": row[32],
                            "critical_power": row[33],
                            "zones": {
                                "z1": [row[34], row[35]],
                                "z2": [row[36], row[37]],
                                "zx": [row[38], row[39]],
                                "z3": [row[40], row[41]],
                                "zy": [row[42], row[43]],
                                "z4": [row[44], row[45]],
                                "z5": [row[46], row[47]],
                            },
                        },
                        "run_pace": {
                            "threshold_pace_per_km": seconds_to_pace(row[48]),
                            "zones": {
                                "z1": [seconds_to_pace(row[49]), seconds_to_pace(row[50])],
                                "z2": [seconds_to_pace(row[51]), seconds_to_pace(row[52])],
                                "zx": [seconds_to_pace(row[53]), seconds_to_pace(row[54])],
                                "z3": [seconds_to_pace(row[55]), seconds_to_pace(row[56])],
                                "zy": [seconds_to_pace(row[57]), seconds_to_pace(row[58])],
                                "z4": [seconds_to_pace(row[59]), seconds_to_pace(row[60])],
                                "z5": [seconds_to_pace(row[61]), seconds_to_pace(row[62])],
                            },
                        },
                        "swim": {
                            "css_pace_per_100m": seconds_to_pace(row[63]),
                            "zones": {
                                "z1": [seconds_to_pace(row[64]), seconds_to_pace(row[65])],
                                "z2": [seconds_to_pace(row[66]), seconds_to_pace(row[67])],
                                "zx": [seconds_to_pace(row[68]), seconds_to_pace(row[69])],
                                "z3": [seconds_to_pace(row[70]), seconds_to_pace(row[71])],
                                "zy": [seconds_to_pace(row[72]), seconds_to_pace(row[73])],
                                "z4": [seconds_to_pace(row[74]), seconds_to_pace(row[75])],
                                "z5": [seconds_to_pace(row[76]), seconds_to_pace(row[77])],
                            },
                        },
                    },
                    "test_dates": {
                        "bike_ftp_test": bike_ftp_test,
                        "run_ltp_test": run_ltp_test,
                        "swim_css_test": swim_css_test,
                    },
                }
                return profile
        except Exception as e:
            if isinstance(e, ProfileNotFoundException):
                raise
            raise DatabaseException(f"Failed to fetch profile: {e}")

def pace_to_seconds(pace: str) -> int:
    """Convert pace string to seconds."""
    try:
        parts = pace.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(pace)
    except:
        return 0

def seconds_to_pace(seconds: int) -> str:
    """Convert seconds to pace string."""
    if seconds <= 0:
        return "0:00"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"

@app.put("/api/profile")
def update_profile(profile: AthleteProfile):
    """Update athlete profile with error handling."""
    with ErrorContext("Update Profile", logger, athlete_id=profile.athlete_id):
        with get_db_conn() as conn:
            try:
                with conn.cursor() as cur:
                    z = profile.zones
                    now = datetime.now()
                    # Resolve athlete UUID – create athlete row if it does not exist
                    try:
                        athlete_uuid = get_athlete_uuid(profile.athlete_id)
                    except ValueError:
                        # Insert new athlete row and fetch UUID
                        cur.execute("INSERT INTO athlete (name) VALUES (%s) RETURNING id", (profile.athlete_id,))
                        athlete_uuid = cur.fetchone()[0]

                    columns = [
                        'athlete_id', 'json_athlete_id', 'valid_from', 'valid_to',
                        'lt_heartrate',
                        'hr_zone_z1_lower', 'hr_zone_z1_upper',
                        'hr_zone_z2_lower', 'hr_zone_z2_upper',
                        'hr_zone_zx_lower', 'hr_zone_zx_upper',
                        'hr_zone_z3_lower', 'hr_zone_z3_upper',
                        'hr_zone_zy_lower', 'hr_zone_zy_upper',
                        'hr_zone_z4_lower', 'hr_zone_z4_upper',
                        'hr_zone_z5_lower', 'hr_zone_z5_upper',
                        'bike_ftp_power',
                        'bike_power_zone_z1_lower', 'bike_power_zone_z1_upper',
                        'bike_power_zone_z2_lower', 'bike_power_zone_z2_upper',
                        'bike_power_zone_zx_lower', 'bike_power_zone_zx_upper',
                        'bike_power_zone_z3_lower', 'bike_power_zone_z3_upper',
                        'bike_power_zone_zy_lower', 'bike_power_zone_zy_upper',
                        'bike_power_zone_z4_lower', 'bike_power_zone_z4_upper',
                        'bike_power_zone_z5_lower', 'bike_power_zone_z5_upper',
                        'run_ltp_power', 'run_critical_power',
                        'run_power_zone_z1_lower', 'run_power_zone_z1_upper',
                        'run_power_zone_z2_lower', 'run_power_zone_z2_upper',
                        'run_power_zone_zx_lower', 'run_power_zone_zx_upper',
                        'run_power_zone_z3_lower', 'run_power_zone_z3_upper',
                        'run_power_zone_zy_lower', 'run_power_zone_zy_upper',
                        'run_power_zone_z4_lower', 'run_power_zone_z4_upper',
                        'run_power_zone_z5_lower', 'run_power_zone_z5_upper',
                        'run_threshold_pace',
                        'run_pace_zone_z1_lower', 'run_pace_zone_z1_upper',
                        'run_pace_zone_z2_lower', 'run_pace_zone_z2_upper',
                        'run_pace_zone_zx_lower', 'run_pace_zone_zx_upper',
                        'run_pace_zone_z3_lower', 'run_pace_zone_z3_upper',
                        'run_pace_zone_zy_lower', 'run_pace_zone_zy_upper',
                        'run_pace_zone_z4_lower', 'run_pace_zone_z4_upper',
                        'run_pace_zone_z5_lower', 'run_pace_zone_z5_upper',
                        'swim_css_pace_per_100',
                        'swim_zone_z1_lower', 'swim_zone_z1_upper',
                        'swim_zone_z2_lower', 'swim_zone_z2_upper',
                        'swim_zone_zx_lower', 'swim_zone_zx_upper',
                        'swim_zone_z3_lower', 'swim_zone_z3_upper',
                        'swim_zone_zy_lower', 'swim_zone_zy_upper',
                        'swim_zone_z4_lower', 'swim_zone_z4_upper',
                        'swim_zone_z5_lower', 'swim_zone_z5_upper',
                        'bike_ftp_test', 'run_ltp_test', 'swim_css_test'
                    ]
                    values = [
                        athlete_uuid, profile.athlete_id, now, None,
                        z.heart_rate.lt_hr,
                        *z.heart_rate.zones.z1, *z.heart_rate.zones.z2, *z.heart_rate.zones.zx, *z.heart_rate.zones.z3, *z.heart_rate.zones.zy, *z.heart_rate.zones.z4, *z.heart_rate.zones.z5,
                        z.bike_power.ftp,
                        *z.bike_power.zones.z1, *z.bike_power.zones.z2, *z.bike_power.zones.zx, *z.bike_power.zones.z3, *z.bike_power.zones.zy, *z.bike_power.zones.z4, *z.bike_power.zones.z5,
                        z.run_power.ltp, z.run_power.critical_power,
                        *z.run_power.zones.z1, *z.run_power.zones.z2, *z.run_power.zones.zx, *z.run_power.zones.z3, *z.run_power.zones.zy, *z.run_power.zones.z4, *z.run_power.zones.z5,
                        pace_to_seconds(z.run_pace.threshold_pace_per_km),
                        *[pace_to_seconds(x) for x in z.run_pace.zones.z1], *[pace_to_seconds(x) for x in z.run_pace.zones.z2], *[pace_to_seconds(x) for x in z.run_pace.zones.zx], *[pace_to_seconds(x) for x in z.run_pace.zones.z3], *[pace_to_seconds(x) for x in z.run_pace.zones.zy], *[pace_to_seconds(x) for x in z.run_pace.zones.z4], *[pace_to_seconds(x) for x in z.run_pace.zones.z5],
                        pace_to_seconds(z.swim.css_pace_per_100m),
                        *[pace_to_seconds(x) for x in z.swim.zones.z1], *[pace_to_seconds(x) for x in z.swim.zones.z2], *[pace_to_seconds(x) for x in z.swim.zones.zx], *[pace_to_seconds(x) for x in z.swim.zones.z3], *[pace_to_seconds(x) for x in z.swim.zones.zy], *[pace_to_seconds(x) for x in z.swim.zones.z4], *[pace_to_seconds(x) for x in z.swim.zones.z5],
                        profile.test_dates.bike_ftp_test, profile.test_dates.run_ltp_test, profile.test_dates.swim_css_test
                    ]
                    if len(columns) != len(values):
                        raise ValidationException(f"Column/value count mismatch: {len(columns)} columns, {len(values)} values")
                    colnames = ', '.join(columns)
                    placeholders = ', '.join(['%s'] * len(values))
                    cur.execute(f"""
                        INSERT INTO athlete_profile ({colnames})
                        VALUES ({placeholders})
                    """, values)

                    # Close previous active profile (if any) for the athlete
                    cur.execute(
                        """
                        UPDATE athlete_profile
                        SET valid_to = %s
                        WHERE athlete_id = %s AND valid_to IS NULL AND valid_from < %s
                        """,
                        (now - timedelta(seconds=1), athlete_uuid, now)
                    )
                    conn.commit()
                    logger.info(f"Profile updated successfully for athlete {profile.athlete_id}")
                return {"status": "Profile updated"}
            except Exception as e:
                conn.rollback()
                if isinstance(e, ValidationException):
                    raise
                raise DatabaseException(f"Failed to update profile: {e}")

class WorkoutSummary(BaseModel):
    id: str
    athlete_id: str
    timestamp: str
    workout_type: str
    tss: Optional[float] = None
    duration_sec: Optional[int] = None
    duration_hr: Optional[float] = None
    description: Optional[str] = None
    planned: bool = False

class WorkoutDetail(WorkoutSummary):
    json_file: Optional[dict] = None
    csv_file: Optional[str] = None
    synced_at: Optional[str] = None


class TrainingPlanInput(BaseModel):
    athlete_id: str
    race_date: str
    race_type: str
    max_workouts_per_week: int


class TrainingSessionOut(BaseModel):
    id: str
    date: str
    workout_type: str
    description: Optional[str] = None
    phase: Optional[str] = None


class TrainingPlanOut(BaseModel):
    plan_id: str
    race_date: str
    race_type: str
    max_workouts_per_week: int
    sessions: List[TrainingSessionOut]

@app.get("/api/workouts", response_model=List[WorkoutSummary])
def get_workouts(
    athlete_id: str = Query(..., description="Athlete UUID or name"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get workouts for an athlete in a date range (default: current week)."""
    try:
        athlete_uuid = get_athlete_uuid(athlete_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Athlete not found: {e}")

    today = dt.date.today()
    if not start_date:
        # Default to start of current week (Monday)
        start_date = (today - dt.timedelta(days=today.weekday())).isoformat()
    if not end_date:
        # Default to end of current week (Sunday)
        end_date = (today + dt.timedelta(days=6-today.weekday())).isoformat()

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, athlete_id, timestamp, workout_type, tss
                FROM workout
                WHERE athlete_id = %s AND timestamp::date BETWEEN %s AND %s
                ORDER BY timestamp ASC
                """,
                (athlete_uuid, start_date, end_date)
            )
            workout_rows = cur.fetchall()

            cur.execute(
                """
                SELECT id, athlete_id, session_date, workout_type, planned_tss, description
                FROM training_session
                WHERE athlete_id = %s AND session_date BETWEEN %s AND %s
                ORDER BY session_date ASC
                """,
                (athlete_uuid, start_date, end_date)
            )
            session_rows = cur.fetchall()

            result = []
            for row in workout_rows:
                result.append(WorkoutSummary(
                    id=row[0],
                    athlete_id=row[1],
                    timestamp=row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2]),
                    workout_type=row[3],
                    tss=row[4],
                    planned=False
                ))
            for row in session_rows:
                result.append(WorkoutSummary(
                    id=row[0],
                    athlete_id=row[1],
                    timestamp=row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2]),
                    workout_type=row[3],
                    tss=row[4],
                    description=row[5],
                    planned=True
                ))

            result.sort(key=lambda w: w.timestamp)
            return result

@app.post("/api/training-plan", response_model=TrainingPlanOut)
def create_training_plan(plan: TrainingPlanInput):
    """Generate a training plan and persist sessions."""
    start_date = dt.date.today()
    race_date = dt.date.fromisoformat(plan.race_date)
    agent = TrainingPlanAgent()
    sessions = agent.generate_plan(start_date, race_date, plan.max_workouts_per_week)

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO training_plan (athlete_id, race_date, race_type, max_workouts_per_week)
                VALUES (%s, %s, %s, %s) RETURNING id
                """,
                (plan.athlete_id, plan.race_date, plan.race_type, plan.max_workouts_per_week)
            )
            plan_id = cur.fetchone()[0]
            session_out: List[TrainingSessionOut] = []
            for s in sessions:
                cur.execute(
                    """
                    INSERT INTO training_session (plan_id, athlete_id, session_date, workout_type, description, phase)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (plan_id, plan.athlete_id, s["date"], s["workout_type"], s["description"], s["phase"])
                )
                sid = cur.fetchone()[0]
                session_out.append(TrainingSessionOut(
                    id=sid,
                    date=s["date"].isoformat(),
                    workout_type=s["workout_type"],
                    description=s["description"],
                    phase=s["phase"]
                ))
            conn.commit()

    return TrainingPlanOut(
        plan_id=plan_id,
        race_date=plan.race_date,
        race_type=plan.race_type,
        max_workouts_per_week=plan.max_workouts_per_week,
        sessions=session_out
    )


@app.get("/api/training-plan", response_model=TrainingPlanOut)
def get_training_plan(athlete_id: str):
    """Return latest training plan for an athlete."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, race_date, race_type, max_workouts_per_week
                FROM training_plan
                WHERE athlete_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (athlete_id,)
            )
            plan_row = cur.fetchone()
            if not plan_row:
                raise HTTPException(status_code=404, detail="Training plan not found")
            plan_id = plan_row[0]
            cur.execute(
                """
                SELECT id, session_date, workout_type, description, phase
                FROM training_session
                WHERE plan_id = %s
                ORDER BY session_date ASC
                """,
                (plan_id,)
            )
            sessions = [
                TrainingSessionOut(
                    id=r[0],
                    date=r[1].isoformat() if hasattr(r[1], 'isoformat') else str(r[1]),
                    workout_type=r[2],
                    description=r[3],
                    phase=r[4]
                )
                for r in cur.fetchall()
            ]

    return TrainingPlanOut(
        plan_id=plan_id,
        race_date=plan_row[1].isoformat() if hasattr(plan_row[1], 'isoformat') else str(plan_row[1]),
        race_type=plan_row[2],
        max_workouts_per_week=plan_row[3],
        sessions=sessions
    )

@app.get("/api/workouts/{workout_id}", response_model=WorkoutDetail)
def get_workout_detail(workout_id: str):
    """Get detailed information for a specific workout."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, athlete_id, timestamp, workout_type, tss, json_file
                FROM workout
                WHERE id = %s
                """,
                (workout_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Workout not found")
            return WorkoutDetail(
                id=row[0],
                athlete_id=row[1],
                timestamp=row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2]),
                workout_type=row[3],
                tss=row[4],
                json_file=row[5],
            )

# --- Timeseries Models ---
class TimeseriesPoint(BaseModel):
    timestamp: str
    value: float
    unit: str

class TimeseriesResponse(BaseModel):
    workout_id: str
    metric: str
    data: List[TimeseriesPoint]
    available_metrics: List[str]

@app.get("/api/workouts/{workout_id}/timeseries", response_model=TimeseriesResponse)
def get_workout_timeseries(
    workout_id: str,
    metric: str = Query(..., description="Metric type: hr, pace, power, speed, cadence, altitude, form_power, air_power")
):
    """Get timeseries data for a specific workout and metric."""
    # Define valid metrics for each workout type
    valid_metrics = {
        "swim": ["hr"],
        "bike": ["hr", "pace", "power", "speed", "cadence", "distance"],
        "run": ["hr", "pace", "power", "speed", "run_cadence", "altitude", "form_power", "air_power", "distance"]
    }
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get workout data
            cur.execute(
                """
                SELECT json_file, workout_type
                FROM workout
                WHERE id = %s
                """,
                (workout_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Workout not found")
            
            json_file = row[0]
            workout_type = row[1]
            
            if not json_file or not json_file.get("data"):
                raise HTTPException(status_code=404, detail="No timeseries data available for this workout")
            
            # Get available metrics for this workout type
            workout_metrics = valid_metrics.get(workout_type, [])
            
            # Detect which metrics are actually available in the data
            available_metrics = []
            sample_data = json_file["data"][0] if json_file["data"] else {}
            
            # Check for heart rate
            if "heart_rate" in sample_data:
                available_metrics.append("hr")
            
            # Check for GPS data (for pace calculation)
            if "latitude" in sample_data and "longitude" in sample_data:
                available_metrics.append("pace")
            
            # Check for power metrics
            if "power" in sample_data:
                available_metrics.append("power")
            if "Power" in sample_data:  # Run workouts use capital P
                available_metrics.append("power")
            if "watts" in sample_data:
                available_metrics.append("power")
            
            # Check for speed
            if "speed" in sample_data:
                available_metrics.append("speed")
            
            # Check for cadence
            if "cadence" in sample_data:
                available_metrics.append("cadence")
            if "run_cadence" in sample_data:
                available_metrics.append("run_cadence")
            
            # Check for altitude
            if "altitude" in sample_data:
                available_metrics.append("altitude")
            
            # Check for form power (run only)
            if "Form Power" in sample_data:
                available_metrics.append("form_power")
            
            # Check for air power (run only)
            if "Air Power" in sample_data:
                available_metrics.append("air_power")
            
            # Check for distance
            if "distance" in sample_data:
                available_metrics.append("distance")
            
            # Check if requested metric is available
            if metric not in available_metrics:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Metric '{metric}' not available. Available metrics: {', '.join(available_metrics)}"
                )
            
            # Extract timeseries data based on metric
            timeseries_data = []
            
            if metric == "hr":
                # Heart rate data
                for point in json_file["data"]:
                    if point.get("heart_rate") is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(point["heart_rate"]),
                            unit="bpm"
                        ))
            
            elif metric == "power":
                # Power data (handle both "power" and "Power" fields)
                for point in json_file["data"]:
                    power_value = point.get("power") or point.get("Power") or point.get("watts")
                    if power_value is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(power_value),
                            unit="W"
                        ))
            
            elif metric == "pace":
                # Calculate pace from GPS coordinates
                timeseries_data = calculate_pace_from_gps(json_file["data"])
            
            elif metric == "speed":
                # Speed data
                for point in json_file["data"]:
                    if point.get("speed") is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(point["speed"]),
                            unit="km/h"
                        ))
            
            elif metric == "cadence":
                # Cadence data (bike)
                for point in json_file["data"]:
                    if point.get("cadence") is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(point["cadence"]),
                            unit="rpm"
                        ))
            
            elif metric == "run_cadence":
                # Run cadence data
                for point in json_file["data"]:
                    if point.get("run_cadence") is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(point["run_cadence"]),
                            unit="spm"
                        ))
            
            elif metric == "altitude":
                # Altitude data
                for point in json_file["data"]:
                    if point.get("altitude") is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(point["altitude"]),
                            unit="m"
                        ))
            
            elif metric == "form_power":
                # Form power data (run only)
                for point in json_file["data"]:
                    if point.get("Form Power") is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(point["Form Power"]),
                            unit="W"
                        ))
            
            elif metric == "air_power":
                # Air power data (run only)
                for point in json_file["data"]:
                    if point.get("Air Power") is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(point["Air Power"]),
                            unit="W"
                        ))
            
            elif metric == "distance":
                # Distance data
                for point in json_file["data"]:
                    if point.get("distance") is not None:
                        timeseries_data.append(TimeseriesPoint(
                            timestamp=point.get("timestamp", ""),
                            value=float(point["distance"]),
                            unit="km"
                        ))
            
            return TimeseriesResponse(
                workout_id=workout_id,
                metric=metric,
                data=timeseries_data,
                available_metrics=available_metrics
            )

def calculate_pace_from_gps(data_points: List[Dict[str, Any]]) -> List[TimeseriesPoint]:
    """Calculate pace (min/km) from GPS coordinates."""
    pace_data = []
    
    for i in range(1, len(data_points)):
        prev_point = data_points[i-1]
        curr_point = data_points[i]
        
        # Check if both points have valid GPS coordinates
        if (prev_point.get("latitude") is not None and 
            prev_point.get("longitude") is not None and
            curr_point.get("latitude") is not None and 
            curr_point.get("longitude") is not None):
            
            # Calculate distance between points (Haversine formula)
            lat1, lon1 = float(prev_point["latitude"]), float(prev_point["longitude"])
            lat2, lon2 = float(curr_point["latitude"]), float(curr_point["longitude"])
            
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            
            # Haversine formula
            a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon/2) * math.sin(delta_lon/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance_km = 6371 * c  # Earth radius in km
            
            # Calculate time difference
            if prev_point.get("timestamp") and curr_point.get("timestamp"):
                try:
                    time1 = datetime.fromisoformat(prev_point["timestamp"].replace('Z', '+00:00'))
                    time2 = datetime.fromisoformat(curr_point["timestamp"].replace('Z', '+00:00'))
                    time_diff_minutes = (time2 - time1).total_seconds() / 60
                    
                    if time_diff_minutes > 0 and distance_km > 0:
                        # Calculate pace (minutes per kilometer)
                        pace_min_per_km = time_diff_minutes / distance_km
                        
                        # Convert to MM:SS format
                        minutes = int(pace_min_per_km)
                        seconds = int((pace_min_per_km - minutes) * 60)
                        pace_str = f"{minutes}:{seconds:02d}"
                        
                        # Store as seconds for easier charting
                        pace_seconds = minutes * 60 + seconds
                        
                        pace_data.append(TimeseriesPoint(
                            timestamp=curr_point.get("timestamp", ""),
                            value=pace_seconds,
                            unit="min/km"
                        ))
                except (ValueError, TypeError):
                    # Skip points with invalid timestamps
                    continue
    
    return pace_data

# --- Zone Analysis Models ---
class ZoneData(BaseModel):
    z1_minutes: float
    z2_minutes: float
    zx_minutes: float
    z3_minutes: float
    zy_minutes: float
    z4_minutes: float
    z5_minutes: float

class ZonesAvailable(BaseModel):
    heart_rate: bool
    power: bool

class WorkoutZoneAnalysis(BaseModel):
    heart_rate_zones: ZoneData
    power_zones: ZoneData
    total_duration_minutes: float
    zones_available: ZonesAvailable

@app.get("/api/workouts/{workout_id}/zones", response_model=WorkoutZoneAnalysis)
def get_workout_zones(workout_id: str):
    """Get zone analysis data for a specific workout."""
    from services.zone_database import get_workout_zones
    
    zone_data = get_workout_zones(workout_id)
    if not zone_data:
        raise HTTPException(status_code=404, detail="Zone analysis not found for this workout")
    
    return WorkoutZoneAnalysis(
        heart_rate_zones=ZoneData(**zone_data["heart_rate_zones"]),
        power_zones=ZoneData(**zone_data["power_zones"]),
        total_duration_minutes=zone_data["total_duration_minutes"],
        zones_available=ZonesAvailable(**zone_data["zones_available"])
    )

# --- Zone Definitions Models ---
class ZoneRange(BaseModel):
    lower: int
    upper: int

class HeartRateZones(BaseModel):
    z1: ZoneRange
    z2: ZoneRange
    zx: ZoneRange
    z3: ZoneRange
    zy: ZoneRange
    z4: ZoneRange
    z5: ZoneRange

class PowerZones(BaseModel):
    z1: ZoneRange
    z2: ZoneRange
    zx: ZoneRange
    z3: ZoneRange
    zy: ZoneRange
    z4: ZoneRange
    z5: ZoneRange

class ZoneDefinitions(BaseModel):
    heart_rate: HeartRateZones
    power: Optional[PowerZones] = None

@app.get("/api/athlete/{athlete_id}/zones", response_model=ZoneDefinitions)
def get_athlete_zones(athlete_id: str):
    """Get the latest zone definitions for an athlete."""
    try:
        athlete_uuid = get_athlete_uuid(athlete_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Athlete not found: {e}")
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get the latest athlete profile (most recent valid_from)
            cur.execute("""
                SELECT 
                    hr_zone_z1_lower, hr_zone_z1_upper,
                    hr_zone_z2_lower, hr_zone_z2_upper,
                    hr_zone_zx_lower, hr_zone_zx_upper,
                    hr_zone_z3_lower, hr_zone_z3_upper,
                    hr_zone_zy_lower, hr_zone_zy_upper,
                    hr_zone_z4_lower, hr_zone_z4_upper,
                    hr_zone_z5_lower, hr_zone_z5_upper,
                    bike_power_zone_z1_lower, bike_power_zone_z1_upper,
                    bike_power_zone_z2_lower, bike_power_zone_z2_upper,
                    bike_power_zone_zx_lower, bike_power_zone_zx_upper,
                    bike_power_zone_z3_lower, bike_power_zone_z3_upper,
                    bike_power_zone_zy_lower, bike_power_zone_zy_upper,
                    bike_power_zone_z4_lower, bike_power_zone_z4_upper,
                    bike_power_zone_z5_lower, bike_power_zone_z5_upper,
                    run_power_zone_z1_lower, run_power_zone_z1_upper,
                    run_power_zone_z2_lower, run_power_zone_z2_upper,
                    run_power_zone_zx_lower, run_power_zone_zx_upper,
                    run_power_zone_z3_lower, run_power_zone_z3_upper,
                    run_power_zone_zy_lower, run_power_zone_zy_upper,
                    run_power_zone_z4_lower, run_power_zone_z4_upper,
                    run_power_zone_z5_lower, run_power_zone_z5_upper
                FROM athlete_profile 
                WHERE athlete_id = %s 
                ORDER BY valid_from DESC 
                LIMIT 1
            """, (athlete_uuid,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="No athlete profile found")
            
            # Extract heart rate zones
            hr_zones = HeartRateZones(
                z1=ZoneRange(lower=row[0], upper=row[1]),
                z2=ZoneRange(lower=row[2], upper=row[3]),
                zx=ZoneRange(lower=row[4], upper=row[5]),
                z3=ZoneRange(lower=row[6], upper=row[7]),
                zy=ZoneRange(lower=row[8], upper=row[9]),
                z4=ZoneRange(lower=row[10], upper=row[11]),
                z5=ZoneRange(lower=row[12], upper=row[13])
            )
            
            # Extract power zones (bike and run are the same for now, using bike zones)
            power_zones = PowerZones(
                z1=ZoneRange(lower=row[14], upper=row[15]),
                z2=ZoneRange(lower=row[16], upper=row[17]),
                zx=ZoneRange(lower=row[18], upper=row[19]),
                z3=ZoneRange(lower=row[20], upper=row[21]),
                zy=ZoneRange(lower=row[22], upper=row[23]),
                z4=ZoneRange(lower=row[24], upper=row[25]),
                z5=ZoneRange(lower=row[26], upper=row[27])
            )
            
            return ZoneDefinitions(
                heart_rate=hr_zones,
                power=power_zones
            )

# --- Health and Recovery Analysis Endpoints ---

class HealthMetricData(BaseModel):
    date: str
    value: float
    unit: str

class HealthTrendData(BaseModel):
    sleep: List[HealthMetricData]
    hrv: List[HealthMetricData]
    rhr: List[HealthMetricData]

class RecoveryStatus(BaseModel):
    status: str  # "good", "moderate", "poor"
    score: float  # 0-100
    factors: List[str]

class ReadinessRecommendation(BaseModel):
    recommendation: str  # "train_hard", "maintain", "rest"
    confidence: float  # 0-100
    reasoning: str

class HealthAnalysisResponse(BaseModel):
    trends: HealthTrendData
    recovery_status: RecoveryStatus
    readiness_recommendation: ReadinessRecommendation

# --- PMC (Performance Management Chart) Models ---
class PMCMetricData(BaseModel):
    date: str
    ctl: float
    atl: float
    tsb: float

class PMCResponse(BaseModel):
    metrics: List[PMCMetricData]
    summary: Dict[str, float]  # Latest CTL, ATL, TSB values

@app.get("/api/health/trends", response_model=HealthTrendData)
def get_health_trends(
    athlete_id: str = Query(..., description="Athlete UUID or name"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get health trends (sleep, HRV, RHR) for the specified number of days."""
    try:
        athlete_uuid = get_athlete_uuid(athlete_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Athlete not found: {e}")

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Get sleep data
            cur.execute("""
                SELECT timestamp, json_file
                FROM sleep
                WHERE athlete_id = %s AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """, (athlete_uuid, days))
            sleep_data = []
            sleep_rows = cur.fetchall()
            for row in sleep_rows:
                json_data = row[1]
                if json_data and isinstance(json_data, dict):
                    # Extract sleep score from Garmin data
                    sleep_score = None
                    if 'sleepScore' in json_data:
                        sleep_score = json_data['sleepScore']
                    elif 'sleepScoreDTO' in json_data and 'sleepScore' in json_data['sleepScoreDTO']:
                        sleep_score = json_data['sleepScoreDTO']['sleepScore']
                    elif 'dailySleepDTO' in json_data and 'sleepScores' in json_data['dailySleepDTO']:
                        sleep_scores = json_data['dailySleepDTO']['sleepScores']
                        if 'overall' in sleep_scores and 'value' in sleep_scores['overall']:
                            sleep_score = sleep_scores['overall']['value']
                    
                    if sleep_score is not None:
                        sleep_data.append(HealthMetricData(
                            date=row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                            value=float(sleep_score),
                            unit="score"
                        ))

            # Get HRV data
            cur.execute("""
                SELECT timestamp, json_file
                FROM hrv
                WHERE athlete_id = %s AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """, (athlete_uuid, days))
            hrv_data = []
            for row in cur.fetchall():
                json_data = row[1]
                if json_data and isinstance(json_data, dict):
                    # Extract HRV value from Garmin data
                    hrv_value = None
                    if 'hrvSummary' in json_data:
                        hrv_summary = json_data['hrvSummary']
                        if 'weeklyAvg' in hrv_summary:
                            hrv_value = hrv_summary['weeklyAvg']
                        elif 'lastNightAvg' in hrv_summary:
                            hrv_value = hrv_summary['lastNightAvg']
                        elif 'hrvWeeklyAverage' in hrv_summary:
                            hrv_value = hrv_summary['hrvWeeklyAverage']
                        elif 'hrvDailyAverage' in hrv_summary:
                            hrv_value = hrv_summary['hrvDailyAverage']
                    
                    if hrv_value is not None:
                        hrv_data.append(HealthMetricData(
                            date=row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                            value=float(hrv_value),
                            unit="ms"
                        ))

            # Get RHR data
            cur.execute("""
                SELECT timestamp, json_file
                FROM rhr
                WHERE athlete_id = %s AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """, (athlete_uuid, days))
            rhr_data = []
            for row in cur.fetchall():
                json_data = row[1]
                if json_data and isinstance(json_data, dict):
                    # Extract RHR value from Garmin data
                    rhr_value = None
                    if 'allMetrics' in json_data and 'metricsMap' in json_data['allMetrics']:
                        metrics_map = json_data['allMetrics']['metricsMap']
                        if 'WELLNESS_RESTING_HEART_RATE' in metrics_map:
                            rhr_list = metrics_map['WELLNESS_RESTING_HEART_RATE']
                            if rhr_list and len(rhr_list) > 0:
                                rhr_value = rhr_list[0].get('value')
                    
                    if rhr_value is not None:
                        rhr_data.append(HealthMetricData(
                            date=row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                            value=float(rhr_value),
                            unit="bpm"
                        ))

            return HealthTrendData(
                sleep=sleep_data,
                hrv=hrv_data,
                rhr=rhr_data
            )

@app.get("/api/health/recovery-status", response_model=RecoveryStatus)
def get_recovery_status(
    athlete_id: str = Query(..., description="Athlete UUID or name")
):
    """Get recovery status assessment (placeholder implementation)."""
    # TODO: Implement actual recovery status calculation based on health trends
    # For now, return dummy data
    return RecoveryStatus(
        status="good",
        score=85.0,
        factors=["Good sleep quality", "Stable HRV", "Low RHR"]
    )

@app.get("/api/health/readiness", response_model=ReadinessRecommendation)
def get_readiness_recommendation(
    athlete_id: str = Query(..., description="Athlete UUID or name")
):
    """Get readiness recommendation (placeholder implementation)."""
    # TODO: Implement actual readiness calculation based on recovery status and recent training
    # For now, return dummy data
    return ReadinessRecommendation(
        recommendation="maintain",
        confidence=75.0,
        reasoning="Good recovery status, moderate training load"
    )

def get_health_trends_with_dates(athlete_id: str, start_date: str, end_date: str) -> HealthTrendData:
    """Get health trends for a specific date range."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get athlete UUID from athlete table
                cur.execute("SELECT id FROM athlete WHERE name = %s", (athlete_id,))
                result = cur.fetchone()
                if not result:
                    raise ProfileNotFoundException(f"Athlete {athlete_id} not found")
                athlete_uuid = result[0]

                # Get sleep data
                cur.execute("""
                    SELECT timestamp, json_file
                    FROM sleep
                    WHERE athlete_id = %s AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp ASC
                """, (athlete_uuid, start_date, end_date))
                sleep_data = []
                for row in cur.fetchall():
                    json_data = row[1]
                    if json_data and isinstance(json_data, dict):
                        # Extract sleep score from Garmin data
                        sleep_score = None
                        if 'dailySleepDTO' in json_data and 'sleepScores' in json_data['dailySleepDTO']:
                            sleep_scores = json_data['dailySleepDTO']['sleepScores']
                            if 'overall' in sleep_scores and 'value' in sleep_scores['overall']:
                                sleep_score = sleep_scores['overall']['value']
                        
                        if sleep_score is not None:
                            sleep_data.append(HealthMetricData(
                                date=row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                                value=float(sleep_score),
                                unit="score"
                            ))

                # Get HRV data
                cur.execute("""
                    SELECT timestamp, json_file
                    FROM hrv
                    WHERE athlete_id = %s AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp ASC
                """, (athlete_uuid, start_date, end_date))
                hrv_data = []
                for row in cur.fetchall():
                    json_data = row[1]
                    if json_data and isinstance(json_data, dict):
                        # Extract HRV value from Garmin data
                        hrv_value = None
                        if 'hrvSummary' in json_data:
                            hrv_summary = json_data['hrvSummary']
                            if 'weeklyAvg' in hrv_summary:
                                hrv_value = hrv_summary['weeklyAvg']
                            elif 'lastNightAvg' in hrv_summary:
                                hrv_value = hrv_summary['lastNightAvg']
                            elif 'hrvWeeklyAverage' in hrv_summary:
                                hrv_value = hrv_summary['hrvWeeklyAverage']
                            elif 'hrvDailyAverage' in hrv_summary:
                                hrv_value = hrv_summary['hrvDailyAverage']
                        
                        if hrv_value is not None:
                            hrv_data.append(HealthMetricData(
                                date=row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                                value=float(hrv_value),
                                unit="ms"
                            ))

                # Get RHR data
                cur.execute("""
                    SELECT timestamp, json_file
                    FROM rhr
                    WHERE athlete_id = %s AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp ASC
                """, (athlete_uuid, start_date, end_date))
                rhr_data = []
                for row in cur.fetchall():
                    json_data = row[1]
                    if json_data and isinstance(json_data, dict):
                        # Extract RHR value from Garmin data
                        rhr_value = None
                        if 'allMetrics' in json_data and 'metricsMap' in json_data['allMetrics']:
                            metrics_map = json_data['allMetrics']['metricsMap']
                            if 'WELLNESS_RESTING_HEART_RATE' in metrics_map:
                                rhr_list = metrics_map['WELLNESS_RESTING_HEART_RATE']
                                if rhr_list and len(rhr_list) > 0:
                                    rhr_value = rhr_list[0].get('value')
                        
                        if rhr_value is not None:
                            rhr_data.append(HealthMetricData(
                                date=row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                                value=float(rhr_value),
                                unit="bpm"
                            ))

                return HealthTrendData(
                    sleep=sleep_data,
                    hrv=hrv_data,
                    rhr=rhr_data
                )
    except Exception as e:
        raise DatabaseException(f"Failed to get health trends: {str(e)}")

@app.post("/api/health/agent-analysis")
def trigger_agent_analysis():
    """Trigger a new recovery analysis using the intelligent agent."""
    from agents.recovery_analysis_agent import execute_recovery_analysis
    from utils.database import get_active_profile, get_db_conn
    from datetime import datetime
    
    try:
        # Get athlete ID from profile
        profile = get_active_profile()
        if not profile:
            raise HTTPException(status_code=404, detail="No active profile found")
        
        athlete_name = profile.get("athlete_id")  # This is the human-readable name
        if not athlete_name:
            raise HTTPException(status_code=404, detail="No athlete ID found in profile")
        
        # Get athlete UUID from database
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM athlete WHERE name = %s", (athlete_name,))
                athlete_row = cur.fetchone()
                if not athlete_row:
                    raise HTTPException(status_code=404, detail=f"Athlete '{athlete_name}' not found in database")
                athlete_uuid = athlete_row[0]
        
        # Execute recovery analysis
        analysis_result = execute_recovery_analysis(athlete_name)  # Use name for agent
        
        # Store result in database using UUID - create new version
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get the next version number for today
                cur.execute("""
                    SELECT COALESCE(MAX(version), 0) + 1
                    FROM daily_recovery_analysis 
                    WHERE athlete_id = %s AND analysis_date = %s
                """, (athlete_uuid, datetime.now().date()))
                next_version = cur.fetchone()[0]
                
                # Insert new version
                cur.execute("""
                    INSERT INTO daily_recovery_analysis 
                    (athlete_id, analysis_date, version, status, detailed_reasoning, agent_analysis)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    athlete_uuid,
                    datetime.now().date(),
                    next_version,
                    analysis_result.get("status", "medium"),
                    analysis_result.get("detailed_reasoning", "Analysis completed"),
                    json.dumps(analysis_result)
                ))
                conn.commit()
        
        return {
            "status": analysis_result.get("status", "medium"),
            "detailed_reasoning": analysis_result.get("detailed_reasoning", "Analysis completed"),
            "analysis_date": analysis_result.get("analysis_date", datetime.now().strftime('%Y-%m-%d')),
            "last_updated": datetime.now().isoformat(),
            "message": "Agent analysis completed and stored"
        }
        
    except Exception as e:
        logger.error(f"Error in agent analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {str(e)}")

@app.get("/api/health/analysis")
def get_health_analysis(
    athlete_id: str = Query(None, description="Athlete ID (optional, uses active profile if not provided)"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get health analysis data, including latest agent analysis if available."""
    from utils.database import get_active_profile, get_db_conn
    from datetime import datetime, timedelta
    
    try:
        # Get athlete ID
        athlete_name = None
        athlete_uuid = None
        
        if not athlete_id:
            profile = get_active_profile()
            if not profile:
                raise HTTPException(status_code=404, detail="No active profile found")
            athlete_name = profile.get("athlete_id")  # Human-readable name
        else:
            athlete_name = athlete_id
        
        # Get athlete UUID from database
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM athlete WHERE name = %s", (athlete_name,))
                athlete_row = cur.fetchone()
                if not athlete_row:
                    raise HTTPException(status_code=404, detail=f"Athlete '{athlete_name}' not found in database")
                athlete_uuid = athlete_row[0]
        
        # Get latest agent analysis
        agent_analysis = None
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status, detailed_reasoning, agent_analysis, created_at
                    FROM daily_recovery_analysis 
                    WHERE athlete_id = %s 
                    ORDER BY analysis_date DESC, version DESC 
                    LIMIT 1
                """, (athlete_uuid,))
                agent_row = cur.fetchone()
                
                if agent_row:
                    agent_analysis = {
                        "status": agent_row[0],
                        "detailed_reasoning": agent_row[1],
                        "agent_analysis": agent_row[2],
                        "last_updated": agent_row[3].isoformat() if agent_row[3] else None
                    }
        
        # Get health trends data (existing logic)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Fetch health data (existing logic)
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get sleep data
                cur.execute("""
                    SELECT timestamp, json_file 
                    FROM sleep 
                    WHERE athlete_id = %s AND timestamp BETWEEN %s AND %s 
                    ORDER BY timestamp
                """, (athlete_uuid, start_date, end_date))
                sleep_data = cur.fetchall()
                
                # Get HRV data
                cur.execute("""
                    SELECT timestamp, json_file 
                    FROM hrv 
                    WHERE athlete_id = %s AND timestamp BETWEEN %s AND %s 
                    ORDER BY timestamp
                """, (athlete_uuid, start_date, end_date))
                hrv_data = cur.fetchall()
                
                # Get RHR data
                cur.execute("""
                    SELECT timestamp, json_file 
                    FROM rhr 
                    WHERE athlete_id = %s AND timestamp BETWEEN %s AND %s 
                    ORDER BY timestamp
                """, (athlete_uuid, start_date, end_date))
                rhr_data = cur.fetchall()
        
        # Process health data (existing logic)
        trends = {
            "sleep": [],
            "hrv": [],
            "rhr": []
        }
        
        for row in sleep_data:
            date = row[0].strftime('%Y-%m-%d')
            json_data = row[1]
            if 'sleepQuality' in json_data:
                trends["sleep"].append({
                    "date": date,
                    "value": json_data['sleepQuality'],
                    "unit": "score"
                })
        
        for row in hrv_data:
            date = row[0].strftime('%Y-%m-%d')
            json_data = row[1]
            if 'hrv' in json_data:
                trends["hrv"].append({
                    "date": date,
                    "value": json_data['hrv'],
                    "unit": "ms"
                })
        
        for row in rhr_data:
            date = row[0].strftime('%Y-%m-%d')
            json_data = row[1]
            if 'restingHeartRate' in json_data:
                trends["rhr"].append({
                    "date": date,
                    "value": json_data['restingHeartRate'],
                    "unit": "bpm"
                })
        
        # Build response with agent analysis if available
        response = {
            "trends": trends,
            "agent_analysis": agent_analysis
        }
        
        # Add legacy fields for backward compatibility
        if agent_analysis:
            response["recovery_status"] = {
                "status": agent_analysis["status"],
                "score": 85.0 if agent_analysis["status"] == "good" else 60.0 if agent_analysis["status"] == "medium" else 30.0,
                "factors": [agent_analysis["detailed_reasoning"]]
            }
            response["readiness_recommendation"] = {
                "recommendation": "maintain" if agent_analysis["status"] == "good" else "reduce" if agent_analysis["status"] == "medium" else "rest",
                "confidence": 75.0,
                "reasoning": agent_analysis["detailed_reasoning"]
            }
        else:
            # Fallback to static analysis if no agent data
            response["recovery_status"] = {
                "status": "good",
                "score": 85.0,
                "factors": ["Good sleep quality", "Stable HRV", "Low RHR"]
            }
            response["readiness_recommendation"] = {
                "recommendation": "maintain",
                "confidence": 75.0,
                "reasoning": "Good recovery status, moderate training load"
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in health analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Health analysis failed: {str(e)}")

@app.get("/api/metrics/pmc", response_model=PMCResponse)
def get_pmc_metrics(
    athlete_id: str = Query(..., description="Athlete UUID or name"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    days: int = Query(30, description="Number of days to analyze (if start_date/end_date not provided)")
):
    """Get Performance Management Chart (PMC) metrics including CTL, ATL, and TSB."""
    try:
        from datetime import date
        
        # Determine date range
        if start_date and end_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        else:
            end = date.today()
            start = end - timedelta(days=days)
        
        # Get PMC data from database
        pmc_data = pmc_metrics.get_pmc_data(athlete_id, start, end)
        
        # Convert to Pydantic models
        metrics = []
        for data in pmc_data:
            metrics.append(PMCMetricData(
                date=data['date'],
                ctl=data['ctl'],
                atl=data['atl'],
                tsb=data['tsb']
            ))
        
        # Calculate summary (latest values)
        summary = {}
        if metrics:
            latest = metrics[-1]
            summary = {
                'ctl': latest.ctl,
                'atl': latest.atl,
                'tsb': latest.tsb
            }
        else:
            # If no data, calculate for today
            today_metrics = pmc_metrics.calculate_daily_metrics(athlete_id, date.today())
            pmc_metrics.save_daily_metrics(athlete_id, date.today(), today_metrics)
            
            summary = {
                'ctl': today_metrics['ctl'],
                'atl': today_metrics['atl'],
                'tsb': today_metrics['tsb']
            }
            
            # Add today's data to metrics
            metrics.append(PMCMetricData(
                date=date.today().isoformat(),
                ctl=today_metrics['ctl'],
                atl=today_metrics['atl'],
                tsb=today_metrics['tsb']
            ))
        
        return PMCResponse(
            metrics=metrics,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get PMC metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get PMC metrics: {str(e)}")

@app.get("/api/test/recovery-table")
def test_recovery_table():
    """Test endpoint to verify the daily_recovery_analysis table is working."""
    from utils.database import test_recovery_analysis_table
    
    try:
        result = test_recovery_analysis_table()
        return {"success": result, "message": "Recovery analysis table is working" if result else "Table not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/test/recovery-agent")
def test_recovery_agent():
    """Test endpoint to verify the recovery analysis agent is working."""
    from agents.recovery_analysis_agent import execute_recovery_analysis
    from utils.database import get_active_profile
    
    try:
        # Get athlete ID from profile
        profile = get_active_profile()
        if not profile:
            return {"success": False, "error": "No active profile found"}
        
        athlete_id = profile.get("athlete_id")
        if not athlete_id:
            return {"success": False, "error": "No athlete ID found in profile"}
        
        # Execute recovery analysis
        result = execute_recovery_analysis(athlete_id)
        
        return {
            "success": True,
            "result": result,
            "message": "Recovery analysis agent executed successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
