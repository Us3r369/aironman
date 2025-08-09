"""Multi-agent orchestration for Garmin data processing and analysis.

This module defines lightweight agents that wrap existing services to provide
an explicit multi-agent architecture. The agents can be composed by a
``SchedulerAgent`` to execute the full data pipeline:

1. ``GarminSyncAgent`` downloads workouts and health metrics.
2. ``WorkoutProcessorAgent`` parses raw downloads into ``Workout`` models.
3. ``MetricsAgent`` updates chronic/acute training load metrics.
4. ``RecoveryAnalysisAgent`` (existing) provides recovery status.

The agents are intentionally simple and rely on the repository's service layer.
They serve as a starting point for a richer collaborative agent system.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List

from services import sync as sync_service
from services import preprocess
from services import pmc_metrics
from utils.models import Workout
from utils import database


@dataclass
class DatabaseAgent:
    """Thin wrapper around ``utils.database`` functions."""
    def save_workout(self, workout: Workout) -> None:
        database.execute_query(
            """
            INSERT INTO workouts (
                id, workout_date, type, tss, details
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                workout.id,
                workout.workout_date,
                workout.workout_type,
                workout.tss,
                workout.details,
            ),
        )

    def save_metrics(self, metrics: pmc_metrics.PMCMetrics) -> None:
        database.execute_query(
            """
            INSERT INTO daily_metrics (
                metric_date, ctl, atl, tsb
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(metric_date) DO UPDATE SET
                ctl=excluded.ctl,
                atl=excluded.atl,
                tsb=excluded.tsb
            """,
            (
                metrics.metric_date,
                metrics.ctl,
                metrics.atl,
                metrics.tsb,
            ),
        )


class GarminSyncAgent:
    """Handles authentication and raw data download from Garmin."""

    def __init__(self, db: DatabaseAgent):
        self.db = db

    def sync_range(self, start: date, end: date) -> List[Path]:
        garmin = sync_service.get_garmin_client()
        date_dir = Path("data") / start.isoformat()
        date_dir.mkdir(parents=True, exist_ok=True)
        downloaded = sync_service.fetch_and_save_activities(
            garmin, date_dir, start, end
        )
        return downloaded


class WorkoutProcessorAgent:
    """Parses downloaded files and stores ``Workout`` rows."""

    def __init__(self, db: DatabaseAgent):
        self.db = db

    def process_files(self, files: List[Path]) -> List[Workout]:
        workouts: List[Workout] = []
        for f in files:
            processed = preprocess.process_downloaded_files(f)
            if isinstance(processed, Workout):
                self.db.save_workout(processed)
                workouts.append(processed)
        return workouts


class MetricsAgent:
    """Calculates CTL/ATL/TSB using ``PMCMetrics``."""

    def __init__(self, db: DatabaseAgent):
        self.db = db

    def update(self, workout_history: List[Workout]) -> pmc_metrics.PMCMetrics:
        metrics = pmc_metrics.PMCMetrics.from_workouts(workout_history)
        self.db.save_metrics(metrics)
        return metrics


class SchedulerAgent:
    """Coordinates the full pipeline of agents."""

    def __init__(self):
        self.db_agent = DatabaseAgent()
        self.sync_agent = GarminSyncAgent(self.db_agent)
        self.processor_agent = WorkoutProcessorAgent(self.db_agent)
        self.metrics_agent = MetricsAgent(self.db_agent)

    def run(self, start: date, end: date) -> pmc_metrics.PMCMetrics:
        files = self.sync_agent.sync_range(start, end)
        workouts = self.processor_agent.process_files(files)
        return self.metrics_agent.update(workouts)
