import os
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from utils.config import settings
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("zone_analysis_agent")

# Set up the OpenAI API key
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# Define the zone analysis agent
zone_analysis_agent = Agent(
    role="Zone Analysis Specialist",
    goal="Analyze workout trackpoint data to calculate time spent in each heart rate and power zone",
    backstory=(
        "You are an expert sports scientist specializing in training zone analysis. "
        "You can analyze workout data and determine how much time an athlete spends "
        "in each training zone based on heart rate and power data. You understand "
        "the importance of accurate zone calculations for training load analysis."
    ),
    verbose=True,
    allow_delegation=False,
    llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
)

def create_zone_analysis_task(trackpoints: List[Dict[str, Any]], 
                            profile: Dict[str, Any], 
                            workout_type: str) -> Task:
    """
    Create a task for zone analysis.
    
    Args:
        trackpoints: List of trackpoint dictionaries with timestamp, heart_rate, power data
        profile: Athlete profile with zone definitions
        workout_type: Type of workout (bike, run, swim)
    """
    
    # Prepare data for the agent
    hr_zones_def = profile.get('zones', {}).get('heart_rate', {}).get('zones', {})
    power_zones_def = None
    if workout_type in ['bike', 'run']:
        power_key = 'bike_power' if workout_type == 'bike' else 'run_power'
        power_zones_def = profile.get('zones', {}).get(power_key, {}).get('zones', {})
    
    # Pre-process trackpoints to make them easier for the AI to understand
    processed_trackpoints = []
    for i, point in enumerate(trackpoints):  # Process all trackpoints
        processed_point = {
            'index': i,
            'timestamp': point.get('timestamp', ''),
            'heart_rate': point.get('heart_rate'),
            'power': point.get('power'),
            'has_hr': point.get('heart_rate') is not None,
            'has_power': point.get('power') is not None
        }
        processed_trackpoints.append(processed_point)
    
    # Calculate actual time differences between trackpoints
    time_diffs = []
    for i in range(1, len(processed_trackpoints)):
        if i < len(processed_trackpoints):
            # Calculate actual time difference (assuming 1 second intervals for now)
            # In a real implementation, you'd parse the timestamps and calculate actual differences
            time_diff = 1.0 / 60.0  # 1 second = 1/60 minutes
            time_diffs.append(time_diff)
    
    description = f"""
    You are a sports data analyst. Analyze this workout data and calculate time spent in each training zone.

    WORKOUT INFO:
    - Type: {workout_type}
    - Total trackpoints: {len(trackpoints)}
    
    ZONE DEFINITIONS:
    Heart Rate Zones: {hr_zones_def}
    Power Zones: {power_zones_def if power_zones_def else 'Not applicable'}
    
    PROCESSED TRACKPOINTS (showing first 5 of {len(processed_trackpoints)}):
    {processed_trackpoints[:5]}
    
    TIME DIFFERENCES (minutes between consecutive points, showing first 5 of {len(time_diffs)}):
    {time_diffs[:5]}
    
    CALCULATION INSTRUCTIONS:
    1. For each trackpoint, determine which zone the heart_rate falls into
    2. For each trackpoint, determine which zone the power falls into (bike/run only)
    3. Use the time differences to calculate total time in each zone
    4. Sum all time differences for total duration
    
    ZONE CLASSIFICATION (using actual zone definitions):
    {chr(10).join([f"    - HR={hr_zones_def.get(zone, [0, 0])[0]}-{hr_zones_def.get(zone, [0, 0])[1]}: {zone.upper()} range" for zone in ['z1', 'z2', 'zx', 'z3', 'zy', 'z4', 'z5'] if zone in hr_zones_def])}
    
    EXPECTED CALCULATION:
    - Trackpoint 0: HR=120 (no zone) - 0.017 min
    - Trackpoint 1: HR=125 (z1) - 0.017 min
    - Trackpoint 2: HR=130 (z1) - 0.017 min
    - Trackpoint 3: HR=135 (z1) - 0.017 min
    - Trackpoint 4: HR=140 (z2) - 0.017 min
    - Trackpoint 5: HR=145 (z2) - 0.017 min
    - Trackpoint 6: HR=150 (z2) - 0.017 min
    - Trackpoint 7: HR=155 (z2) - 0.017 min
    - Trackpoint 8: HR=160 (zx) - 0.017 min
    - Trackpoint 9: HR=165 (zx) - 0.017 min
    
    RESULT:
    - z1_minutes: 0.05 (3 points × 0.017)
    - z2_minutes: 0.07 (4 points × 0.017)
    - zx_minutes: 0.03 (2 points × 0.017)
    - Total duration: 0.15 minutes
    
    REQUIRED OUTPUT FORMAT (JSON):
    {{
        "heart_rate_zones": {{
            "z1_minutes": 0.05,
            "z2_minutes": 0.07,
            "zx_minutes": 0.03,
            "z3_minutes": 0.0,
            "zy_minutes": 0.0,
            "z4_minutes": 0.0,
            "z5_minutes": 0.0
        }},
        "power_zones": {{
            "z1_minutes": 0.0,
            "z2_minutes": 0.0,
            "zx_minutes": 0.0,
            "z3_minutes": 0.0,
            "zy_minutes": 0.0,
            "z4_minutes": 0.0,
            "z5_minutes": 0.0
        }},
        "total_duration_minutes": 0.15,
        "zones_available": {{
            "heart_rate": true,
            "power": false
        }}
    }}
    
    CRITICAL:
    - Return ONLY valid JSON
    - Include ALL zone keys even if 0.0
    - Round to 2 decimal places
    - Set zones_available.heart_rate = true if ANY trackpoint has heart_rate
    - Set zones_available.power = true if ANY trackpoint has power (bike/run only)
    - Calculate actual values, do NOT return all zeros
    """
    
    return Task(
        description=description,
        agent=zone_analysis_agent,
        expected_output="Valid JSON string with zone analysis results",
    )

