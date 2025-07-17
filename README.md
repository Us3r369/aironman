# AIronman Coaching App

AIronman is an agent-driven web application for endurance athletes and coaches. It aggregates, analyzes, and visualizes health and workout data from Garmin Connect, providing actionable insights into training, recovery, and performance.

---

## Features

- **Garmin Connect Integration:** Securely syncs workouts and health metrics (sleep, HRV, RHR, etc.) from Garmin Connect.
- **Profile & Zones:** Stores athlete profiles, training zones, and key fitness test dates.
- **Workout & Fitness Metrics:** Calculates TSS, CTL, ATL, TSB, and other performance metrics.
- **Health & Recovery Analysis:** Tracks trends in sleep, HRV, and RHR to provide readiness recommendations.
- **Agent-Based Architecture:** Modular agents handle data ingestion, processing, analysis, and UI preparation.
- **Web UI:** Modern React frontend with calendar and chart views for workouts and health data.
- **Containerized:** Fully Dockerized for easy local development and deployment.

---

## Architecture Overview

```mermaid
graph TD
  subgraph Frontend
    A[React App] 
  end
  subgraph Backend
    B[FastAPI App]
    C[Agent System (CrewAI)]
    D[Data Processing]
  end
  subgraph Database
    E[(PostgreSQL)]
  end
  subgraph External
    F[Garmin Connect]
  end

  A <--> B
  B <--> C
  C <--> D
  D <--> E
  B <--> E
  C <--> F
```

- **Frontend:** React app (served by Nginx in Docker) for user interaction.
- **Backend:** FastAPI app orchestrates agents, handles API requests, and manages data.
- **Agents:** CrewAI-based agents for data sync, processing, and analysis.
- **Database:** PostgreSQL stores all athlete, workout, and health data.
- **Garmin Connect:** Data source for workouts and health metrics.

---

## Quickstart: Running with Docker

### 1. Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/) installed.
- Garmin Connect authentication tokens (see below).

### 2. Garmin Connect Authentication

This app requires valid Garmin Connect tokens, generated using the [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) library.

**Steps:**
1. Clone and run the example script from the `python-garminconnect` repo on your local machine.
2. Authenticate with your Garmin credentials and complete MFA if prompted.
3. Ensure the following files exist in your home directory:  
   `~/.garminconnect/oauth1_token.json`  
   `~/.garminconnect/oauth2_token.json`

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

```
POSTGRES_DB=aironman
POSTGRES_USER=youruser
POSTGRES_PASSWORD=yourpassword
```

### 4. Start the App

From the project root, run:

```sh
docker-compose up --build
```

- The backend (FastAPI) will be available at [http://localhost:8000](http://localhost:8000)
- The frontend (React) will be available at [http://localhost:3000](http://localhost:3000)

### 5. Using Your Garmin Tokens in Docker

The backend service mounts your local `~/.garminconnect` directory into the container:

```yaml
volumes:
  - ~/.garminconnect:/app/.garmin_tokens
```

Set in your `.env`:

```
GARMINTOKENS=/app/.garmin_tokens
```

---

## Project Structure

```
.
├── api/            # FastAPI backend
├── agents/         # CrewAI agent logic
├── data/           # Synced and processed data
├── database/       # SQL schema, seed scripts
├── frontend/       # React app (served by Nginx)
├── services/       # Data sync, preprocessing, auth
├── utils/          # Utility modules
├── docker-compose.yml
├── Dockerfile      # Backend Dockerfile
├── environment.yaml
├── requirements.txt
└── README.md
```

---

## Database Schema

- **athlete:** Profile and metadata for each user.
- **zone:** Training zones for each sport.
- **test_date:** Key fitness test dates.
- **health_metric:** Daily health data (HRV, sleep, etc.).
- **workout:** Workout sessions and metadata.
- **workout_metric:** Time-series and summary metrics for workouts.

See [`database_schema.md`](database_schema.md) for full details.

---

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, CrewAI, GarminConnect, PostgreSQL
- **Frontend:** React, Nginx
- **Containerization:** Docker, Docker Compose

---

## Development

- To set up a local Python environment (optional, for backend dev):
  ```sh
  chmod +x setup_env.sh
  ./setup_env.sh
  ```

- To run the frontend locally (optional):
  ```sh
  cd frontend
  npm install
  npm start
  ```