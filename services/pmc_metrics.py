"""
Performance Management Chart (PMC) Metrics Calculation Service

This module provides functions to calculate CTL (Chronic Training Load),
ATL (Acute Training Load), and TSB (Training Stress Balance) for
endurance athletes based on their workout TSS data.
"""

import math
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
from utils.database import get_db_conn
from utils.exceptions import DatabaseException


class PMCMetrics:
    """Performance Management Chart metrics calculator"""
    
    def __init__(self):
        # Standard PMC decay constants
        self.CTL_DECAY_DAYS = 42  # Chronic Training Load decay
        self.ATL_DECAY_DAYS = 7   # Acute Training Load decay
        
    def calculate_decay_factor(self, days: int) -> float:
        """
        Calculate the exponential decay factor for PMC calculations.
        
        Args:
            days: Number of days for the decay period
            
        Returns:
            Decay factor (typically 0.95 for CTL, 0.86 for ATL)
        """
        return math.exp(-1 / days)
    
    def calculate_ctl(self, workouts: List[Dict], target_date: date) -> float:
        """
        Calculate Chronic Training Load (CTL) for a specific date.
        
        CTL represents long-term training load (fitness) using an exponentially
        weighted average of TSS over 42 days.
        
        Args:
            workouts: List of workout dictionaries with 'date' and 'tss' keys
            target_date: Date for which to calculate CTL
            
        Returns:
            CTL value (typically 0-150)
        """
        if not workouts:
            return 0.0
            
        decay_factor = self.calculate_decay_factor(self.CTL_DECAY_DAYS)
        ctl = 0.0
        total_weight = 0.0
        
        for workout in workouts:
            workout_date = workout['date']
            if isinstance(workout_date, str):
                workout_date = datetime.strptime(workout_date, '%Y-%m-%d').date()
            
            days_diff = (target_date - workout_date).days
            
            if days_diff >= 0 and days_diff <= self.CTL_DECAY_DAYS:
                weight = math.pow(decay_factor, days_diff)
                ctl += workout['tss'] * weight
                total_weight += weight
        
        return ctl / total_weight if total_weight > 0 else 0.0
    
    def calculate_atl(self, workouts: List[Dict], target_date: date) -> float:
        """
        Calculate Acute Training Load (ATL) for a specific date.
        
        ATL represents short-term training load (fatigue) using an exponentially
        weighted average of TSS over 7 days.
        
        Args:
            workouts: List of workout dictionaries with 'date' and 'tss' keys
            target_date: Date for which to calculate ATL
            
        Returns:
            ATL value (typically 0-150)
        """
        if not workouts:
            return 0.0
            
        decay_factor = self.calculate_decay_factor(self.ATL_DECAY_DAYS)
        atl = 0.0
        total_weight = 0.0
        
        for workout in workouts:
            workout_date = workout['date']
            if isinstance(workout_date, str):
                workout_date = datetime.strptime(workout_date, '%Y-%m-%d').date()
            
            days_diff = (target_date - workout_date).days
            
            if days_diff >= 0 and days_diff <= self.ATL_DECAY_DAYS:
                weight = math.pow(decay_factor, days_diff)
                atl += workout['tss'] * weight
                total_weight += weight
        
        return atl / total_weight if total_weight > 0 else 0.0
    
    def calculate_tsb(self, ctl: float, atl: float) -> float:
        """
        Calculate Training Stress Balance (TSB) from CTL and ATL.
        
        TSB = CTL - ATL (fitness - fatigue)
        Positive TSB indicates readiness to train, negative indicates fatigue.
        
        Args:
            ctl: Chronic Training Load value
            atl: Acute Training Load value
            
        Returns:
            TSB value (typically -50 to +50)
        """
        return ctl - atl
    
    def get_workouts_for_athlete(self, athlete_id: str, start_date: date, end_date: date) -> List[Dict]:
        """
        Retrieve workouts for an athlete within a date range.
        
        Args:
            athlete_id: Athlete identifier
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of workout dictionaries with date and TSS
        """
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    # Get athlete UUID
                    cur.execute("SELECT id FROM athlete WHERE name = %s", (athlete_id,))
                    result = cur.fetchone()
                    if not result:
                        raise ValueError(f"Athlete {athlete_id} not found")
                    athlete_uuid = result[0]
                    
                    # Get workouts with TSS
                    cur.execute("""
                        SELECT timestamp, tss
                        FROM workout
                        WHERE athlete_id = %s 
                        AND timestamp >= %s 
                        AND timestamp <= %s
                        AND tss IS NOT NULL
                        ORDER BY timestamp ASC
                    """, (athlete_uuid, start_date, end_date))
                    
                    workouts = []
                    for row in cur.fetchall():
                        workouts.append({
                            'date': row[0].date() if hasattr(row[0], 'date') else row[0],
                            'tss': float(row[1]) if row[1] else 0.0
                        })
                    
                    return workouts
                    
        except Exception as e:
            raise DatabaseException(f"Failed to get workouts for PMC calculation: {str(e)}")
    
    def calculate_daily_metrics(self, athlete_id: str, target_date: date) -> Dict[str, float]:
        """
        Calculate CTL, ATL, and TSB for a specific athlete and date.
        
        Args:
            athlete_id: Athlete identifier
            target_date: Date for which to calculate metrics
            
        Returns:
            Dictionary with 'ctl', 'atl', and 'tsb' values
        """
        # Get workouts for the past 42 days (CTL decay period)
        start_date = target_date - timedelta(days=self.CTL_DECAY_DAYS)
        workouts = self.get_workouts_for_athlete(athlete_id, start_date, target_date)
        
        # Calculate metrics
        ctl = self.calculate_ctl(workouts, target_date)
        atl = self.calculate_atl(workouts, target_date)
        tsb = self.calculate_tsb(ctl, atl)
        
        return {
            'ctl': round(ctl, 2),
            'atl': round(atl, 2),
            'tsb': round(tsb, 2)
        }
    
    def save_daily_metrics(self, athlete_id: str, target_date: date, metrics: Dict[str, float]) -> None:
        """
        Save daily metrics to the database.
        
        Args:
            athlete_id: Athlete identifier
            target_date: Date for the metrics
            metrics: Dictionary with 'ctl', 'atl', 'tsb' values
        """
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    # Get athlete UUID
                    cur.execute("SELECT id FROM athlete WHERE name = %s", (athlete_id,))
                    result = cur.fetchone()
                    if not result:
                        raise ValueError(f"Athlete {athlete_id} not found")
                    athlete_uuid = result[0]
                    
                    # Upsert daily metrics
                    cur.execute("""
                        INSERT INTO daily_metrics (athlete_id, date, ctl, atl, tsb)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (athlete_id, date)
                        DO UPDATE SET
                            ctl = EXCLUDED.ctl,
                            atl = EXCLUDED.atl,
                            tsb = EXCLUDED.tsb,
                            updated_at = NOW()
                    """, (
                        athlete_uuid,
                        target_date,
                        metrics['ctl'],
                        metrics['atl'],
                        metrics['tsb']
                    ))
                    
                    conn.commit()
                    
        except Exception as e:
            raise DatabaseException(f"Failed to save daily metrics: {str(e)}")
    
    def get_pmc_data(self, athlete_id: str, start_date: date, end_date: date) -> List[Dict]:
        """
        Get PMC data for an athlete within a date range.
        
        Args:
            athlete_id: Athlete identifier
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of daily metrics dictionaries
        """
        try:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    # Get athlete UUID
                    cur.execute("SELECT id FROM athlete WHERE name = %s", (athlete_id,))
                    result = cur.fetchone()
                    if not result:
                        raise ValueError(f"Athlete {athlete_id} not found")
                    athlete_uuid = result[0]
                    
                    # Get daily metrics
                    cur.execute("""
                        SELECT date, ctl, atl, tsb
                        FROM daily_metrics
                        WHERE athlete_id = %s 
                        AND date >= %s 
                        AND date <= %s
                        ORDER BY date ASC
                    """, (athlete_uuid, start_date, end_date))
                    
                    pmc_data = []
                    for row in cur.fetchall():
                        pmc_data.append({
                            'date': row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                            'ctl': float(row[1]) if row[1] else 0.0,
                            'atl': float(row[2]) if row[2] else 0.0,
                            'tsb': float(row[3]) if row[3] else 0.0
                        })
                    
                    return pmc_data
                    
        except Exception as e:
            raise DatabaseException(f"Failed to get PMC data: {str(e)}")


# Global instance for easy access
pmc_metrics = PMCMetrics() 
def calculate_pmc_metrics(workouts: List[Dict]) -> Dict[str, Any]:
    """Calculate per-workout metrics and overall PMC summary.

    Args:
        workouts: list of dicts with at least ``timestamp`` and ``tss`` keys.

    Returns:
        dict with two keys:
            ``metrics`` – simple echo of input workouts with timestamp and tss
            ``summary`` – aggregate CTL/ATL/TSB values for today
    """
    pmc = PMCMetrics()
    metrics = []
    formatted = []
    for w in workouts:
        ts = w.get('timestamp')
        tss = float(w.get('tss', 0))
        metrics.append({'timestamp': ts, 'tss': tss})
        if isinstance(ts, datetime):
            formatted.append({'date': ts.date(), 'tss': tss})
        elif ts is not None:
            formatted.append({'date': ts, 'tss': tss})
    today = date.today()
    ctl = pmc.calculate_ctl(formatted, today)
    atl = pmc.calculate_atl(formatted, today)
    tsb = pmc.calculate_tsb(ctl, atl)
    summary = {'ctl': round(ctl, 2), 'atl': round(atl, 2), 'tsb': round(tsb, 2)}
    return {'metrics': metrics, 'summary': summary}
