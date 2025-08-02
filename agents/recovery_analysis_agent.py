"""
Recovery Analysis Agent using CrewAI
Analyzes RHR, HRV, sleep, and training load to provide recovery status and recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database imports
from utils.database import get_db_conn, get_active_profile

def get_athlete_uuid(athlete_name: str) -> str:
    """Get athlete UUID from name."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM athlete WHERE name = %s", (athlete_name,))
                athlete_row = cur.fetchone()
                if not athlete_row:
                    raise ValueError(f"Athlete '{athlete_name}' not found in database")
                return athlete_row[0]
    except Exception as e:
        logger.error(f"Error getting athlete UUID for '{athlete_name}': {e}")
        raise ValueError(f"Cannot find athlete '{athlete_name}' in database")

class HealthMetricsTool(BaseTool):
    """Tool to extract RHR, HRV, and sleep data for analysis."""
    
    name: str = "health_metrics_tool"
    description: str = "Extract RHR, HRV, and sleep data for the last 7 days with trend analysis"
    
    def _run(self, athlete_name: str) -> str:
        """Extract health metrics data for analysis."""
        try:
            athlete_id = get_athlete_uuid(athlete_name)
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    # Get RHR data for last 7 days
                    cur.execute("""
                        SELECT timestamp, json_file 
                        FROM rhr 
                        WHERE athlete_id = %s 
                        AND timestamp >= %s 
                        ORDER BY timestamp DESC
                    """, (athlete_id, (datetime.now() - timedelta(days=7)).date()))
                    rhr_data = cur.fetchall()
                    
                    # Get HRV data for last 7 days
                    cur.execute("""
                        SELECT timestamp, json_file 
                        FROM hrv 
                        WHERE athlete_id = %s 
                        AND timestamp >= %s 
                        ORDER BY timestamp DESC
                    """, (athlete_id, (datetime.now() - timedelta(days=7)).date()))
                    hrv_data = cur.fetchall()
                    
                    # Get sleep data for last 7 days
                    cur.execute("""
                        SELECT timestamp, json_file 
                        FROM sleep 
                        WHERE athlete_id = %s 
                        AND timestamp >= %s 
                        ORDER BY timestamp DESC
                    """, (athlete_id, (datetime.now() - timedelta(days=7)).date()))
                    sleep_data = cur.fetchall()
                    
                    # Process and structure the data
                    health_metrics = {
                        "rhr": [],
                        "hrv": [],
                        "sleep": [],
                        "analysis_period": "7 days",
                        "data_quality": "good"
                    }
                    
                    # Process RHR data
                    for row in rhr_data:
                        date = row[0].strftime('%Y-%m-%d')
                        json_data = row[1]
                        if 'restingHeartRate' in json_data:
                            health_metrics["rhr"].append({
                                "date": date,
                                "value": json_data['restingHeartRate'],
                                "unit": "bpm"
                            })
                    
                    # Process HRV data
                    for row in hrv_data:
                        date = row[0].strftime('%Y-%m-%d')
                        json_data = row[1]
                        if 'hrv' in json_data:
                            health_metrics["hrv"].append({
                                "date": date,
                                "value": json_data['hrv'],
                                "unit": "ms"
                            })
                    
                    # Process sleep data
                    for row in sleep_data:
                        date = row[0].strftime('%Y-%m-%d')
                        json_data = row[1]
                        if 'sleepQuality' in json_data:
                            health_metrics["sleep"].append({
                                "date": date,
                                "value": json_data['sleepQuality'],
                                "unit": "score"
                            })
                    
                    # Assess data quality
                    total_data_points = len(health_metrics["rhr"]) + len(health_metrics["hrv"]) + len(health_metrics["sleep"])
                    if total_data_points < 5:
                        health_metrics["data_quality"] = "poor"
                    elif total_data_points < 15:
                        health_metrics["data_quality"] = "moderate"
                    
                    return json.dumps(health_metrics, indent=2)
                    
        except Exception as e:
            logger.error(f"Error extracting health metrics: {e}")
            return json.dumps({"error": str(e), "data_quality": "poor"})

