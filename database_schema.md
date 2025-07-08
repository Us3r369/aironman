# Proposed Database Schema

This document outlines the proposed database schema for the AIronman application.

### **Data Sources**

-   **`profile.json`**: Contains athlete profile information, training zones (heart rate, power, pace), and key fitness test dates.
-   **`/data` directory**: Contains daily subdirectories with health metrics and workout files (.fit, .tcx, and processed .json).

### **Identified Entities**

-   **Athlete**: The primary user of the application.
-   **Health Metrics**: Daily physiological data (e.g., HRV, sleep, weight).
-   **Workouts**: Specific training sessions, categorized by type (running, biking, swimming, strength).

---

### **Proposed Table Structure**

#### 1. **`athlete`**
Stores the core profile information for each athlete.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier for the athlete. |
| `username` | String | Athlete's username (e.g., from Garmin). |
| `last_updated` | Date | The last date the profile was updated. |
| `profile_json` | JSONB | Raw JSON from `profile.json` for archival. |

#### 2. **`zone`**
Stores training zones for different sports to allow for structured analysis and reporting.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier for the zone entry. |
| `athlete_id` | Integer (FK) | Foreign key referencing `athlete.id`. |
| `sport` | String | The sport this zone applies to (e.g., 'bike_power'). |
| `zone_name`| String | The name of the zone (e.g., 'z1', 'z2'). |
| `lower_bound`| Float | The lower value of the zone. |
| `upper_bound`| Float | The upper value of the zone. |
| `unit` | String | The unit for the bounds (e.g., 'bpm', 'watts'). |

#### 3. **`test_date`**
Tracks dates of key performance tests.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier for the test date entry. |
| `athlete_id` | Integer (FK) | Foreign key referencing `athlete.id`. |
| `test_type` | String | Type of test (e.g., 'bike_ftp_test'). |
| `date` | Date | The date the test was performed. |

#### 4. **`health_metric`**
Stores daily health and wellness data.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier for the health metric entry. |
| `athlete_id` | Integer (FK) | Foreign key referencing `athlete.id`. |
| `date` | Date | The date the metric was recorded. |
| `metric_type`| String | The type of metric (e.g., 'hrv', 'sleep_score'). |
| `value` | Float | The numeric value of the metric. |
| `unit` | String | The unit of measurement for the value. |

#### 5. **`workout`**
Acts as a central table for all recorded workouts, linking to detailed metrics.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier for the workout. |
| `athlete_id` | Integer (FK) | Foreign key referencing `athlete.id`. |
| `date` | DateTime | The start date and time of the workout. |
| `type` | String | Workout type (e.g., 'running', 'biking'). |
| `name` | String | The name or title of the workout. |
| `duration_sec`| Integer | Total duration in seconds. |
| `distance_m` | Float | Total distance in meters. |
| `calories` | Integer | Total calories burned. |
| `raw_file_path` | String | Path to the original .fit or .tcx file. |
| `processed_json_path`| String | Path to the processed JSON file. |
| `notes` | Text | Any user or system-generated notes. |

#### 6. **`workout_metric`**
Stores time-series or summary data for each workout.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier for the metric entry. |
| `workout_id` | Integer (FK) | Foreign key referencing `workout.id`. |
| `metric_type`| String | The type of metric (e.g., 'power', 'heart_rate'). |
| `value` | Float | The value of the metric. |
| `unit` | String | The unit of measurement. |
| `timestamp` | DateTime | Timestamp for time-series data; null for summary. | 