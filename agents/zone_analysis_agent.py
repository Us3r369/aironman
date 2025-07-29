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
    
    # Convert trackpoints to a more readable format for the agent
    sample_data = trackpoints[:5] if trackpoints else []
    
    description = f"""
    Analyze the workout trackpoint data to calculate time spent in each training zone.
    
    Workout Type: {workout_type}
    
    Athlete Profile Zones:
    {profile.get('zones', {})}
    
    Sample Trackpoint Data (first 5 points):
    {sample_data}
    
    Total Trackpoints: {len(trackpoints)}
    
    Instructions:
    1. For each trackpoint, determine which zone the heart rate falls into (if available)
    2. For each trackpoint, determine which zone the power falls into (if available, for bike/run only)
    3. Calculate the total time spent in each zone
    4. Return the results in JSON format with the following structure:
    {{
        "heart_rate_zones": {{
            "z1_minutes": float,
            "z2_minutes": float,
            "z3_minutes": float,
            "z4_minutes": float,
            "z5_minutes": float
        }},
        "power_zones": {{
            "z1_minutes": float,
            "z2_minutes": float,
            "z3_minutes": float,
            "z4_minutes": float,
            "z5_minutes": float
        }},
        "total_duration_minutes": float,
        "zones_available": {{
            "heart_rate": bool,
            "power": bool
        }}
    }}
    
    Notes:
    - Only analyze power zones for bike and run workouts
    - Handle missing data gracefully
    - Calculate time differences between consecutive trackpoints
    - Round all time values to 2 decimal places
    """
    
    return Task(
        description=description,
        agent=zone_analysis_agent,
        expected_output="JSON string with zone analysis results",
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
        task = create_zone_analysis_task(trackpoints, profile, workout_type)
        crew = Crew(
            agents=[zone_analysis_agent],
            tasks=[task],
            verbose=True,
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
            logger.info(f"Zone analysis completed for {workout_type} workout")
            return zone_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse zone analysis result: {e}")
            logger.error(f"Raw result: {result_str}")
            return get_fallback_zone_analysis(trackpoints, profile, workout_type)
            
    except Exception as e:
        logger.error(f"Zone analysis failed: {e}")
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
    
    # Round all values
    for zone_dict in [hr_zones, power_zones]:
        for key in zone_dict:
            zone_dict[key] = round(zone_dict[key], 2)
    
    total_duration_minutes = round(df['time_diff_seconds'].sum() / 60, 2)
    
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