from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
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
from utils.database import get_db_conn

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
                print(f"test_dates raw: bike_ftp_test={row[78]} ({type(row[78])}), run_ltp_test={row[79]} ({type(row[79])}), swim_css_test={row[80]} ({type(row[80])})")
                def to_str(val):
                    print(f"Converting value: {val} ({type(val)})")
                    if isinstance(val, dt.date):
                        return val.strftime('%Y-%m-%d')
                    elif val is not None:
                        return str(val)
                    return None
                # Force conversion of test_dates fields to string
                bike_ftp_test = row[78]
                run_ltp_test = row[79]
                swim_css_test = row[80]
                if isinstance(bike_ftp_test, dt.date):
                    bike_ftp_test = bike_ftp_test.strftime('%Y-%m-%d')
                if isinstance(run_ltp_test, dt.date):
                    run_ltp_test = run_ltp_test.strftime('%Y-%m-%d')
                if isinstance(swim_css_test, dt.date):
                    swim_css_test = swim_css_test.strftime('%Y-%m-%d')
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
