# Product Requirements Document (PRD)

## Product Name
AIronman Coaching App

## Purpose
To provide endurance athletes with actionable insights into their training, recovery, and performance by aggregating and analyzing health and workout data from Garmin Connect, and presenting it in an intuitive, agent-driven web application.

---

## 1. Target Users
- Endurance athletes (triathletes, cyclists, runners, swimmers)
- Coaches managing multiple athletes
- Data-driven fitness enthusiasts

---

## 2. Key Features

### 2.1 Data Integration
- **Garmin Connect Integration:**  
  - Use the `python-garminconnect` package to authenticate and download user data.
  - Download health metrics (sleep, HRV, RHR, etc.) and workout data (zipped .fit, .csv, .tcx, .gpx files).
  - Special handling for .fit files to extract developer fields (e.g., Running Power) and merge with .tcx for complete workout data.

### 2.2 User Profile & Zones
- User inputs or imports:
  - Functional Threshold Power (FTP)
  - Heart rate, power, and pace zones for swim, bike, and run

### 2.3 Workout & Fitness Metrics Calculation
- Calculate per-workout metrics:
  - Training Stress Score (TSS)
  - Other relevant metrics (e.g., Intensity Factor, Normalized Power)
- Aggregate metrics:
  - Chronic Training Load (CTL)
  - Acute Training Load (ATL)
  - Training Stress Balance (TSB)
- Generate a Performance Management Chart (PMC)

### 2.4 Health & Recovery Analysis
- Analyze trends in:
  - Sleep
  - Heart Rate Variability (HRV)
  - Resting Heart Rate (RHR)
- Combine with training load to assess:
  - Fitness progress
  - Recovery status
  - Readiness to train (recommendations: train hard, maintain, or back off)

### 2.5 Agent-Based Architecture
- Use Crew AI to split the workflow into agents:
  - **Data Agent:** Handles data download and storage
  - **Processing Agent:** Extracts, merges, and processes workout files
  - **Analysis Agent:** Calculates metrics and analyzes trends
  - **UI Agent:** Prepares data for presentation and user interaction

### 2.6 Data Storage
- Store all downloaded and processed data in a structured database (e.g., PostgreSQL, SQLite).

### 2.7 Web UI
- Simple, responsive website with:
  - Performance Management Chart (PMC)
  - Coach analysis and recommendations
  - Individual health metrics with trends
  - Workout analysis and details

### 2.8 Containerization
- Application must be fully containerized (Docker) for easy deployment.

---

## 3. Technical Requirements

- **Backend:** Python (FastAPI or Flask recommended)
- **Frontend:** React, Vue, or simple HTML/CSS/JS (depending on resources)
- **Database:** PostgreSQL or SQLite
- **Agent Framework:** Crew AI
- **Garmin Integration:** python-garminconnect
- **Containerization:** Docker

---

## 4. User Stories

1. **As an athlete**, I want to connect my Garmin account so that my health and workout data is automatically imported.
2. **As an athlete**, I want to see my Performance Management Chart and understand my fitness and fatigue trends.
3. **As an athlete**, I want to receive daily recommendations on whether to train hard, maintain, or rest, based on my recovery and training load.
4. **As a coach**, I want to view detailed workout and health metrics for my athletes.
5. **As a user**, I want to access the app via a simple web interface.

---

## 5. Challenges & Special Considerations

- **File Handling:**  
  - .fit files contain developer fields (e.g., Running Power) not present in .tcx or .gpx.
  - Need robust extraction and merging logic to ensure all relevant data is available for analysis.
- **Data Privacy:**  
  - Secure storage and handling of sensitive health data.
- **Agent Coordination:**  
  - Clear task separation and communication between agents.

---

## 6. Success Metrics

- Accurate and timely import of Garmin data
- Correct calculation of training and recovery metrics
- User engagement with the web UI (e.g., daily logins, chart views)
- Positive user feedback on recommendations and insights

---

## 7. Out of Scope

- Integration with platforms other than Garmin Connect (for MVP)
- Mobile app (web only for MVP)
- Social/sharing features

---

## 8. Next Steps

1. Define database schema for health and workout data.
2. Set up Garmin Connect integration and test data download.
3. Implement file extraction and merging logic for .fit and .tcx files.
4. Develop agent-based workflow using Crew AI.
5. Build backend API and frontend UI.
6. Containerize the application. 