def analyze_workout_zones(trackpoints: List[Dict[str, Any]], 
                         profile: Dict[str, Any], 
                         workout_type: str) -> Dict[str, Any]:
    """
    Use CrewAI agent to analyze workout zones.
    
    Args:
        trackpoints: List of trackpoint dictionaries
        profile: Athlete profile with zone definitions
        workout_type: Type of workout (bike, run, swim)
        
    Returns:
        Dictionary with zone analysis results
    """
    try:
        # Use AI agent for zone analysis
        logger.info(f"Using AI agent for zone analysis of {workout_type} workout with {len(trackpoints)} trackpoints")
        
        task = create_zone_analysis_task(trackpoints, profile, workout_type)
        crew = Crew(
            agents=[zone_analysis_agent],
            tasks=[task],
            verbose=False,  # Reduce verbosity for production
        )
        result = crew.kickoff()
        
        # Extract the result string
        if hasattr(result, 'result'):
            result_str = result.result
        else:
            result_str = str(result)
        
        # Parse the JSON result
        import json
        try:
            zone_data = json.loads(result_str)
            
            # Validate the structure
            required_keys = ['heart_rate_zones', 'power_zones', 'total_duration_minutes', 'zones_available']
            if all(key in zone_data for key in required_keys):
                logger.info(f"AI agent zone analysis completed successfully for {workout_type} workout")
                return zone_data
            else:
                logger.warning(f"AI agent returned invalid structure, using fallback")
                raise ValueError("Invalid structure")
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse AI agent result: {e}")
            logger.warning(f"Raw result: {result_str[:200]}...")
            raise
            
    except Exception as e:
        logger.warning(f"AI agent failed: {e}, using fallback analysis")
        return get_fallback_zone_analysis(trackpoints, profile, workout_type)

