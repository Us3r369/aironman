# TASKS – Phase 03 (July 2025)

This document decomposes the next feature set into concrete, testable tasks.  Follow the order unless there is a strong reason to work in parallel.  Each task lists the **definition of done (DoD)** so we can tick them off during PR review.

---

## 1  Profile editing & versioning ✅ **COMPLETE**

Goal: Users can edit their profile in the web-app. Each edit inserts a **new** row in `athlete_profile`; the most-recent row is treated as *active* for all calculations (TSS, zones, etc.)

### 1.1  Database ✅
- [x] Verify the table already has `valid_from` / `valid_to` columns and that previous rows are correctly closed ( `valid_to IS NOT NULL`).
- [x] Add an index on `(json_athlete_id, valid_to)` to speed up "active profile" look-ups (optional but recommended).
- [x] (If missing) Add a DB check-constraint ensuring that for a given athlete at most one profile has `valid_to IS NULL`.

### 1.2  Backend (FastAPI) ✅
1. **Refactor profile retrieval** ✅
   ∘ Create helper `get_active_profile(athlete_id)` in `utils/database.py` (or new module).  
   ∘ Replace *all* uses of `profile.json` in `services/preprocess.py`, `services/sync.py`, `agents/*` with the DB call.
2. **PUT /api/profile** ✅
   ∘ Already inserts a new row; audit for bugs (column/value mismatch, timezone issues).  
   ∘ After INSERT, close previous active row with `valid_to = now() - INTERVAL '1 second'` (already in place; add unit test).
3. **GET /api/profile/history** (nice-to-have) returns paginated list of previous profiles.
4. **Unit tests** ✅
   ∘ New insert sets exactly one active row.  
   ∘ TSS calculation uses latest profile.

### 1.3  Frontend (React) ✅
1. **ProfileEditForm** component  
   ∘ Pre-populate with data from `GET /api/profile`.  
   ∘ On submit -> `PUT /api/profile` → success toast.
2. **ZonesPreview** – show computed zones as the user edits values.
3. **Validation** – prevent impossible ranges, pace format, etc.
4. **E2E test** with Playwright: edit profile → reload → UI shows new data.

---

## 2  Workout view – metric selector (HR / Pace / Power) ✅ **COMPLETE**

### Implementation Plan

**Backend (API Layer)** ✅ **COMPLETE**
- [x] **New endpoint**: `GET /api/workouts/{id}/timeseries?metric=hr|pace|power`
  - Parse stored CSV/JSON data to extract time series ✅
  - For pace: convert GPS coordinates to pace (min/km) using distance calculations ✅
  - For power: extract from FIT/JSON power data if available ✅
  - Return: `[{timestamp: string, value: number, unit: string}]` ✅
  - Handle missing data gracefully (404 with clear message) ✅
  - **EXTENDED**: Supports 10 metrics (hr, pace, power, speed, cadence, run_cadence, altitude, form_power, air_power, distance) ✅

**Frontend (React)** ✅ **COMPLETE**
- [x] **MetricSelector component** (dropdown)
  - Options: "Heart Rate", "Pace", "Power" (plus 7 more) ✅
  - Default: "Heart Rate" ✅
  - State management: persist selection in URL query params ✅ **COMPLETE**
  - Styling: match existing design system ✅

- [x] **Enhanced LineChart component**
  - Accept metric data as prop ✅
  - Dynamic Y-axis labels based on metric type ✅
  - Color coding: HR=red, Pace=blue, Power=purple (plus 7 more) ✅
  - Handle data format changes (pace vs HR vs power units) ✅
  - Reuse existing chart library (SVG-based) ✅

- [x] **WorkoutDetail page integration**
  - Add MetricSelector above existing chart ✅
  - Fetch new timeseries data when metric changes ✅
  - Loading states during data fetch ✅
  - Error handling for unavailable metrics ✅