class TrainingLoadTool(BaseTool):
    """Tool to extract training load data (TSB, CTL, ATL) for analysis."""
    
    name: str = "training_load_tool"
    description: str = "Extract training load data including TSB, CTL, and ATL for load management context"
    
    def _run(self, athlete_name: str) -> str:
        """Extract training load data for analysis."""
        try:
            athlete_id = get_athlete_uuid(athlete_name)
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    # Get training status data for last 7 days
                    cur.execute("""
                        SELECT timestamp, json_file 
                        FROM training_status 
                        WHERE athlete_id = %s 
                        AND timestamp >= %s 
                        ORDER BY timestamp DESC
                    """, (athlete_id, (datetime.now() - timedelta(days=7)).date()))
                    training_data = cur.fetchall()
                    
                    # Get recent workouts for context
                    cur.execute("""
                        SELECT timestamp, workout_type, json_file 
                        FROM workout 
                        WHERE athlete_id = %s 
                        AND timestamp >= %s 
                        ORDER BY timestamp DESC
                        LIMIT 10
                    """, (athlete_id, (datetime.now() - timedelta(days=7))))
                    workout_data = cur.fetchall()
                    
                    training_load = {
                        "training_status": [],
                        "recent_workouts": [],
                        "analysis_period": "7 days",
                        "load_assessment": "moderate"
                    }
                    
                    # Process training status data
                    for row in training_data:
                        date = row[0].strftime('%Y-%m-%d')
                        json_data = row[1]
                        training_load["training_status"].append({
                            "date": date,
                            "tsb": json_data.get('tsb', 0),
                            "ctl": json_data.get('ctl', 0),
                            "atl": json_data.get('atl', 0)
                        })
                    
                    # Process recent workouts
                    total_tss = 0
                    workout_count = 0
                    for row in workout_data:
                        date = row[0].strftime('%Y-%m-%d %H:%M')
                        workout_type = row[1]
                        json_data = row[2]
                        
                        # Extract TSS if available
                        tss = json_data.get('tss', 0) if json_data else 0
                        total_tss += tss
                        workout_count += 1
                        
                        training_load["recent_workouts"].append({
                            "date": date,
                            "type": workout_type,
                            "tss": tss
                        })
                    
                    # Assess training load
                    if training_load["training_status"]:
                        latest_tsb = training_load["training_status"][0].get("tsb", 0)
                        latest_ctl = training_load["training_status"][0].get("ctl", 0)
                        latest_atl = training_load["training_status"][0].get("atl", 0)
                        
                        # Determine load assessment based on TSB
                        if latest_tsb > 10:
                            training_load["load_assessment"] = "recovery"
                        elif latest_tsb < -10:
                            training_load["load_assessment"] = "high_stress"
                        elif latest_tsb < 0:
                            training_load["load_assessment"] = "moderate_stress"
                        else:
                            training_load["load_assessment"] = "balanced"
                        
                        # Add load context
                        training_load["load_context"] = {
                            "tsb": latest_tsb,
                            "ctl": latest_ctl,
                            "atl": latest_atl,
                            "recent_tss": total_tss,
                            "workout_count": workout_count
                        }
                    
                    return json.dumps(training_load, indent=2)
                    
        except Exception as e:
            logger.error(f"Error extracting training load: {e}")
            return json.dumps({"error": str(e), "load_assessment": "unknown"})

