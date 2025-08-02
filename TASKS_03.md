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

## 3  Recovery dashboard – intelligent summary agent

We'll create a new agent `recovery_analysis_agent.py` that synthesises sleep, HRV, RHR and training load to output **status**, **score 0-100**, and **recommendation**.

### 3.1  Data ingestion helpers
- [ ] Queries to collect last N-days of:
  ∘ `sleep` duration & quality  
  ∘ `hrv` (rmssd)  
  ∘ `rhr`  
  ∘ `training_status` (CTL, ATL, TSB)
- [ ] Normalise to daily records.

### 3.2  Heuristics / model
- **Baseline windows**: 30-day trailing average for each metric.
- **Deviation scoring**: z-score or % change vs baseline, weighted:
  • HRV (-)  • RHR (+)  • Sleep (-)  • TSB (+)
- Map combined score to status: `good ≥70`, `moderate 40-69`, `poor <40`.
- Provide explanation list (e.g., "HRV down 15%, RHR up 10 bpm").

### 3.3  Agent implementation
- Deterministic rules first; later swap to ML if desired.
- Function `analyze_recovery(athlete_id, range_days=14) -> dict`.
- Place in `agents/recovery_analysis_agent.py` with unit tests for edge cases.

### 3.4  API integration
1. Replace stub logic in `GET /api/health/recovery-status`, `/readiness`, `/analysis` to call the agent.
2. Response models unchanged (already defined in `api/main.py`).
3. Add integration test with seeded demo data.

### 3.5  Frontend
- Dashboard shows status icon (green / yellow / red), score, and bullet reasons.
- Add tooltip linking to underlying metrics.

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