**Data Flow** ✅ **COMPLETE**
1. User selects metric from dropdown ✅
2. Frontend calls `/api/workouts/{id}/timeseries?metric={selected}` ✅
3. Backend processes stored workout data, returns time series ✅
4. Frontend updates chart with new data and styling ✅
5. URL updates with `?metric=pace` for deep linking ✅ **COMPLETE**

**Reuse Opportunities** ✅ **COMPLETE**
- Existing workout detail page structure ✅
- Current chart component (extend with new data format) ✅
- Error handling patterns from other API calls ✅
- Loading state components ✅
- URL parameter management utilities ✅ **COMPLETE**

### 2.1  Backend ✅ **COMPLETE**
- [x] Add endpoint `GET /api/workouts/{id}/timeseries?metric=hr|pace|power` returning `[ {timestamp,value} ]`  
  ∘ Derive pace (min/km) and power (W) from stored CSV/JSON. ✅
  ∘ If metric unavailable, return 404 with clear message. ✅
  ∘ **EXTENDED**: Supports 10 metrics for comprehensive workout analysis ✅

### 2.2  Frontend ✅ **COMPLETE**
1. **MetricSelector** dropdown (default "Heart Rate") ✅
2. **LineChart** updates when selector changes. Use color coding: ✅
   • HR = red  • Pace = blue  • Power = purple (plus 7 more) ✅
3. Persist selection in URL query (?metric=pace) for deep-links. ✅ **COMPLETE**
4. Unit test: selector switches dataset & y-axis label. ✅ **COMPLETE**

### **Remaining Work:** ✅ **ALL COMPLETE**
- [x] **URL Persistence**: Add URL query parameter management for metric selection ✅
- [x] **Unit Tests**: Add tests for metric selector functionality ✅
- [x] **Deep Linking**: Enable bookmarking/sharing specific metric views ✅

---

## 3  Recovery dashboard – intelligent agent analysis

**Goal**: Replace static recovery analysis with an intelligent CrewAI agent that analyzes RHR, HRV, sleep, and training load to provide dynamic status, detailed reasoning, and recommendations.

### 3.1  Database Schema
- [ ] Create `daily_recovery_analysis` table:
  ```sql
  CREATE TABLE daily_recovery_analysis (
      id SERIAL PRIMARY KEY,
      athlete_id UUID REFERENCES athlete(id),
      analysis_date DATE NOT NULL,
      status VARCHAR(10) NOT NULL, -- 'good', 'medium', 'bad'
      detailed_reasoning TEXT NOT NULL,
      agent_analysis JSONB, -- Store full agent response
      created_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(athlete_id, analysis_date)
  );
  ```
- [ ] Add database migration file `005_create_recovery_analysis.sql`
- [ ] Add indices for performance: `(athlete_id, analysis_date)`

### 3.2  Agent Infrastructure (CrewAI) ✅ **COMPLETE**
- [x] Install CrewAI dependencies in `requirements.txt`
- [x] Create `agents/recovery_analysis_agent.py` with:
  - **Recovery Analysis Agent**: Main agent for analysis ✅
  - **Health Metrics Tool**: Extract RHR, HRV, sleep data (3-7 day trends) ✅
  - **Training Load Tool**: Extract TSB, CTL, ATL data ✅
  - **Trend Analysis Tool**: Analyze patterns and flag acute spikes/drops ✅
  - **Recovery Assessment Tool**: Generate status and detailed reasoning ✅
- [x] Agent logic:
  - Use TSB for load management context ✅
  - Analyze 3-7 day trends in HRV, sleep, RHR for readiness scoring ✅
  - Flag acute spikes/drops as warning signals ✅
  - Generate status: `good`/`medium`/`bad` ✅
  - Provide detailed reasoning with specific insights ✅

### 3.3  Backend API
- [ ] **New endpoint**: `POST /api/health/agent-analysis`
  - Triggers agent analysis for current athlete
  - Returns: `{status, detailed_reasoning, analysis_date, last_updated}`
  - Store result in `daily_recovery_analysis` table
