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

# Import new logging and exception handling
from utils.logging_config import setup_logging, get_logger, get_correlation_id, set_correlation_id, ErrorContext
from utils.exceptions import (
    AIronmanException, DatabaseException, ProfileNotFoundException, 
    ProfileValidationException, SyncException, ValidationException
)
from utils.database import get_db_conn, get_athlete_uuid

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
                    columns = [
                        'json_athlete_id', 'valid_from', 'valid_to',
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
                        profile.athlete_id, now, None,
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
                    # Update valid_to for previous rows for this athlete
                    cur.execute(
                        """
                        UPDATE athlete_profile
                        SET valid_to = %s
                        WHERE json_athlete_id = %s AND valid_to IS NULL AND valid_from < %s
                        """,
                        (now - timedelta(seconds=1), profile.athlete_id, now)
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
    # Add more fields as needed for the frontend

class WorkoutDetail(WorkoutSummary):
    json_file: Optional[dict] = None
    csv_file: Optional[str] = None
    synced_at: Optional[str] = None

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
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append(WorkoutSummary(
                    id=row[0],
                    athlete_id=row[1],
                    timestamp=row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2]),
                    workout_type=row[3],
                    tss=row[4],
                ))
            return result

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

@app.get("/api/health/analysis", response_model=HealthAnalysisResponse)
def get_health_analysis(
    athlete_id: str = Query(..., description="Athlete UUID or name"),
    days: int = Query(30, description="Number of days to analyze"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get comprehensive health analysis including trends, recovery status, and readiness."""
    if start_date and end_date:
        trends = get_health_trends_with_dates(athlete_id, start_date, end_date)
    else:
        trends = get_health_trends(athlete_id, days)
    
    recovery_status = get_recovery_status(athlete_id)
    readiness_recommendation = get_readiness_recommendation(athlete_id)
    
    return HealthAnalysisResponse(
        trends=trends,
        recovery_status=recovery_status,
        readiness_recommendation=readiness_recommendation
    )
