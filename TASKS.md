# AIronman Coaching App – Task List

## 1. Project Setup & Infrastructure
- [x] Set up project repository structure (backend, frontend, database, agents, docs)
- [x] Initialize Python environment and install dependencies (FastAPI/Flask, python-garminconnect, Crew AI, database drivers, etc.)
- [x] Set up Docker for containerization (Dockerfile, docker-compose)
- [x] Set up version control best practices (branching, PRs, code review)

---

## 2. Garmin Connect Integration
- [x] Integrate python-garminconnect for authentication and data download. Use @referece_files/download_activities.py as guidance to understand authentication, etc.
- [x] Implement data fetching and local storage for:
  - Health metrics (sleep, HRV, RHR, etc.)
  - Workout files (.zip, .csv, .tcx, .gpx)
- [x] Schedule/trigger regular data syncs

---

## 3. Workout File Handling & Processing
- [x] Implement .fit file extraction, including developer fields (e.g., Running Power)
- [x] Implement .tcx file parsing
- [x] For run workouts, add powerdata to other metrics based on the timestamp into one resulting <activityid>_processed.json file 
- [x] Break sync.py into two distinct steps and scripts: Pure download (sync.py), and any processing of the files (preprocess.py)
- [x] Reorganize codebase into /api, /services, /models, /utils, /tests, etc.
- [x] Expand documentation (README, docstrings, diagrams)

---

## 4. Database Design & Implementation
- [x] Design database schema for:
  - User profiles (FTP, zones, etc.)
  - Health metrics (sleep, HRV, RHR, etc.)
  - Workout data (raw files, extracted metrics)
  - Aggregated metrics (TSS, CTL, ATL, TSB)
  - Analysis results and recommendations
- [x] Implement database models and migrations
- [x] Set up database connection and ORM (e.g., SQLAlchemy)
- [x] Replace local filestorage with database
- [x] Implement update logic for incremental sync (replace file system scan with database query)
  - New SQL table for sync tracking
  - Add synced_at to health/workout tables
  - Insert initial sync row for athlete
  - Use DB for last sync date , update after sync, check for duplicates
  - remove/ replace file-based date logic
- [ ] Get rid of local file storage
---

## 5. User Profile & Zone Management
  - [ ] **Backend API Endpoints:**
    - [x] `GET /api/profile` - Fetch current athlete profile from database
    - [ ] `PUT /api/profile` - Update athlete profile in database  
    - [ ] `GET /api/sync/status` - Get sync status/history (enhance existing `/sync` endpoint)
  - [ ] **Frontend React App:**
    - [x] Create React app with sidebar navigation (Sync Garmin Data, User Profile)
    - [ ] Profile management component with zone editing (one sport at a time)
    - [ ] Sync status component with history
    - [x] Styling based on endurance dashboard reference
  - [ ] **Database Integration:**
    - [ ] Use existing `athlete_profile` table structure
    - [ ] Convert between JSON format and database columns
    - [ ] Handle pace/time conversions (mm:ss ↔ seconds)
  - [ ] **Containerization:**
    - [ ] Create separate Docker container for React frontend
    - [ ] Update docker-compose.yml to include frontend service
    - [ ] Configure CORS and API communication between containers

---

## 6. Metrics Calculation
- [x] Implement per-workout metrics calculation:
  - Training Stress Score (TSS)
- [ ] Implement aggregation for:
  - Chronic Training Load (CTL)
  - Acute Training Load (ATL)
  - Training Stress Balance (TSB)
- [ ] Generate Performance Management Chart (PMC) data

---

## 7. Health & Recovery Analysis
- [ ] Analyze trends in sleep, HRV, RHR, etc.
- [ ] Combine health and training data to assess:
  - Fitness progress
  - Recovery status
  - Readiness to train (recommendations)

---

## 8. Agent-Based Architecture (Crew AI)
- [ ] Define agent roles and responsibilities:
  - Data Agent (download & store)
  - Processing Agent (extract, merge, process)
  - Analysis Agent (metrics, trends, recommendations)
  - UI Agent (prepare data for frontend)
- [ ] Implement agent workflows and communication
- [ ] Test agent-based task execution

---

## 9. Backend API
- [ ] Design and implement REST API endpoints for:
  - User authentication and profile management
  - Data retrieval (metrics, charts, recommendations)
  - Workout and health data access
- [ ] Secure API endpoints (auth, permissions)

---

## 10. Frontend Web UI
- [ ] Design simple, responsive UI (React/Vue/HTML+JS)
- [ ] Implement:
  - Performance Management Chart (PMC) visualization
  - Coach analysis and recommendations display
  - Health metrics and trends dashboard
  - Workout analysis and details view
- [ ] Connect frontend to backend API
- [ ] Move Garmin authentication into the app instead of pulling the tokens into the container upon built

---

## 11. Containerization & Deployment
- [ ] Finalize Dockerfile and docker-compose for all services
- [ ] Test local containerized deployment
- [ ] Prepare deployment documentation

---

## 12. Testing & Quality Assurance
- [ ] Write unit and integration tests for backend logic
- [ ] Test agent workflows and data processing
- [ ] Test frontend UI and API integration
- [ ] Conduct end-to-end user flow testing

---

## 13. Documentation
- [ ] Update and maintain PRD and technical documentation
- [ ] Write user onboarding and usage guides
- [ ] Document agent roles and workflows

---

## 14. Out of Scope (for MVP)
- [ ] Integration with platforms other than Garmin Connect
- [ ] Mobile app development
- [ ] Social/sharing features 