- [ ] **Updated endpoint**: `GET /api/health/analysis`
  - Return latest agent analysis from database
  - Include `last_updated` timestamp
  - Fallback to static analysis if no agent data available
- [ ] **Agent execution function**: `execute_recovery_analysis(athlete_id)`
  - Call CrewAI agent with athlete data
  - Handle errors gracefully
  - Return structured response

### 3.4  Frontend Integration ✅ **COMPLETE**
- [x] **Combined Recovery Status Card** (top center of health page):
  - Merge current `RecoveryStatusCard` and `ReadinessCard` into single component ✅
  - Display: status (good/medium/bad), detailed reasoning, last updated timestamp ✅
  - Add refresh button to trigger new agent analysis ✅
  - Show loading state during agent execution ✅
- [x] **Agent Analysis Display**:
  - Show detailed reasoning from agent ✅
  - Display status with appropriate color coding ✅
  - Show "Last updated: [timestamp]" with refresh button ✅
- [x] **Error Handling**:
  - Handle agent execution failures gracefully ✅
  - Show fallback to static analysis if needed ✅
  - Display user-friendly error messages ✅

### 3.5  Data Analysis Requirements ✅ **COMPLETE**
- [x] **Enhanced Health Metrics Analysis**:
  - RHR trends (3-7 days): Flag increases as negative with severity levels ✅
  - HRV trends (3-7 days): Flag decreases as negative with severity levels ✅
  - Sleep quality trends (3-7 days): Flag decreases as negative with severity levels ✅
  - Data quality assessment: Poor/moderate/good based on data points ✅
  - Acute spike/drop detection: Enhanced with severity levels ✅
- [x] **Enhanced Training Load Context**:
  - TSB analysis: Recovery (>10), Balanced (0-10), Moderate stress (<0), High stress (<-10) ✅
  - Load assessment: Recovery, balanced, moderate_stress, high_stress ✅
  - Recent TSS tracking: Total TSS and workout count ✅
  - Load context: Detailed TSB, CTL, ATL analysis ✅
- [x] **Enhanced Agent Reasoning**:
  - Specific insights: "Your RHR is high and sleep was poor, so yellow status" ✅
  - Trend analysis: Detailed percentage changes and recommendations ✅
  - Comprehensive reasoning: Status + factors + recommendations + trend-specific advice ✅
  - Enhanced scoring: More nuanced scoring system (60+ good, 30+ medium, <30 bad) ✅

### 3.6  Testing & Validation ✅ **COMPLETE**
- [x] **Unit Tests**:
  - Agent tests: Test all CrewAI tools and agent execution ✅
  - API tests: Test all FastAPI endpoints with TestClient ✅
  - Database tests: Test database utilities and connection handling ✅
  - Service tests: Test PMC metrics, zones, sync, preprocessing ✅
  - Error handling tests: Test exception scenarios ✅
- [x] **Integration Tests**:
  - End-to-end API testing with mocked dependencies ✅
  - Database integration testing with mocked connections ✅
  - Agent execution testing with mocked CrewAI responses ✅
- [x] **Test Infrastructure**:
  - pytest configuration with coverage reporting ✅
  - Pre-commit hooks for automated testing ✅
  - Comprehensive test runner script ✅
  - Test documentation and examples ✅
- [x] **Code Quality**:
  - Black formatting with 88 character line length ✅
  - isort import sorting ✅
  - flake8 linting with custom rules ✅
  - bandit security scanning ✅
  - 80%+ coverage requirement ✅

---

## 4  Cross-cutting

- [ ] Update OpenAPI docs & README examples.
- [ ] Docker: ensure new dependencies added to `requirements.txt` & images rebuild cleanly.
- [ ] CI: expand test matrix, ensure coverage ≥ 90% for new code.

---

**Release checklist**
1. All tasks green ✅
2. `make test` passes
3. `docker-compose up` starts and manual smoke tests succeed
4. Tag release `v0.3.0` and push 