class TrendAnalysisTool(BaseTool):
    """Tool to analyze trends and flag acute spikes/drops in health metrics."""
    
    name: str = "trend_analysis_tool"
    description: str = "Analyze 3-7 day trends in HRV, sleep, RHR and flag acute spikes/drops as warning signals"
    
    def _run(self, health_metrics_json: str) -> str:
        """Analyze trends in health metrics data."""
        try:
            health_metrics = json.loads(health_metrics_json)
            
            trend_analysis = {
                "rhr_trend": self._analyze_trend(health_metrics.get("rhr", []), "RHR", "bpm", inverse=False),
                "hrv_trend": self._analyze_trend(health_metrics.get("hrv", []), "HRV", "ms", inverse=True),
                "sleep_trend": self._analyze_trend(health_metrics.get("sleep", []), "Sleep Quality", "score", inverse=True),
                "acute_changes": self._detect_acute_changes(health_metrics),
                "overall_trend": "stable"
            }
            
            # Determine overall trend
            trend_scores = []
            for trend in [trend_analysis["rhr_trend"], trend_analysis["hrv_trend"], trend_analysis["sleep_trend"]]:
                if trend["direction"] == "improving":
                    trend_scores.append(1)
                elif trend["direction"] == "declining":
                    trend_scores.append(-1)
                else:
                    trend_scores.append(0)
            
            avg_trend = sum(trend_scores) / len(trend_scores)
            if avg_trend > 0.3:
                trend_analysis["overall_trend"] = "improving"
            elif avg_trend < -0.3:
                trend_analysis["overall_trend"] = "declining"
            
            return json.dumps(trend_analysis, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return json.dumps({"error": str(e)})
    
    def _analyze_trend(self, data: List[Dict], metric_name: str, unit: str, inverse: bool = False) -> Dict:
        """Analyze trend for a specific metric."""
        if len(data) < 3:
            return {
                "metric": metric_name,
                "direction": "insufficient_data",
                "change_percent": 0,
                "warning": "Insufficient data for trend analysis",
                "data_points": len(data),
                "recommendation": "Need more data for accurate trend analysis"
            }
        
        # Sort by date
        sorted_data = sorted(data, key=lambda x: x["date"])
        
        # Calculate trend
        recent_avg = sum(item["value"] for item in sorted_data[-3:]) / 3
        older_avg = sum(item["value"] for item in sorted_data[:3]) / 3
        
        if older_avg == 0:
            return {
                "metric": metric_name,
                "direction": "stable",
                "change_percent": 0,
                "warning": "Cannot calculate trend (zero baseline)",
                "data_points": len(data),
                "recommendation": "Baseline data needed for trend analysis"
            }
        
        change_percent = ((recent_avg - older_avg) / older_avg) * 100
        
        # Determine direction and severity
        if inverse:
            # For HRV and sleep: higher is better
            if change_percent > 10:
                direction = "improving"
                severity = "significant"
            elif change_percent > 5:
                direction = "improving"
                severity = "moderate"
            elif change_percent < -10:
                direction = "declining"
                severity = "significant"
            elif change_percent < -5:
                direction = "declining"
                severity = "moderate"
            else:
                direction = "stable"
                severity = "minimal"
        else:
            # For RHR: lower is better
            if change_percent < -10:
                direction = "improving"
                severity = "significant"
            elif change_percent < -5:
                direction = "improving"
                severity = "moderate"
            elif change_percent > 10:
                direction = "declining"
                severity = "significant"
            elif change_percent > 5:
                direction = "declining"
                severity = "moderate"
            else:
                direction = "stable"
                severity = "minimal"
        
        # Generate recommendations based on trend
        if direction == "improving":
            recommendation = f"Continue current practices for {metric_name}"
        elif direction == "declining":
            if metric_name == "RHR":
                recommendation = "Consider reducing training intensity and focus on recovery"
            elif metric_name == "HRV":
                recommendation = "Prioritize sleep quality and stress management"
            elif metric_name == "Sleep Quality":
                recommendation = "Improve sleep hygiene and recovery practices"
            else:
                recommendation = f"Monitor {metric_name} and adjust training accordingly"
        else:
            recommendation = f"Maintain current {metric_name} levels"
        
        return {
            "metric": metric_name,
            "direction": direction,
            "severity": severity,
            "change_percent": round(change_percent, 1),
            "recent_avg": round(recent_avg, 1),
            "older_avg": round(older_avg, 1),
            "unit": unit,
            "data_points": len(data),
            "recommendation": recommendation
        }
    
    def _detect_acute_changes(self, health_metrics: Dict) -> List[Dict]:
        """Detect acute spikes or drops in metrics."""
        acute_changes = []
        
        for metric_name, data in health_metrics.items():
            if len(data) < 2:
                continue
                
            sorted_data = sorted(data, key=lambda x: x["date"])
            
            for i in range(1, len(sorted_data)):
                current = sorted_data[i]["value"]
                previous = sorted_data[i-1]["value"]
                
                if previous == 0:
                    continue
                
                change_percent = ((current - previous) / previous) * 100
                
                # Flag significant changes (>15% for most metrics, >20% for sleep)
                threshold = 20 if metric_name == "sleep" else 15
                
                if abs(change_percent) > threshold:
                    acute_changes.append({
                        "metric": metric_name,
                        "date": sorted_data[i]["date"],
                        "change_percent": round(change_percent, 1),
                        "severity": "high" if abs(change_percent) > threshold * 1.5 else "moderate"
                    })
        
        return acute_changes

class RecoveryAssessmentTool(BaseTool):
    """Tool to generate recovery status and detailed reasoning based on all analysis."""
    
    name: str = "recovery_assessment_tool"
    description: str = "Generate recovery status (good/medium/bad) and detailed reasoning based on health metrics, training load, and trends"
    
    def _run(self, health_metrics_json: str, training_load_json: str, trend_analysis_json: str) -> str:
        """Generate recovery assessment and reasoning."""
        try:
            health_metrics = json.loads(health_metrics_json)
            training_load = json.loads(training_load_json)
            trend_analysis = json.loads(trend_analysis_json)
            
            # Enhanced scoring system
            score = 0
            reasoning_points = []
            detailed_analysis = []
            
            # Analyze RHR trend
            rhr_trend = trend_analysis.get("rhr_trend", {})
            if rhr_trend.get("direction") == "improving":
                score += 25
                reasoning_points.append("RHR trend is improving")
                detailed_analysis.append(f"RHR: {rhr_trend.get('change_percent', 0)}% improvement")
            elif rhr_trend.get("direction") == "declining":
                score -= 20
                reasoning_points.append(f"RHR is trending up ({rhr_trend.get('change_percent', 0)}%)")
                detailed_analysis.append(f"RHR: {rhr_trend.get('change_percent', 0)}% increase - monitor closely")
            elif rhr_trend.get("direction") == "stable":
                score += 10
                reasoning_points.append("RHR is stable")
                detailed_analysis.append(f"RHR: Stable at {rhr_trend.get('recent_avg', 0)} bpm")
            
            # Analyze HRV trend
            hrv_trend = trend_analysis.get("hrv_trend", {})
            if hrv_trend.get("direction") == "improving":
                score += 25
                reasoning_points.append("HRV trend is improving")
                detailed_analysis.append(f"HRV: {hrv_trend.get('change_percent', 0)}% improvement")
            elif hrv_trend.get("direction") == "declining":
                score -= 20
                reasoning_points.append(f"HRV is trending down ({hrv_trend.get('change_percent', 0)}%)")
                detailed_analysis.append(f"HRV: {hrv_trend.get('change_percent', 0)}% decrease - focus on recovery")
            elif hrv_trend.get("direction") == "stable":
                score += 10
                reasoning_points.append("HRV is stable")
                detailed_analysis.append(f"HRV: Stable at {hrv_trend.get('recent_avg', 0)} ms")
            
            # Analyze sleep trend
            sleep_trend = trend_analysis.get("sleep_trend", {})
            if sleep_trend.get("direction") == "improving":
                score += 20
                reasoning_points.append("Sleep quality is improving")
                detailed_analysis.append(f"Sleep: {sleep_trend.get('change_percent', 0)}% improvement")
            elif sleep_trend.get("direction") == "declining":
                score -= 15
                reasoning_points.append(f"Sleep quality is declining ({sleep_trend.get('change_percent', 0)}%)")
                detailed_analysis.append(f"Sleep: {sleep_trend.get('change_percent', 0)}% decrease - improve sleep hygiene")
            elif sleep_trend.get("direction") == "stable":
                score += 10
                reasoning_points.append("Sleep quality is stable")
                detailed_analysis.append(f"Sleep: Stable at {sleep_trend.get('recent_avg', 0)} score")
            
            # Analyze training load
            load_assessment = training_load.get("load_assessment", "unknown")
            if load_assessment == "recovery":
                score += 15
                reasoning_points.append("Training load indicates recovery phase")
                detailed_analysis.append("Training: Recovery phase (TSB > 10)")
            elif load_assessment == "balanced":
                score += 10
                reasoning_points.append("Training load is balanced")
                detailed_analysis.append("Training: Balanced load (TSB 0-10)")
            elif load_assessment == "moderate_stress":
                score -= 5
                reasoning_points.append("Moderate training stress detected")
                detailed_analysis.append("Training: Moderate stress (TSB < 0)")
            elif load_assessment == "high_stress":
                score -= 15
                reasoning_points.append("High training stress detected")
                detailed_analysis.append("Training: High stress (TSB < -10)")
            
            # Check for acute changes
            acute_changes = trend_analysis.get("acute_changes", [])
            if acute_changes:
                score -= 10
                reasoning_points.append(f"Detected {len(acute_changes)} acute changes in health metrics")
                detailed_analysis.append(f"Acute changes: {len(acute_changes)} significant changes detected")
            
            # Data quality assessment
            data_quality = health_metrics.get("data_quality", "unknown")
            if data_quality == "poor":
                score -= 5
                reasoning_points.append("Limited health data available")
                detailed_analysis.append("Data quality: Poor - limited data points")
            elif data_quality == "moderate":
                score -= 2
                reasoning_points.append("Moderate health data available")
                detailed_analysis.append("Data quality: Moderate - some data gaps")
            
            # Determine status with enhanced thresholds
            if score >= 60:
                status = "good"
                status_description = "Excellent recovery status"
            elif score >= 30:
                status = "medium"
                status_description = "Moderate recovery status"
            else:
                status = "bad"
                status_description = "Poor recovery status"
            
            # Generate comprehensive reasoning
            detailed_reasoning = f"{status_description}. "
            
            if reasoning_points:
                detailed_reasoning += "Key factors: " + "; ".join(reasoning_points) + ". "
            
            # Add specific recommendations based on status and trends
            if status == "good":
                detailed_reasoning += "Continue with current training plan. Maintain good recovery practices."
            elif status == "medium":
                detailed_reasoning += "Consider reducing training intensity or adding recovery days. Monitor health metrics closely."
            else:
                detailed_reasoning += "Recommend rest day or very light training. Focus on sleep and recovery. Consider consulting with coach."
            
            # Add trend-specific recommendations
            trend_recommendations = []
            for trend in [rhr_trend, hrv_trend, sleep_trend]:
                if trend.get("recommendation"):
                    trend_recommendations.append(trend["recommendation"])
            
            if trend_recommendations:
                detailed_reasoning += " Specific recommendations: " + "; ".join(trend_recommendations) + "."
            
            assessment = {
                "status": status,
                "score": score,
                "detailed_reasoning": detailed_reasoning,
                "trend_analysis": trend_analysis,
                "acute_changes": acute_changes,
                "training_load": training_load.get("load_assessment", "unknown"),
                "data_quality": data_quality,
                "detailed_analysis": detailed_analysis,
                "analysis_date": datetime.now().strftime('%Y-%m-%d')
            }
            
            return json.dumps(assessment, indent=2)
            
        except Exception as e:
            logger.error(f"Error in recovery assessment: {e}")
            return json.dumps({"error": str(e)})

def create_recovery_analysis_agent() -> Agent:
    """Create the recovery analysis agent."""
    return Agent(
        role="Recovery Analysis Specialist",
        goal="Analyze athlete recovery status using health metrics, training load, and trends to provide accurate status and recommendations",
        backstory="""You are an expert sports physiologist specializing in athlete recovery analysis. 
        You analyze RHR, HRV, sleep quality, and training load to determine recovery status and provide 
        actionable recommendations. You understand what metrics are important and how to interpret them.""",
        verbose=True,
        allow_delegation=False,
        tools=[
            HealthMetricsTool(),
            TrainingLoadTool(),
            TrendAnalysisTool(),
            RecoveryAssessmentTool()
        ]
    )

def execute_recovery_analysis(athlete_name: str) -> Dict[str, Any]:
    """Execute the recovery analysis using CrewAI."""
    try:
        # Create the agent
        agent = create_recovery_analysis_agent()
        
        # Create the analysis task
        task = Task(
            description=f"""
            Analyze the recovery status for athlete {athlete_name} using the following steps:
            
            1. Extract health metrics (RHR, HRV, sleep) for the last 7 days
            2. Extract training load data (TSB, CTL, ATL) for context
            3. Analyze trends in health metrics (3-7 day patterns)
            4. Detect acute spikes/drops as warning signals
            5. Generate recovery status (good/medium/bad) with detailed reasoning
            
            Focus on:
            - RHR trends (increases are negative)
            - HRV trends (decreases are negative) 
            - Sleep quality trends (decreases are negative)
            - Training stress balance (TSB) for load context
            - Acute changes as warning signals
            
            Provide specific insights including metrics like "Your RHR of 42 is high compared to your 30 day average of 40, and sleep was poor, so yellow status"
            """,
            agent=agent,
            expected_output="JSON with status, detailed_reasoning, and analysis metadata"
        )
        
        # Create and run the crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the analysis
        result = crew.kickoff()
        
        # Parse the result
        try:
            # Handle CrewOutput object
            if hasattr(result, 'raw'):
                result_str = str(result.raw)
            else:
                result_str = str(result)
            
            # Try to parse as JSON
            try:
                analysis_result = json.loads(result_str)
                return analysis_result
            except json.JSONDecodeError:
                # If result is not JSON, create a structured response
                return {
                    "status": "medium",
                    "detailed_reasoning": result_str,
                    "analysis_date": datetime.now().strftime('%Y-%m-%d'),
                    "raw_result": result_str
                }
                
        except Exception as parse_error:
            logger.error(f"Error parsing agent result: {parse_error}")
            return {
                "status": "medium",
                "detailed_reasoning": f"Analysis completed but parsing failed: {str(parse_error)}. Raw result: {str(result)}",
                "analysis_date": datetime.now().strftime('%Y-%m-%d'),
                "raw_result": str(result)
            }
            
    except Exception as e:
        logger.error(f"Error in recovery analysis: {e}")
        return {
            "status": "medium",
            "detailed_reasoning": f"Analysis failed: {str(e)}. Using fallback assessment.",
            "analysis_date": datetime.now().strftime('%Y-%m-%d'),
            "error": str(e)
        } 