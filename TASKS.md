# AIronman Coaching App – Task List

## ✅ **Completed Features**

### 1. Project Setup & Infrastructure
- [x] Set up project repository structure (backend, frontend, database, agents, docs)
- [x] Initialize Python environment and install dependencies (FastAPI/Flask, python-garminconnect, Crew AI, database drivers, etc.)
- [x] Set up Docker for containerization (Dockerfile, docker-compose)
- [x] Set up version control best practices (branching, PRs, code review)

### 2. Garmin Connect Integration
- [x] Integrate python-garminconnect for authentication and data download
- [x] Implement data fetching and local storage for:
  - Health metrics (sleep, HRV, RHR, etc.)
  - Workout files (.zip, .csv, .tcx, .gpx)
- [x] Schedule/trigger regular data syncs
- [x] 42-day historical data sync script

### 3. Workout File Handling & Processing
- [x] Implement .fit file extraction, including developer fields (e.g., Running Power)
- [x] Implement .tcx file parsing
- [x] For run workouts, add powerdata to other metrics based on the timestamp into one resulting <activityid>_processed.json file 
- [x] Break sync.py into two distinct steps and scripts: Pure download (sync.py), and any processing of the files (preprocess.py)
- [x] Reorganize codebase into /api, /services, /models, /utils, /tests, etc.
- [x] Expand documentation (README, docstrings, diagrams)

### 4. Database Design & Implementation
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

### 5. User Profile & Zone Management
- [x] **Backend API Endpoints:**
  - [x] `GET /api/profile` - Fetch current athlete profile from database
  - [x] `PUT /api/profile` - Update athlete profile in database  
  - [x] `GET /api/sync/status` - Get sync status/history (enhance existing `/sync` endpoint)
- [x] **Frontend React App:**
  - [x] Create React app with sidebar navigation (Sync Garmin Data, User Profile, Health & Recovery)
  - [x] Profile management component with zone editing (one sport at a time)
  - [x] Sync status component with history
  - [x] Styling based on endurance dashboard reference
- [x] **Database Integration:**
  - [x] Use existing `athlete_profile` table structure
  - [x] Convert between JSON format and database columns
  - [x] Handle pace/time conversions (mm:ss ↔ seconds)
- [x] **Containerization:**
  - [x] Create separate Docker container for React frontend
  - [x] Update docker-compose.yml to include frontend service
  - [x] Configure CORS and API communication between containers

### 6. Metrics Calculation
- [x] Implement per-workout metrics calculation:
  - Training Stress Score (TSS)
- [ ] Implement aggregation for:
  - Chronic Training Load (CTL)
  - Acute Training Load (ATL)
  - Training Stress Balance (TSB)
- [ ] Generate Performance Management Chart (PMC) data

### 7. Health & Recovery Analysis ✅ **COMPLETED**
- [x] Analyze trends in sleep, HRV, RHR, etc.
- [x] Combine health and training data to assess:
  - Fitness progress
  - Recovery status
  - Readiness to train (recommendations)
- [x] **Week Navigation**: Navigate through different weeks to analyze historical trends
- [x] **Visual Analytics**: Beautiful line charts with date labels and value indicators
- [x] **API Endpoints**: Complete health analysis API with date range support
- [x] **Frontend Integration**: Full React component with navigation and visualization

---

## 🚧 **In Progress**

### 8. Agent-Based Architecture (Crew AI)
- [ ] Define agent roles and responsibilities:
  - Data Agent (download & store)
  - Processing Agent (extract, merge, process)
  - Analysis Agent (metrics, trends, recommendations)
  - UI Agent (prepare data for frontend)
- [ ] Implement agent workflows and communication
- [ ] Test agent-based task execution

---

## 📋 **Next Priority Tasks**

### Phase 1: Immediate Value
1. **Performance Management Chart (PMC)**
   - [ ] CTL (Chronic Training Load) calculation
   - [ ] ATL (Acute Training Load) calculation  
   - [ ] TSB (Training Stress Balance) calculation
   - [ ] PMC visualization in frontend

2. **Enhanced Health & Recovery Analysis**
   - [ ] Implement actual recovery status calculation (currently placeholder)
   - [ ] Implement actual readiness recommendations (currently placeholder)
   - [ ] Add more health metrics (stress, body battery, etc.)

3. **Training Planning & Recommendations**
   - [ ] Next week training suggestions
   - [ ] Generic training type repository
   - [ ] Macro cycle planning
   - [ ] Workout recommendations based on recovery status

### Phase 2: Advanced Features
4. **Multi-Athlete Support**
   - [ ] Coach-athlete relationship management
   - [ ] Team training insights
   - [ ] Comparative performance analysis

5. **Advanced Analytics**
   - [ ] Export functionality
   - [ ] Mobile responsiveness improvements
   - [ ] Advanced charts and visualizations
   - [ ] Training plan templates

### Phase 3: Technical Debt & Infrastructure
6. **Code Quality & Testing**
   - [ ] Remove local file storage completely
   - [ ] Complete `PUT /api/profile` endpoint implementation
   - [ ] Add proper error handling for missing athlete profiles
   - [ ] Improve frontend error states
   - [ ] Add comprehensive tests
   - [ ] Improve logging
   - [ ] Add API documentation
   - [ ] Performance optimization

---

## 🎯 **Current Status**

**✅ Completed Major Features:**
- Garmin Connect integration with 42-day historical data sync
- Health & Recovery Analysis with week navigation and visual analytics
- Workout management with week navigation
- Athlete profile and zone management
- Complete Docker containerization
- Database schema and data persistence
- Modern React frontend with responsive design

**🚧 Ready for Next Phase:**
- Performance Management Chart (PMC) implementation
- Enhanced training recommendations
- Advanced analytics and multi-athlete support

**📊 Data Status:**
- 41 sleep records (54-88 score range)
- 42 HRV records (weekly averages)
- 42 RHR records (37-43 bpm range)
- 74 workout records with TSS calculations 