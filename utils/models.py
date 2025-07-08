from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

@dataclass
class Athlete:
    id: str
    name: str
    profile: Optional[Dict[str, Any]] = None

@dataclass
class Workout:
    id: str
    athlete_id: str
    timestamp: str  # ISO 8601 string or datetime
    workout_type: str
    tss: Optional[float] = None
    duration_sec: Optional[int] = None
    duration_hr: Optional[float] = None
    json_file: Optional[Dict[str, Any]] = None  # Parsed JSON data
    csv_file: Optional[str] = None  # Raw CSV as string
    synced_at: Optional[str] = None

    def insert(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO workout (id, athlete_id, timestamp, workout_type, json_file, csv_file, tss, synced_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    self.id,
                    self.athlete_id,
                    self.timestamp,
                    self.workout_type,
                    json.dumps(self.json_file) if self.json_file else None,
                    self.csv_file,
                    self.tss,
                    self.synced_at,
                )
            )

@dataclass
class HealthMetric:
    id: str
    athlete_id: str
    metric_type: str  # 'sleep', 'hrv', 'rhr'
    timestamp: str
    json_file: Dict[str, Any]
    synced_at: Optional[str] = None

    def insert(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO {metric_type} (id, athlete_id, timestamp, json_file, synced_at)
                VALUES (%s, %s, %s, %s, %s)
                """.format(metric_type=self.metric_type),
                (
                    self.id,
                    self.athlete_id,
                    self.timestamp,
                    json.dumps(self.json_file),
                    self.synced_at,
                )
            ) 