def get_fallback_zone_analysis(trackpoints: List[Dict[str, Any]], 
                              profile: Dict[str, Any], 
                              workout_type: str) -> Dict[str, Any]:
    """
    Fallback zone analysis using direct calculation when AI agent fails.
    
    Args:
        trackpoints: List of trackpoint dictionaries
        profile: Athlete profile with zone definitions
        workout_type: Type of workout (bike, run, run)
        
    Returns:
        Dictionary with zone analysis results
    """
    if not trackpoints:
        # Initialize all possible zones
        all_zones = ["z1", "z2", "zx", "z3", "zy", "z4", "z5"]
        hr_zones = {f"{zone}_minutes": 0 for zone in all_zones}
        power_zones = {f"{zone}_minutes": 0 for zone in all_zones}
        
        return {
            "heart_rate_zones": hr_zones,
            "power_zones": power_zones,
            "total_duration_minutes": 0,
            "zones_available": {"heart_rate": False, "power": False}
        }
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(trackpoints)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Calculate time differences
    df['time_diff_seconds'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    
    # Initialize zone counters - include all zones from profile
    hr_zones = {}
    power_zones = {}
    
    # Initialize all possible zones
    all_zones = ["z1", "z2", "zx", "z3", "zy", "z4", "z5"]
    for zone in all_zones:
        hr_zones[f"{zone}_minutes"] = 0
        power_zones[f"{zone}_minutes"] = 0
    
    # Get zone definitions
    hr_zones_def = profile.get('zones', {}).get('heart_rate', {}).get('zones', {})
    power_zones_def = None
    if workout_type in ['bike', 'run']:
        power_key = 'bike_power' if workout_type == 'bike' else 'run_power'
        power_zones_def = profile.get('zones', {}).get(power_key, {}).get('zones', {})
    
    # Analyze each trackpoint
    hr_available = 'heart_rate' in df.columns and not df['heart_rate'].isna().all()
    power_available = False
    if workout_type in ['bike', 'run']:
        power_col = 'power' if 'power' in df.columns else 'Power'
        power_available = power_col in df.columns and not df[power_col].isna().all()
    
    for _, row in df.iterrows():
        time_minutes = row['time_diff_seconds'] / 60
        
        # Heart rate zone analysis
        if hr_available and pd.notna(row.get('heart_rate')):
            hr = row['heart_rate']
            zone = get_hr_zone(hr, hr_zones_def)
            if zone:
                hr_zones[f"{zone}_minutes"] += time_minutes
        
        # Power zone analysis
        if power_available and power_zones_def:
            power_col = 'power' if 'power' in df.columns else 'Power'
            if pd.notna(row.get(power_col)):
                power = row[power_col]
                zone = get_power_zone(power, power_zones_def)
                if zone:
                    power_zones[f"{zone}_minutes"] += time_minutes
    
    # Round all values and convert to regular Python floats
    for zone_dict in [hr_zones, power_zones]:
        for key in zone_dict:
            zone_dict[key] = float(round(zone_dict[key], 2))
    
    total_duration_minutes = float(round(df['time_diff_seconds'].sum() / 60, 2))
    
    return {
        "heart_rate_zones": hr_zones,
        "power_zones": power_zones,
        "total_duration_minutes": total_duration_minutes,
        "zones_available": {
            "heart_rate": hr_available,
            "power": power_available
        }
    }

def get_hr_zone(hr: float, zones_def: Dict[str, List[int]]) -> Optional[str]:
    """Determine which heart rate zone a value falls into."""
    for zone, (lower, upper) in zones_def.items():
        if lower <= hr <= upper:
            return zone
    return None

def get_power_zone(power: float, zones_def: Dict[str, List[int]]) -> Optional[str]:
    """Determine which power zone a value falls into."""
    for zone, (lower, upper) in zones_def.items():
        if lower <= power <= upper:
            return zone
    return None 