from datetime import date, timedelta
from typing import List, Dict

class TrainingPlanAgent:
    """Simple rule-based agent to generate a training plan.

    The implementation is intentionally modular so workout type templates
    can easily be adjusted or extended.
    """

    WORKOUT_LIBRARY: Dict[str, str] = {
        "easy_run": "Easy run in zone 2",
        "long_run": "Long run building endurance",
        "rest": "Rest or cross-training"
    }

    def generate_plan(
        self,
        start_date: date,
        race_date: date,
        workouts_per_week: int
    ) -> List[Dict]:
        """Generate a very simple training plan.

        Args:
            start_date: first day of the plan
            race_date: target race day
            workouts_per_week: maximum number of sessions per week

        Returns:
            List of session dictionaries with keys:
            date, workout_type, description, phase
        """
        total_days = (race_date - start_date).days
        total_weeks = max(total_days // 7, 1)

        # Determine phase lengths (base, build, peak, taper)
        phase_weeks = {
            "base": max(int(total_weeks * 0.4), 1),
            "build": max(int(total_weeks * 0.3), 1),
            "peak": max(int(total_weeks * 0.2), 1),
            "taper": max(total_weeks - sum(
                [int(total_weeks * 0.4), int(total_weeks * 0.3), int(total_weeks * 0.2)]
            ), 1),
        }

        sessions = []
        current = start_date
        for phase, weeks in phase_weeks.items():
            for _ in range(weeks):
                for day in range(workouts_per_week):
                    # simple rotation: long run on day 0, easy otherwise
                    if day == 0 and phase != "taper":
                        wtype = "long_run"
                    elif day == workouts_per_week - 1:
                        wtype = "rest"
                    else:
                        wtype = "easy_run"
                    sessions.append({
                        "date": current,
                        "workout_type": wtype,
                        "description": self.WORKOUT_LIBRARY[wtype],
                        "phase": phase,
                    })
                    current += timedelta(days=1)
                # move to next week (skip remaining days)
                current += timedelta(days=max(0, 7 - workouts_per_week))
        return sessions
