import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import "./App.css";

function Sidebar({ selectedItem, onItemSelect }) {
  return (
    <div className="sidebar">
      <div className="sidebar-title">AIronman</div>
      <ul>
        <li 
          className={`sidebar-item ${selectedItem === 'pmc' ? 'active' : ''}`}
          onClick={() => onItemSelect('pmc')}
        >
          Performance Chart
        </li>
        <li 
          className={`sidebar-item ${selectedItem === 'sync' ? 'active' : ''}`}
          onClick={() => onItemSelect('sync')}
        >
          Sync Data
        </li>
        <li 
          className={`sidebar-item ${selectedItem === 'profile' ? 'active' : ''}`}
          onClick={() => onItemSelect('profile')}
        >
          View Profile
        </li>
        <li
          className={`sidebar-item ${selectedItem === 'workouts' ? 'active' : ''}`}
          onClick={() => onItemSelect('workouts')}
        >
          Workouts
        </li>
        <li
          className={`sidebar-item ${selectedItem === 'plan' ? 'active' : ''}`}
          onClick={() => onItemSelect('plan')}
        >
          Training Plan
        </li>
        <li
          className={`sidebar-item ${selectedItem === 'health' ? 'active' : ''}`}
          onClick={() => onItemSelect('health')}
        >
          Health & Recovery
        </li>
      </ul>
    </div>
  );
}

function ZoneCard({ title, threshold, zones, unit, testDate, testLabel, onEdit, showEdit, editData, onCloseEdit, onSave, saving, saveError }) {
  const [showEditModal, setShowEditModal] = useState(false);
  const [editThreshold, setEditThreshold] = useState(threshold);
  const [editZones, setEditZones] = useState(zones);
  const [editTestDate, setEditTestDate] = useState(testDate || "");

  useEffect(() => {
    if (showEdit) {
      setEditThreshold(editData?.threshold ?? threshold);
      setEditZones(editData?.zones ?? zones);
      setEditTestDate((editData?.testDate ?? testDate) || "");
      setShowEditModal(true);
    } else {
      setShowEditModal(false);
    }
  }, [showEdit, editData, threshold, zones, testDate]);

  // Prevent background scroll when modal is open
  useEffect(() => {
    if (showEditModal) {
      document.body.classList.add('modal-open');
    } else {
      document.body.classList.remove('modal-open');
    }
    return () => {
      document.body.classList.remove('modal-open');
    };
  }, [showEditModal]);

  const handleZoneChange = (zoneName, idx, value) => {
    setEditZones(prev => {
      const updated = { ...prev };
      if (Array.isArray(updated[zoneName])) {
        const arr = [...updated[zoneName]];
        arr[idx] = value;
        updated[zoneName] = arr;
      } else {
        updated[zoneName] = value;
      }
      return updated;
    });
  };

  const isValidDate = (str) => /^\d{4}-\d{2}-\d{2}$/.test(str);

  const handleSaveClick = () => {
    if (onSave) {
      onSave(editThreshold, editZones, editTestDate);
    }
  };

  return (
    <div className="zone-card">
      <h3 className="zone-title">{title}</h3>
      {threshold && (
        <div className="threshold">
          <span className="threshold-label">Threshold:</span>
          <span className="threshold-value">{threshold} {unit}</span>
        </div>
      )}
      {testDate && (
        <div className="test-date-inline">
          <span className="test-label">{testLabel}:</span>
          <span className="test-date">{testDate}</span>
        </div>
      )}
      <div className="zones-grid">
        {Object.entries(zones).map(([zoneName, zoneRange]) => (
          <div key={zoneName} className="zone-item">
            <div className="zone-name">{zoneName.toUpperCase()}</div>
            <div className="zone-range">
              {Array.isArray(zoneRange) ? zoneRange.join(' - ') : zoneRange}
            </div>
          </div>
        ))}
      </div>
      <button className="edit-btn" onClick={onEdit}>Edit</button>
      {showEditModal && ReactDOM.createPortal(
        <div className="edit-modal">
          <div className="edit-modal-content">
            <button className="close-btn" onClick={onCloseEdit}>&times;</button>
            <h3 className="zone-title">{title} (Edit Mode)</h3>
            {threshold && (
              <div className="threshold">
                <span className="threshold-label">Threshold:</span>
                <input
                  className="edit-input"
                  value={editThreshold}
                  onChange={e => setEditThreshold(e.target.value)}
                  style={{ width: 80, marginLeft: 8, marginRight: 8 }}
                />
                <span className="threshold-value">{unit}</span>
              </div>
            )}
            {testDate && (
              <div className="test-date-inline">
                <span className="test-label">{testLabel}:</span>
                {isValidDate(editTestDate) ? (
                  <input
                    className="edit-input"
                    type="date"
                    value={editTestDate}
                    onChange={e => setEditTestDate(e.target.value)}
                    style={{ width: 140 }}
                  />
                ) : (
                  <input
                    className="edit-input"
                    type="text"
                    value={editTestDate}
                    onChange={e => setEditTestDate(e.target.value)}
                    style={{ width: 140 }}
                  />
                )}
              </div>
            )}
            <div className="zones-grid">
              {Object.entries(editZones).map(([zoneName, zoneRange]) => (
                <div key={zoneName} className="zone-item">
                  <div className="zone-name">{zoneName.toUpperCase()}</div>
                  <div className="zone-range">
                    {Array.isArray(zoneRange)
                      ? zoneRange.map((val, idx) => (
                          <input
                            key={idx}
                            className="edit-input"
                            value={val}
                            onChange={e => handleZoneChange(zoneName, idx, e.target.value)}
                            style={{ width: 60, margin: '0 4px' }}
                          />
                        ))
                      : (
                          <input
                            className="edit-input"
                            value={zoneRange}
                            onChange={e => handleZoneChange(zoneName, 0, e.target.value)}
                            style={{ width: 80 }}
                          />
                        )}
                  </div>
                </div>
              ))}
            </div>
            {saveError && (
              <div className="error-message" style={{ marginTop: 16 }}>
                <p>{saveError}</p>
              </div>
            )}
            <div className="edit-actions">
              <button className="save-btn" onClick={handleSaveClick} disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
              <button className="cancel-btn" onClick={onCloseEdit} disabled={saving}>Cancel</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

function SyncData() {
  const [isLoading, setIsLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleSync = async () => {
    setIsLoading(true);
    setError(null);
    setSyncStatus(null);
    
    try {
      const response = await fetch('http://localhost:8000/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setSyncStatus({
        message: 'Sync completed successfully!',
        timestamp: new Date().toLocaleString(),
        details: result
      });
    } catch (err) {
      setError(`Sync failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="sync-container">
      <h2>Sync Garmin Data</h2>
      <p>Download the latest workouts and health metrics from Garmin Connect.</p>
      
      <button 
        className={`sync-button ${isLoading ? 'loading' : ''}`}
        onClick={handleSync}
        disabled={isLoading}
      >
        {isLoading ? 'Syncing...' : 'Start Sync'}
      </button>

      {error && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {syncStatus && (
        <div className="success-message">
          <h3>Sync Complete</h3>
          <p>{syncStatus.message}</p>
          <p><strong>Time:</strong> {syncStatus.timestamp}</p>
          {syncStatus.details && (
            <div className="sync-details">
              <h4>Details:</h4>
              <pre>{JSON.stringify(syncStatus.details, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      <div className="sync-info">
        <h3>What gets synced:</h3>
        <ul>
          <li>Workouts (bike, run, swim, strength)</li>
          <li>Health metrics (sleep, HRV, resting heart rate)</li>
          <li>Activity files (.fit, .tcx, .gpx, .csv)</li>
        </ul>
      </div>
    </div>
  );
}

function ViewProfile() {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [editCard, setEditCard] = useState(null); // which card is being edited
  const [editData, setEditData] = useState(null); // { threshold, zones, testDate, testLabel, cardKey }

  // Fetch profile
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/profile');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setProfile(data);
      } catch (err) {
        setError(`Failed to load profile: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, [saving]);

  // Handler to open modal for a card
  const handleEdit = (cardKey, threshold, zones, testDate, testLabel) => {
    setEditCard(cardKey);
    setEditData({ threshold, zones, testDate, testLabel });
  };

  // Handler to close modal
  const handleCloseEdit = () => {
    setEditCard(null);
    setEditData(null);
    setSaveError(null);
  };

  // Handler to save changes
  const handleSave = async (newThreshold, newZones, newTestDate) => {
    if (!profile) return;
    setSaving(true);
    setSaveError(null);
    // Build updated profile object
    let updatedProfile = JSON.parse(JSON.stringify(profile));
    if (editCard === 'heart_rate') {
      updatedProfile.zones.heart_rate.lt_hr = newThreshold;
      updatedProfile.zones.heart_rate.zones = newZones;
    } else if (editCard === 'bike_power') {
      updatedProfile.zones.bike_power.ftp = newThreshold;
      updatedProfile.zones.bike_power.zones = newZones;
      updatedProfile.test_dates.bike_ftp_test = newTestDate;
    } else if (editCard === 'run_power') {
      const [ltp, cp] = String(newThreshold).split('/').map(x => x.trim());
      updatedProfile.zones.run_power.ltp = ltp;
      updatedProfile.zones.run_power.critical_power = cp;
      updatedProfile.zones.run_power.zones = newZones;
      updatedProfile.test_dates.run_ltp_test = newTestDate;
    } else if (editCard === 'run_pace') {
      updatedProfile.zones.run_pace.threshold_pace_per_km = newThreshold;
      updatedProfile.zones.run_pace.zones = newZones;
      updatedProfile.test_dates.run_ltp_test = newTestDate;
    } else if (editCard === 'swim') {
      updatedProfile.zones.swim.css_pace_per_100m = newThreshold;
      updatedProfile.zones.swim.zones = newZones;
      updatedProfile.test_dates.swim_css_test = newTestDate;
    }
    // Set last_updated to now
    updatedProfile.last_updated = new Date().toISOString().slice(0, 10);
    try {
      const response = await fetch('http://localhost:8000/api/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedProfile),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setProfile(updatedProfile);
      handleCloseEdit();
    } catch (err) {
      setSaveError(`Failed to save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="profile-container">
        <div className="loading-spinner">Loading profile...</div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="profile-container">
        <div className="error-message">
          <h3>Error Loading Profile</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }
  if (!profile) {
    return (
      <div className="profile-container">
        <div className="error-message">
          <h3>No Profile Found</h3>
          <p>No athlete profile data is available.</p>
        </div>
      </div>
    );
  }

  // Helper to render a ZoneCard with edit modal
  const renderZoneCard = (cardKey, title, threshold, zones, unit, testDate, testLabel) => (
    <ZoneCard
      title={title}
      threshold={threshold}
      zones={zones}
      unit={unit}
      testDate={testDate}
      testLabel={testLabel}
      onEdit={() => handleEdit(cardKey, threshold, zones, testDate, testLabel)}
      showEdit={editCard === cardKey}
      editData={editData}
      onCloseEdit={handleCloseEdit}
      onSave={handleSave}
      saving={saving}
      saveError={saveError}
    />
  );

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h2>Athlete Profile</h2>
        <div className="profile-meta">
          <span className="athlete-id">Athlete: {profile.athlete_id}</span>
          <span className="last-updated">Last Updated: {profile.last_updated}</span>
        </div>
      </div>
      <div className="zones-grid-container">
        {renderZoneCard('heart_rate', 'Heart Rate Zones', profile.zones.heart_rate.lt_hr, profile.zones.heart_rate.zones, 'bpm')}
        {renderZoneCard('bike_power', 'Bike Power Zones', profile.zones.bike_power.ftp, profile.zones.bike_power.zones, 'watts', profile.test_dates?.bike_ftp_test, 'Bike FTP Test')}
        {renderZoneCard('run_power', 'Run Power Zones', `${profile.zones.run_power.ltp} / ${profile.zones.run_power.critical_power}`, profile.zones.run_power.zones, 'watts', profile.test_dates?.run_ltp_test, 'Run LTP Test')}
        {renderZoneCard('run_pace', 'Run Pace Zones', profile.zones.run_pace.threshold_pace_per_km, profile.zones.run_pace.zones, 'per km', profile.test_dates?.run_ltp_test, 'Run LTP Test')}
        {renderZoneCard('swim', 'Swim Zones', profile.zones.swim.css_pace_per_100m, profile.zones.swim.zones, 'per 100m', profile.test_dates?.swim_css_test, 'Swim CSS Test')}
      </div>
    </div>
  );
}

// Calendar utility: get dates for any week (Monday-Sunday)
function getMonthDates(monthOffset = 0) {
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth();
  
  // Calculate target month
  const targetYear = currentYear + Math.floor((currentMonth + monthOffset) / 12);
  const targetMonth = (currentMonth + monthOffset) % 12;
  
  // Get first day of the month
  const firstDay = new Date(targetYear, targetMonth, 1);
  const lastDay = new Date(targetYear, targetMonth + 1, 0);
  
  // Get the day of week for first day (0 = Sunday)
  const firstDayOfWeek = firstDay.getDay();
  
  // Calculate start date (previous month's days to fill first week)
  const startDate = new Date(firstDay);
  startDate.setDate(1 - firstDayOfWeek);
  
  // Calculate end date (next month's days to fill last week)
  const endDate = new Date(lastDay);
  const lastDayOfWeek = lastDay.getDay();
  endDate.setDate(lastDay.getDate() + (6 - lastDayOfWeek));
  
  // Generate all dates for the calendar
  const dates = [];
  const currentDate = new Date(startDate);
  
  while (currentDate <= endDate) {
    dates.push(new Date(currentDate));
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  return {
    dates,
    year: targetYear,
    month: targetMonth,
    monthName: firstDay.toLocaleDateString('en-US', { month: 'long' })
  };
}

// Get current month dates (for backward compatibility)
function getCurrentMonthDates() {
  return getMonthDates(0);
}

function WorkoutsView() {
  const [workouts, setWorkouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWorkout, setSelectedWorkout] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);
  const [workoutDetail, setWorkoutDetail] = useState(null);
  const [athleteId, setAthleteId] = useState("");
  const [monthOffset, setMonthOffset] = useState(0);
  const [zoneData, setZoneData] = useState(null);
  const [zoneLoading, setZoneLoading] = useState(false);
  const [zoneDefinitions, setZoneDefinitions] = useState(null);
  const [zoneDefsLoading, setZoneDefsLoading] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState("hr");
  const [availableMetrics, setAvailableMetrics] = useState(["hr"]);
  const [metricLoading, setMetricLoading] = useState(false);

  // URL query parameter management - only for workouts context
  const updateWorkoutURL = (workoutId, metric) => {
    const url = new URL(window.location);
    // Only update workout-specific parameters, preserve other navigation state
    if (workoutId) {
      url.searchParams.set('workout', workoutId);
    } else {
      url.searchParams.delete('workout');
    }
    if (metric) {
      url.searchParams.set('metric', metric);
    } else {
      url.searchParams.delete('metric');
    }
    window.history.replaceState({}, '', url);
  };

  const getWorkoutURLParams = () => {
    const url = new URL(window.location);
    return {
      workoutId: url.searchParams.get('workout'),
      metric: url.searchParams.get('metric') || 'hr'
    };
  };

  // Initialize from URL on component mount
  useEffect(() => {
    const { workoutId, metric } = getWorkoutURLParams();
    if (workoutId && workoutId !== selectedWorkout) {
      setSelectedWorkout(workoutId);
    }
    if (metric && metric !== selectedMetric) {
      setSelectedMetric(metric);
    }
  }, []);

  // Update URL when workout or metric changes
  useEffect(() => {
    updateWorkoutURL(selectedWorkout, selectedMetric);
  }, [selectedWorkout, selectedMetric]);

  // Handle metric change with URL update
  const handleMetricChange = (newMetric) => {
    setSelectedMetric(newMetric);
    updateWorkoutURL(selectedWorkout, newMetric);
  };

  // Handle workout selection with URL update
  const handleWorkoutSelect = (workoutId) => {
    setSelectedWorkout(workoutId);
    updateWorkoutURL(workoutId, selectedMetric);
  };

  // Handle workout close with URL update
  const handleWorkoutClose = () => {
    setSelectedWorkout(null);
    updateWorkoutURL(null, selectedMetric);
  };

  // Fetch athleteId from profile (assume single athlete for now)
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/profile');
        if (!response.ok) throw new Error('Failed to fetch profile');
        const data = await response.json();
        setAthleteId(data.athlete_id);
      } catch (err) {
        setError('Failed to load athlete profile');
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  // Fetch workouts for selected month
  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    setError(null);
    const month = getMonthDates(monthOffset);
    const start = month.dates[0].toISOString().slice(0, 10);
    const end = month.dates[month.dates.length - 1].toISOString().slice(0, 10);
    fetch(`http://localhost:8000/api/workouts?athlete_id=${athleteId}&start_date=${start}&end_date=${end}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch workouts');
        return res.json();
      })
      .then(data => {
        setWorkouts(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [athleteId, monthOffset]);

  // Fetch zone definitions when athleteId is available
  useEffect(() => {
    if (!athleteId) return;
    setZoneDefsLoading(true);
    fetch(`http://localhost:8000/api/athlete/${athleteId}/zones`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch zone definitions');
        return res.json();
      })
      .then(data => {
        setZoneDefinitions(data);
        setZoneDefsLoading(false);
      })
      .catch(err => {
        console.warn('Zone definitions not available:', err.message);
        setZoneDefsLoading(false);
      });
  }, [athleteId]);

  // Fetch workout detail when selected
  useEffect(() => {
    if (!selectedWorkout) return;
    setDetailLoading(true);
    setDetailError(null);
    setWorkoutDetail(null);
    setZoneData(null);
    
    // Fetch workout detail
    fetch(`http://localhost:8000/api/workouts/${selectedWorkout}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch workout detail');
        return res.json();
      })
      .then(data => {
        setWorkoutDetail(data);
        setDetailLoading(false);
        
        // Fetch available metrics for this workout
        setMetricLoading(true);
        fetch(`http://localhost:8000/api/workouts/${selectedWorkout}/timeseries?metric=hr`)
          .then(res => {
            if (res.ok) {
              return res.json();
            }
            throw new Error('Failed to fetch available metrics');
          })
          .then(data => {
            setAvailableMetrics(data.available_metrics);
            // Set default metric to first available
            if (data.available_metrics.length > 0 && !data.available_metrics.includes(selectedMetric)) {
              setSelectedMetric(data.available_metrics[0]);
            }
            setMetricLoading(false);
          })
          .catch(err => {
            console.warn('Could not determine available metrics:', err.message);
            setAvailableMetrics(["hr"]);
            setMetricLoading(false);
          });
        
        // Fetch zone data for bike and run workouts
        if (data.workout_type === 'bike' || data.workout_type === 'run') {
          setZoneLoading(true);
          fetch(`http://localhost:8000/api/workouts/${selectedWorkout}/zones`)
            .then(res => {
              if (!res.ok) throw new Error('Failed to fetch zone data');
              return res.json();
            })
            .then(zoneData => {
              setZoneData(zoneData);
              setZoneLoading(false);
            })
            .catch(err => {
              console.warn('Zone data not available:', err.message);
              setZoneLoading(false);
            });
        }
      })
      .catch(err => {
        setDetailError(err.message);
        setDetailLoading(false);
      });
  }, [selectedWorkout]);

  const month = getMonthDates(monthOffset);
  // Group workouts by date (YYYY-MM-DD)
  const workoutsByDate = {};
  workouts.forEach(w => {
    const date = w.timestamp.slice(0, 10);
    if (!workoutsByDate[date]) workoutsByDate[date] = [];
    workoutsByDate[date].push(w);
  });

  // Navigation functions
  const goToPreviousMonth = () => setMonthOffset(prev => prev - 1);
  const goToNextMonth = () => setMonthOffset(prev => prev + 1);
  const goToCurrentMonth = () => setMonthOffset(0);

  const formatMonthDisplay = () => {
    return month.monthName + ' ' + month.year;
  };

  return (
    <div className="workouts-container">
      <div className="workouts-header">
        <h2>Workouts</h2>
        <div className="month-navigation">
          <button onClick={goToPreviousMonth}>&lt; Previous Month</button>
          <button onClick={goToCurrentMonth} className="current-btn">Current Month</button>
          <button onClick={goToNextMonth}>Next Month &gt;</button>
        </div>
        <div className="month-display">{formatMonthDisplay()}</div>
      </div>
      {loading ? (
        <div className="loading-spinner">Loading workouts...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <table className="calendar-table">
          <thead>
            <tr>
              <th>Sun</th>
              <th>Mon</th>
              <th>Tue</th>
              <th>Wed</th>
              <th>Thu</th>
              <th>Fri</th>
              <th>Sat</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: Math.ceil(month.dates.length / 7) }, (_, weekIndex) => (
              <tr key={weekIndex}>
                {Array.from({ length: 7 }, (_, dayIndex) => {
                  const dateIndex = weekIndex * 7 + dayIndex;
                  const date = month.dates[dateIndex];
                  if (!date) return <td key={dayIndex} className="calendar-cell empty"></td>;
                  
                  const dateStr = date.toISOString().slice(0, 10);
                  const dayWorkouts = workoutsByDate[dateStr] || [];
                  const isCurrentMonth = date.getMonth() === month.month;
                  const isToday = date.toDateString() === new Date().toDateString();
                  
                  return (
                    <td key={dayIndex} className={`calendar-cell ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}>
                      <div className="date-number">{date.getDate()}</div>
                      {dayWorkouts.length === 0 ? (
                        <span className="no-workout">-</span>
                      ) : (
                        <ul className="workout-list">
                          {dayWorkouts.map(w => (
                            <li
                              key={w.id}
                              className={`workout-item ${w.planned ? 'planned' : ''}`}
                              onClick={w.planned ? undefined : () => handleWorkoutSelect(w.id)}
                            >
                              <span className="workout-type">{w.workout_type}</span>
                              {w.planned && <span className="planned-label">planned</span>}
                              {w.description && (
                                <span className="workout-desc">{w.description}</span>
                              )}
                              {w.tss !== null && <span className="workout-tss">TSS: {w.tss}</span>}
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {/* Workout detail modal */}
      {selectedWorkout && (
        <div className="workout-modal-overlay" onClick={handleWorkoutClose}>
          <div className="workout-modal" onClick={e => e.stopPropagation()}>
            <button className="close-btn" onClick={handleWorkoutClose}>&times;</button>
            {detailLoading ? (
              <div className="loading-spinner">Loading workout...</div>
            ) : detailError ? (
              <div className="error-message">{detailError}</div>
            ) : workoutDetail ? (
              <div>
                <h3>Workout Details</h3>
                <div><b>Type:</b> {workoutDetail.workout_type}</div>
                <div><b>Date:</b> {workoutDetail.timestamp}</div>
                <div><b>TSS:</b> {workoutDetail.tss}</div>
                
                {/* Metric Selector and Chart */}
                {workoutDetail.json_file && workoutDetail.json_file.data && Array.isArray(workoutDetail.json_file.data) && (
                  <div>
                    {metricLoading ? (
                      <div className="loading-spinner">Loading available metrics...</div>
                    ) : (
                      <>
                        <MetricSelector
                          selectedMetric={selectedMetric}
                          onMetricChange={handleMetricChange}
                          availableMetrics={availableMetrics}
                          workoutType={workoutDetail.workout_type}
                        />
                        <WorkoutChart
                          workoutId={selectedWorkout}
                          selectedMetric={selectedMetric}
                          availableMetrics={availableMetrics}
                          zoneData={zoneData}
                          workoutType={workoutDetail.workout_type}
                          zoneDefinitions={zoneDefinitions}
                        />
                      </>
                    )}
                  </div>
                )}
                
                {/* Tabular data for workouts without chart visualization or when no heart rate data */}
                {((!['bike', 'run', 'swim'].includes(workoutDetail.workout_type)) || 
                  !workoutDetail.json_file?.data?.some(d => d.heart_rate)) && 
                 workoutDetail.json_file && workoutDetail.json_file.data && Array.isArray(workoutDetail.json_file.data) && (
                  <div className="workout-table-container">
                    <h4>Data Points</h4>
                    <table className="workout-detail-table">
                      <thead>
                        <tr>
                          {Object.keys(workoutDetail.json_file.data[0]).map(key => (
                            <th key={key}>{key}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {workoutDetail.json_file.data.slice(0, 20).map((row, idx) => (
                          <tr key={idx}>
                            {Object.values(row).map((val, i) => (
                              <td key={i}>{val}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {workoutDetail.json_file.data.length > 20 && <div>Showing first 20 rows...</div>}
                  </div>
                )}
                
                {/* Pretty-printed JSON for the full json_file - only show for workouts without chart visualization */}
                {workoutDetail.json_file && 
                 !['bike', 'run', 'swim'].includes(workoutDetail.workout_type) && (
                   <div className="json-file-block">
                     <h4>Raw JSON</h4>
                     <pre style={{ maxHeight: 300, overflow: 'auto', background: '#f8f8f8', border: '1px solid #ccc', padding: 8 }}>
                       {JSON.stringify(workoutDetail.json_file, null, 2)}
                     </pre>
                   </div>
                 )}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

function TrainingPlanDesigner() {
  const [raceDate, setRaceDate] = useState("");
  const [raceType, setRaceType] = useState("marathon");
  const [workoutsPerWeek, setWorkoutsPerWeek] = useState(4);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      const profileRes = await fetch("http://localhost:8000/api/profile");
      if (!profileRes.ok) throw new Error("Failed to load profile");
      const profile = await profileRes.json();

      const res = await fetch("http://localhost:8000/api/training-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          athlete_id: profile.athlete_id,
          race_date: raceDate,
          race_type: raceType,
          max_workouts_per_week: Number(workoutsPerWeek)
        })
      });
      if (res.ok) {
        setMessage("Training plan created.");
      } else {
        setMessage("Failed to create plan.");
      }
    } catch (err) {
      setMessage("Error: " + err.message);
    }
  };

  return (
    <div className="training-plan-container">
      <h2>Training Plan Designer</h2>
      <form onSubmit={handleSubmit} className="training-plan-form">
        <label>
          Race Date:
          <input type="date" value={raceDate} onChange={e => setRaceDate(e.target.value)} required />
        </label>
        <label>
          Race Type:
          <select value={raceType} onChange={e => setRaceType(e.target.value)}>
            <option value="marathon">Running Marathon</option>
            <option value="ironman">Triathlon Ironman</option>
          </select>
        </label>
        <label>
          Workouts per Week:
          <input type="number" min="1" max="14" value={workoutsPerWeek} onChange={e => setWorkoutsPerWeek(e.target.value)} />
        </label>
        <button type="submit">Generate Plan</button>
      </form>
      {message && <div className="plan-message">{message}</div>}
    </div>
  );
}

// Metric Selector Component
function MetricSelector({ selectedMetric, onMetricChange, availableMetrics, workoutType }) {
  const metricOptions = [
    { value: "hr", label: "Heart Rate", color: "#ef4444" },
    { value: "pace", label: "Pace", color: "#3b82f6" },
    { value: "power", label: "Power", color: "#8b5cf6" },
    { value: "speed", label: "Speed", color: "#10b981" },
    { value: "cadence", label: "Cadence", color: "#f59e0b" },
    { value: "run_cadence", label: "Run Cadence", color: "#f59e0b" },
    { value: "altitude", label: "Altitude", color: "#6366f1" },
    { value: "form_power", label: "Form Power", color: "#ec4899" },
    { value: "air_power", label: "Air Power", color: "#8b5cf6" },
    { value: "distance", label: "Distance", color: "#06b6d4" }
  ];
  
  // Filter options based on workout type and available metrics
  const availableOptions = metricOptions.filter(option => {
    if (workoutType === "swim" && option.value === "run_cadence") return false;
    if (workoutType === "bike" && option.value === "run_cadence") return false;
    if (workoutType === "run" && option.value === "cadence") return false;
    if (workoutType === "swim" && (option.value === "form_power" || option.value === "air_power")) return false;
    if (workoutType === "bike" && (option.value === "form_power" || option.value === "air_power")) return false;
    return availableMetrics.includes(option.value);
  });
  
  if (availableOptions.length <= 1) return null;
  
  return (
    <div className="metric-selector">
      <label htmlFor="metric-select">Metric:</label>
      <select
        id="metric-select"
        value={selectedMetric}
        onChange={(e) => onMetricChange(e.target.value)}
        className="metric-dropdown"
      >
        {availableOptions.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

// Enhanced Workout Chart Component (renamed from HeartRatePlot)
function WorkoutChart({ workoutId, selectedMetric, availableMetrics, zoneData, workoutType, zoneDefinitions }) {
  const [timeseriesData, setTimeseriesData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hoverData, setHoverData] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  
  // Fetch timeseries data when metric changes
  useEffect(() => {
    if (!workoutId || !selectedMetric) return;
    
    setLoading(true);
    setError(null);
    
    fetch(`http://localhost:8000/api/workouts/${workoutId}/timeseries?metric=${selectedMetric}`)
      .then(res => {
        if (!res.ok) {
          if (res.status === 404) {
            throw new Error(`No ${selectedMetric} data available for this workout`);
          }
          throw new Error('Failed to fetch timeseries data');
        }
        return res.json();
      })
      .then(data => {
        setTimeseriesData(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [workoutId, selectedMetric]);
  
  if (loading) {
    return <div className="loading-spinner">Loading {selectedMetric} data...</div>;
  }
  
  if (error) {
    return <div className="error-message">{error}</div>;
  }
  
  if (!timeseriesData || timeseriesData.data.length < 2) {
    return <div className="no-data">No {selectedMetric} data available</div>;
  }
  
  const data = timeseriesData.data;
  const width = 800;
  const height = 400;
  const margin = { top: 40, right: 60, bottom: 80, left: 100 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  
  // Calculate scales based on metric
  const values = data.map(d => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valueRange = maxValue - minValue;
  
  const scaleY = (value) => margin.top + plotHeight - ((value - minValue) / valueRange) * plotHeight;
  const scaleX = (index) => margin.left + (index / (data.length - 1)) * plotWidth;
  
  // Metric-specific styling
  const getMetricStyle = () => {
    const styles = {
      hr: { color: "#ef4444", label: "Heart Rate" },
      pace: { color: "#3b82f6", label: "Pace" },
      power: { color: "#8b5cf6", label: "Power" },
      speed: { color: "#10b981", label: "Speed" },
      cadence: { color: "#f59e0b", label: "Cadence" },
      run_cadence: { color: "#f59e0b", label: "Run Cadence" },
      altitude: { color: "#6366f1", label: "Altitude" },
      form_power: { color: "#ec4899", label: "Form Power" },
      air_power: { color: "#8b5cf6", label: "Air Power" },
      distance: { color: "#06b6d4", label: "Distance" }
    };
    return styles[selectedMetric] || { color: "#6b7280", label: "Unknown" };
  };
  
  const metricStyle = getMetricStyle();
  
  // Zone colors (only for heart rate)
  const zoneColors = {
    z1: '#4ade80', // green
    z2: '#fbbf24', // yellow
    zx: '#f97316', // orange
    z3: '#ef4444', // red
    zy: '#dc2626', // dark red
    z4: '#7c2d12', // brown
    z5: '#581c87'  // purple
  };
  
  // Zone backgrounds (only for heart rate)
  let zoneBackgrounds = [];
  if (selectedMetric === "hr" && zoneDefinitions?.heart_rate) {
    const zoneRanges = {
      z1: [zoneDefinitions.heart_rate.z1.lower, zoneDefinitions.heart_rate.z1.upper],
      z2: [zoneDefinitions.heart_rate.z2.lower, zoneDefinitions.heart_rate.z2.upper],
      zx: [zoneDefinitions.heart_rate.zx.lower, zoneDefinitions.heart_rate.zx.upper],
      z3: [zoneDefinitions.heart_rate.z3.lower, zoneDefinitions.heart_rate.z3.upper],
      zy: [zoneDefinitions.heart_rate.zy.lower, zoneDefinitions.heart_rate.zy.upper],
      z4: [zoneDefinitions.heart_rate.z4.lower, zoneDefinitions.heart_rate.z4.upper],
      z5: [zoneDefinitions.heart_rate.z5.lower, zoneDefinitions.heart_rate.z5.upper]
    };
    
    zoneBackgrounds = Object.entries(zoneRanges).map(([zone, [min, max]]) => {
      const y1 = scaleY(max);
      const y2 = scaleY(min);
      return (
        <rect
          key={zone}
          x={margin.left}
          y={y1}
          width={plotWidth}
          height={y2 - y1}
          fill={zoneColors[zone]}
          opacity={0.2}
          stroke={zoneColors[zone]}
          strokeWidth={1}
        />
      );
    });
  }
  
  // Create the data line
  const linePoints = data.map((d, i) => `${scaleX(i)},${scaleY(d.value)}`).join(' ');
  
  // Create grid lines
  const gridLines = [];
  const valueStep = Math.ceil(valueRange / 10 / 10) * 10; // Round to nearest 10
  for (let value = Math.floor(minValue / 10) * 10; value <= maxValue; value += valueStep) {
    const y = scaleY(value);
    gridLines.push(
      <line
        key={value}
        x1={margin.left}
        y1={y}
        x2={margin.left + plotWidth}
        y2={y}
        stroke="#e5e7eb"
        strokeWidth={1}
        opacity={0.5}
      />
    );
  }
  
  // Create time grid lines
  const timeStep = Math.ceil(data.length / 10);
  for (let i = 0; i < data.length; i += timeStep) {
    const x = scaleX(i);
    gridLines.push(
      <line
        key={`time-${i}`}
        x1={x}
        y1={margin.top}
        x2={x}
        y2={margin.top + plotHeight}
        stroke="#e5e7eb"
        strokeWidth={1}
        opacity={0.5}
      />
    );
  }
  
  const handleMouseMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Find closest data point
    const index = Math.round(((x - margin.left) / plotWidth) * (data.length - 1));
    if (index >= 0 && index < data.length) {
      const point = data[index];
      setHoverData(point);
      setHoverPosition({ x: event.clientX, y: event.clientY });
    }
  };
  
  const handleMouseLeave = () => {
    setHoverData(null);
  };
  
  const formatValue = (value) => {
    if (selectedMetric === "pace") {
      // Convert seconds back to MM:SS format
      const minutes = Math.floor(value / 60);
      const seconds = Math.floor(value % 60);
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
    if (selectedMetric === "distance") {
      return value.toFixed(2);
    }
    if (selectedMetric === "altitude") {
      return Math.round(value);
    }
    return value.toFixed(1);
  };
  
  const formatTime = (timestamp) => {
    try {
      // Calculate elapsed time from the first data point
      const firstTimestamp = data[0]?.timestamp;
      if (!firstTimestamp) return timestamp;
      
      const startTime = new Date(firstTimestamp);
      const currentTime = new Date(timestamp);
      const elapsedMs = currentTime - startTime;
      
      // Convert to seconds
      const totalSeconds = Math.floor(elapsedMs / 1000);
      
      // Format as MM:SS or HH:MM:SS
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;
      
      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      } else {
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
      }
    } catch {
      return timestamp;
    }
  };
  
  return (
    <div className="workout-chart">
      <h4>{metricStyle.label}</h4>
      <svg width={width} height={height} style={{ border: '1px solid #ccc' }}>
        {/* Zone backgrounds */}
        {zoneBackgrounds}
        
        {/* Grid lines */}
        {gridLines}
        
        {/* Y-axis title */}
        <text
          x={margin.left - 50}
          y={margin.top + plotHeight / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="14"
          fontWeight="600"
          fill="#374151"
          transform={`rotate(-90, ${margin.left - 50}, ${margin.top + plotHeight / 2})`}
        >
          {metricStyle.label}
        </text>
        
        {/* Data line */}
        <polyline
          points={linePoints}
          fill="none"
          stroke={metricStyle.color}
          strokeWidth={2}
        />
        
        {/* Data points */}
        {data.map((point, i) => (
          <circle
            key={i}
            cx={scaleX(i)}
            cy={scaleY(point.value)}
            r={3}
            fill={metricStyle.color}
            opacity={0.7}
          />
        ))}
        
        {/* Y-axis labels */}
        {Array.from({ length: 6 }, (_, i) => {
          const value = minValue + (valueRange * i / 5);
          const y = scaleY(value);
          return (
            <text
              key={i}
              x={margin.left - 10}
              y={y + 4}
              textAnchor="end"
              fontSize="12"
              fill="#666"
            >
              {formatValue(value)}
            </text>
          );
        })}
        
        {/* X-axis labels */}
        {Array.from({ length: 6 }, (_, i) => {
          const index = Math.floor((data.length - 1) * i / 5);
          const x = scaleX(index);
          const point = data[index];
          return (
            <text
              key={i}
              x={x}
              y={height - margin.bottom + 20}
              textAnchor="middle"
              fontSize="12"
              fill="#666"
              transform={`rotate(-45 ${x} ${height - margin.bottom + 20})`}
            >
              {formatTime(point.timestamp)}
            </text>
          );
        })}
      </svg>
      
      {/* Hover tooltip */}
      {hoverData && (
        <div
          className="chart-tooltip"
          style={{
            position: 'fixed',
            left: hoverPosition.x + 10,
            top: hoverPosition.y - 10,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '8px',
            borderRadius: '4px',
            fontSize: '12px',
            pointerEvents: 'none',
            zIndex: 1000
          }}
        >
          <div>Time: {formatTime(hoverData.timestamp)}</div>
          <div>{metricStyle.label}: {formatValue(hoverData.value)}</div>
        </div>
      )}
    </div>
  );
}

// PMC Chart component - Interactive Performance Management Chart
function PMCChart({ pmcData, workoutsData, timeframe, setTimeframe }) {
  const [hoverData, setHoverData] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  const [selectedMetrics, setSelectedMetrics] = useState({
    ctl: true,
    atl: true,
    tsb: true,
    dailyTss: true
  });

  if (!pmcData || pmcData.length === 0) {
    return (
      <div className="pmc-chart-container">
        <div className="no-data">No PMC data available</div>
      </div>
    );
  }

  // Dynamic axis calculation based on selected metrics
  const needsTssAxis = selectedMetrics.ctl || selectedMetrics.atl || selectedMetrics.dailyTss;
  const needsTsbAxis = selectedMetrics.tsb;
  
  // Dynamic padding based on axes needed
  const padding = {
    top: 50,
    right: needsTsbAxis ? 100 : 40,
    bottom: 80,
    left: needsTssAxis ? 80 : 40
  };
  
  const width = 900;
  const height = 450;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Parse dates and calculate ranges
  const dates = pmcData.map(d => new Date(d.date));
  const minDate = new Date(Math.min(...dates));
  const maxDate = new Date(Math.max(...dates));
  
  // Calculate ranges for selected metrics
  const ctlValues = pmcData.map(d => d.ctl);
  const atlValues = pmcData.map(d => d.atl);
  const tsbValues = pmcData.map(d => d.tsb);
  const workoutTssValues = workoutsData ? workoutsData.map(w => w.tss) : [];
  
  // Dynamic TSS range calculation
  const getTssRange = () => {
    const values = [];
    if (selectedMetrics.ctl) values.push(...ctlValues);
    if (selectedMetrics.atl) values.push(...atlValues);
    if (selectedMetrics.dailyTss) values.push(...workoutTssValues);
    return Math.max(...values, 100); // Ensure minimum range
  };
  
  const maxTSS = getTssRange();
  const minTSB = Math.min(...tsbValues, -20);
  const maxTSB = Math.max(...tsbValues, 20);

  // Scale functions
  const scaleX = x => padding.left + ((x - minDate) / (maxDate - minDate)) * chartWidth;
  const scaleYTSS = y => padding.top + (1 - (y / maxTSS)) * chartHeight;
  const scaleYTSB = y => padding.top + (1 - ((y - minTSB) / (maxTSB - minTSB))) * chartHeight;

  // Format date for display
  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Create paths for each metric (only if selected)
  const createPath = (data, scaleY, key) => {
    return data.map((d, i) => {
      const x = scaleX(new Date(d.date));
      const y = scaleY(d[key]);
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };

  const ctlPath = selectedMetrics.ctl ? createPath(pmcData, scaleYTSS, 'ctl') : '';
  const atlPath = selectedMetrics.atl ? createPath(pmcData, scaleYTSS, 'atl') : '';
  const tsbPath = selectedMetrics.tsb ? createPath(pmcData, scaleYTSB, 'tsb') : '';

  // Create workout scatter points (only if selected)
  const workoutPoints = (selectedMetrics.dailyTss && workoutsData) ? workoutsData.map(w => ({
    x: scaleX(new Date(w.date)),
    y: scaleYTSS(w.tss),
    tss: w.tss,
    date: w.date
  })) : [];

  // Generate Y-axis labels with proper intervals
  const tssLabels = [0, 20, 40, 60, 80, 100, 120, 140, 150, 200, 250, 300];
  const tsbLabels = [-60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60];

  // Handle mouse events for interactivity
  const handleMouseMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Find closest data point
    let closestData = null;
    let minDistance = Infinity;
    
    pmcData.forEach(d => {
      const dataX = scaleX(new Date(d.date));
      const distance = Math.abs(x - dataX);
      if (distance < minDistance && distance < 30) { // Increased detection range
        minDistance = distance;
        closestData = d;
      }
    });
    
    if (closestData) {
      setHoverData(closestData);
      // Fixed position at top right corner of chart
      const rect = event.currentTarget.getBoundingClientRect();
      setHoverPosition({ 
        x: rect.left + width - 10, 
        y: rect.top + 10 
      });
    } else {
      setHoverData(null);
    }
  };

  const handleMouseLeave = () => {
    setHoverData(null);
  };

  // Metric selection handlers
  const handleMetricToggle = (metric) => {
    setSelectedMetrics(prev => ({
      ...prev,
      [metric]: !prev[metric]
    }));
  };

  return (
    <div className="pmc-chart-container">
      <h3>Performance Management - All Workout Types</h3>
      
      {/* Interactive Controls */}
      <div className="pmc-controls">
        <div className="metric-selector">
          <h4>Select Metrics:</h4>
          <div className="metric-buttons">
            <button
              className={`metric-btn ${selectedMetrics.ctl ? 'active' : ''}`}
              onClick={() => handleMetricToggle('ctl')}
            >
              <span className="metric-color" style={{backgroundColor: '#374151'}}></span>
              CTL (Fitness)
            </button>
            <button
              className={`metric-btn ${selectedMetrics.atl ? 'active' : ''}`}
              onClick={() => handleMetricToggle('atl')}
            >
              <span className="metric-color" style={{backgroundColor: '#f97316'}}></span>
              ATL (Fatigue)
            </button>
            <button
              className={`metric-btn ${selectedMetrics.tsb ? 'active' : ''}`}
              onClick={() => handleMetricToggle('tsb')}
            >
              <span className="metric-color" style={{backgroundColor: '#ec4899'}}></span>
              TSB (Form)
            </button>
            <button
              className={`metric-btn ${selectedMetrics.dailyTss ? 'active' : ''}`}
              onClick={() => handleMetricToggle('dailyTss')}
            >
              <span className="metric-color" style={{backgroundColor: '#3b82f6'}}></span>
              Daily TSS
            </button>
          </div>
        </div>
        
        <div className="timeframe-selector">
          <h4>Timeframe: {timeframe} days</h4>
          <div className="timeframe-buttons">
            {[7, 14, 30, 60, 90].map(days => (
              <button
                key={days}
                className={`timeframe-btn ${timeframe === days ? 'active' : ''}`}
                onClick={() => setTimeframe(days)}
              >
                {days} days
              </button>
            ))}
          </div>
        </div>
      </div>
      
      <div className="pmc-chart-wrapper" 
           onMouseMove={handleMouseMove} 
           onMouseLeave={handleMouseLeave}>
        <svg width={width} height={height} style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
          {/* Horizontal grid lines for TSS (only if TSS axis is needed) */}
          {needsTssAxis && tssLabels.map(tss => {
            const y = scaleYTSS(tss);
            return (
              <line
                key={`grid-tss-${tss}`}
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="#f1f5f9"
                strokeWidth="1"
              />
            );
          })}

          {/* Horizontal grid lines for TSB (only if TSB axis is needed) */}
          {needsTsbAxis && tsbLabels.map(tsb => {
            const y = scaleYTSB(tsb);
            return (
              <line
                key={`grid-tsb-${tsb}`}
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="#f1f5f9"
                strokeWidth="1"
                strokeDasharray="2,2"
              />
            );
          })}

          {/* Vertical grid lines for dates */}
          {pmcData.map((d, i) => {
            const x = scaleX(new Date(d.date));
            return (
              <line
                key={`grid-vertical-${i}`}
                x1={x}
                y1={padding.top}
                x2={x}
                y2={height - padding.bottom}
                stroke="#f1f5f9"
                strokeWidth="1"
                opacity="0.5"
              />
            );
          })}

          {/* CTL line with shaded area (only if selected) */}
          {selectedMetrics.ctl && (
            <>
              <defs>
                <linearGradient id="ctlGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#374151" stopOpacity="0.3"/>
                  <stop offset="100%" stopColor="#374151" stopOpacity="0.1"/>
                </linearGradient>
              </defs>
              
              {/* CTL shaded area */}
              <path
                d={`${ctlPath} L ${scaleX(maxDate)} ${scaleYTSS(0)} L ${scaleX(minDate)} ${scaleYTSS(0)} Z`}
                fill="url(#ctlGradient)"
              />
              
              {/* CTL line */}
              <path
                d={ctlPath}
                fill="none"
                stroke="#374151"
                strokeWidth="3"
              />
            </>
          )}

          {/* ATL line (only if selected) */}
          {selectedMetrics.atl && (
            <path
              d={atlPath}
              fill="none"
              stroke="#f97316"
              strokeWidth="2"
            />
          )}

          {/* TSB line (only if selected) */}
          {selectedMetrics.tsb && (
            <path
              d={tsbPath}
              fill="none"
              stroke="#ec4899"
              strokeWidth="2"
            />
          )}

          {/* Workout scatter points (only if selected) */}
          {selectedMetrics.dailyTss && workoutPoints.map((point, i) => (
            <circle
              key={`workout-${i}`}
              cx={point.x}
              cy={point.y}
              r="3"
              fill="#3b82f6"
              opacity="0.7"
            />
          ))}

          {/* X-axis */}
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke="#64748b"
            strokeWidth="2"
          />

          {/* X-axis labels - one per day */}
          {pmcData.map((d, i) => {
            const x = scaleX(new Date(d.date));
            return (
              <text
                key={`x-label-${i}`}
                x={x}
                y={height - padding.bottom + 25}
                textAnchor="middle"
                fontSize="10"
                fill="#64748b"
                transform={`rotate(-45, ${x}, ${height - padding.bottom + 25})`}
              >
                {formatDate(new Date(d.date))}
              </text>
            );
          })}

          {/* Y-axis gridlines */}
          <g className="y-grid">
            {tssLabels.map((tick, index) => (
              <line
                key={index}
                x1={padding.left}
                y1={scaleYTSS(tick)}
                x2={width - padding.right}
                y2={scaleYTSS(tick)}
                stroke="#e5e7eb"
                strokeWidth="1"
                strokeDasharray="2,2"
              />
            ))}
          </g>

          {/* Y-axis */}
          <g className="y-axis">
            <line
              x1={padding.left}
              y1={padding.top}
              x2={padding.left}
              y2={height - padding.bottom}
              stroke="#64748b"
              strokeWidth="2"
            />
            {/* Y-axis ticks and labels */}
            {tssLabels.map((tick, index) => (
              <g key={index}>
                <line
                  x1={padding.left - 5}
                  y1={scaleYTSS(tick)}
                  x2={padding.left}
                  y2={scaleYTSS(tick)}
                  stroke="#64748b"
                  strokeWidth="1"
                />
                <text
                  x={padding.left - 10}
                  y={scaleYTSS(tick)}
                  textAnchor="end"
                  dominantBaseline="middle"
                  fontSize="12"
                  fill="#64748b"
                >
                  {tick}
                </text>
              </g>
            ))}
          </g>

          {/* Y-axis title */}
          <text
            x={padding.left - 40}
            y={height / 2}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="14"
            fontWeight="600"
            fill="#374151"
            transform={`rotate(-90, ${padding.left - 40}, ${height / 2})`}
          >
            TSS/d
          </text>

          {/* Right Y-axis (TSB) - only if needed */}
          {needsTsbAxis && (
            <>
              <line
                x1={width - padding.right}
                y1={padding.top}
                x2={width - padding.right}
                y2={height - padding.bottom}
                stroke="#64748b"
                strokeWidth="2"
              />

              {/* Right Y-axis labels */}
              {tsbLabels.map(tsb => {
                const y = scaleYTSB(tsb);
                return (
                  <text
                    key={`y-tsb-${tsb}`}
                    x={width - padding.right + 15}
                    y={y + 4}
                    textAnchor="start"
                    fontSize="11"
                    fill="#64748b"
                  >
                    {tsb}
                  </text>
                );
              })}

              {/* TSB Axis title */}
              <text
                x={width - padding.right + 40}
                y={height / 2}
                textAnchor="middle"
                transform={`rotate(90, ${width - padding.right + 40}, ${height / 2})`}
                fontSize="14"
                fill="#374151"
                fontWeight="600"
              >
                Form (TSB)
              </text>
            </>
          )}

          {/* Legend - only show selected metrics */}
          <g transform={`translate(${padding.left}, ${padding.top - 30})`}>
            {selectedMetrics.ctl && (
              <>
                <circle cx="0" cy="0" r="4" fill="#374151"/>
                <text x="15" y="4" fontSize="11" fill="#374151" fontWeight="500">CTL</text>
              </>
            )}
            
            {selectedMetrics.atl && (
              <>
                <circle cx={selectedMetrics.ctl ? "80" : "0"} cy="0" r="4" fill="#f97316"/>
                <text x={selectedMetrics.ctl ? "95" : "15"} y="4" fontSize="11" fill="#f97316" fontWeight="500">ATL</text>
              </>
            )}
            
            {selectedMetrics.tsb && (
              <>
                <circle cx={selectedMetrics.ctl && selectedMetrics.atl ? "160" : selectedMetrics.ctl || selectedMetrics.atl ? "80" : "0"} cy="0" r="4" fill="#ec4899"/>
                <text x={selectedMetrics.ctl && selectedMetrics.atl ? "175" : selectedMetrics.ctl || selectedMetrics.atl ? "95" : "15"} y="4" fontSize="11" fill="#ec4899" fontWeight="500">TSB</text>
              </>
            )}
            
            {selectedMetrics.dailyTss && (
              <>
                <circle cx={selectedMetrics.ctl && selectedMetrics.atl && selectedMetrics.tsb ? "240" : selectedMetrics.ctl && selectedMetrics.atl ? "160" : selectedMetrics.ctl || selectedMetrics.atl ? "80" : "0"} cy="0" r="3" fill="#3b82f6" opacity="0.7"/>
                <text x={selectedMetrics.ctl && selectedMetrics.atl && selectedMetrics.tsb ? "255" : selectedMetrics.ctl && selectedMetrics.atl ? "175" : selectedMetrics.ctl || selectedMetrics.atl ? "95" : "15"} y="4" fontSize="11" fill="#3b82f6" fontWeight="500">Daily TSS</text>
              </>
            )}
          </g>

          {/* Hover indicator line */}
          {hoverData && (
            <line
              x1={scaleX(new Date(hoverData.date))}
              y1={padding.top}
              x2={scaleX(new Date(hoverData.date))}
              y2={height - padding.bottom}
              stroke="#64748b"
              strokeWidth="1"
              strokeDasharray="3,3"
            />
          )}
        </svg>

        {/* Hover tooltip */}
        {hoverData && (
          <div 
            className="pmc-tooltip"
            style={{
              position: 'absolute',
              left: hoverPosition.x - 200, // Align tooltip's right edge with chart's right edge
              top: hoverPosition.y,
              transform: 'none',
              pointerEvents: 'none',
              zIndex: 1000
            }}
          >
            <div className="tooltip-header">
              {formatDate(new Date(hoverData.date))}
            </div>
            <div className="tooltip-content">
              {selectedMetrics.ctl && (
                <div className="tooltip-row">
                  <span className="tooltip-label">Fitness (CTL):</span>
                  <span className="tooltip-value">{Math.round(hoverData.ctl)}</span>
                </div>
              )}
              {selectedMetrics.atl && (
                <div className="tooltip-row">
                  <span className="tooltip-label">Fatigue (ATL):</span>
                  <span className="tooltip-value">{Math.round(hoverData.atl)}</span>
                </div>
              )}
              {selectedMetrics.tsb && (
                <div className="tooltip-row">
                  <span className="tooltip-label">Form (TSB):</span>
                  <span className={`tooltip-value ${hoverData.tsb > 0 ? 'positive' : 'negative'}`}>
                    {Math.round(hoverData.tsb)}
                  </span>
                </div>
              )}
              {selectedMetrics.dailyTss && (
                <div className="tooltip-row">
                  <span className="tooltip-label">Daily TSS:</span>
                  <span className="tooltip-value">
                    {workoutsData?.find(w => w.date === hoverData.date)?.tss || 'N/A'}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Tabular Data View for Debugging */}
      <PMCDataTable 
        pmcData={pmcData} 
        workoutsData={workoutsData} 
        selectedMetrics={selectedMetrics}
      />
    </div>
  );
}

// PMC Data Table Component
function PMCDataTable({ pmcData, workoutsData, selectedMetrics }) {
  if (!pmcData || pmcData.length === 0) {
    return null;
  }

  return (
    <div className="pmc-data-table">
      <h4>Data Table (Debug View)</h4>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              {selectedMetrics.ctl && <th>CTL</th>}
              {selectedMetrics.atl && <th>ATL</th>}
              {selectedMetrics.tsb && <th>TSB</th>}
              {selectedMetrics.dailyTss && <th>Daily TSS</th>}
            </tr>
          </thead>
          <tbody>
            {pmcData.map((data, index) => {
              const workout = workoutsData?.find(w => w.date === data.date);
              return (
                <tr key={index}>
                  <td>{new Date(data.date).toLocaleDateString()}</td>
                  {selectedMetrics.ctl && <td>{Math.round(data.ctl)}</td>}
                  {selectedMetrics.atl && <td>{Math.round(data.atl)}</td>}
                  {selectedMetrics.tsb && (
                    <td className={data.tsb > 0 ? 'positive' : 'negative'}>
                      {Math.round(data.tsb)}
                    </td>
                  )}
                  {selectedMetrics.dailyTss && (
                    <td>{workout ? Math.round(workout.tss) : 'N/A'}</td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Health trend line plot component
function HealthTrendPlot({ data, title, color = "#06b6d4", unit = "" }) {
  if (!data || data.length === 0) {
    return (
      <div className="health-plot-container">
        <h4>{title}</h4>
        <div className="no-data">No data available</div>
      </div>
    );
  }

  const width = 400;
  const height = 200;
  const padding = 40;
  const labelHeight = 30; // Extra space for rotated labels
  const margin = { top: 20, right: 20, bottom: 40, left: 50 };

  // Parse dates and get min/max values
  const dates = data.map(d => new Date(d.date));
  const values = data.map(d => d.value);
  const minDate = new Date(Math.min(...dates));
  const maxDate = new Date(Math.max(...dates));
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valueRange = maxValue - minValue;

  // Scale functions
  const scaleX = x => padding + ((x - minDate) / (maxDate - minDate)) * (width - 2 * padding);
  const scaleY = y => height - padding - ((y - minValue) / (maxValue - minValue)) * (height - 2 * padding);

  // Helper functions
  const formatValue = (value) => {
    if (unit === "score") return Math.round(value);
    if (unit === "ms") return Math.round(value);
    if (unit === "bpm") return Math.round(value);
    return value.toFixed(1);
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Create line path
  const linePath = data.map((d, i) => {
    const x = scaleX(new Date(d.date));
    const y = scaleY(d.value);
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  // Create points
  const points = data.map((d, i) => {
    const x = scaleX(new Date(d.date));
    const y = scaleY(d.value);
    return { x, y, value: d.value, date: d.date };
  });

  // Add x-axis date labels (show every 3rd point to avoid crowding)
  const dateLabels = points.filter((_, i) => i % 3 === 0 || i === points.length - 1);

  return (
    <div className="health-plot-container">
      <h4>{title}</h4>
      <svg width={width} height={height + labelHeight} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
        {/* Grid lines */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e2e8f0" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke={color}
          strokeWidth="3"
        />
        
        {/* Data points */}
        {points.map((point, i) => (
          <circle
            key={i}
            cx={point.x}
            cy={point.y}
            r="4"
            fill={color}
            stroke="white"
            strokeWidth="2"
          />
        ))}
        
        {/* Y-axis labels */}
        {Array.from({ length: 6 }, (_, i) => {
          const value = minValue + (valueRange * i / 5);
          const y = scaleY(value);
          return (
            <text
              key={i}
              x={margin.left - 10}
              y={y + 4}
              textAnchor="end"
              fontSize="12"
              fill="#666"
            >
              {formatValue(value)}
            </text>
          );
        })}
        
        {/* X-axis labels */}
        {dateLabels.map((point, i) => (
          <text
            key={i}
            x={point.x}
            y={height - margin.bottom + 20}
            textAnchor="middle"
            fontSize="12"
            fill="#666"
            transform={`rotate(-45 ${point.x} ${height - margin.bottom + 20})`}
          >
            {formatDate(point.date)}
          </text>
        ))}
      </svg>
    </div>
  );
}

// Recovery status card component
function RecoveryStatusCard({ status }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return '#10b981';
      case 'moderate': return '#f59e0b';
      case 'poor': return '#ef4444';
      default: return '#64748b';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'good': return 'Good Recovery';
      case 'moderate': return 'Moderate Recovery';
      case 'poor': return 'Poor Recovery';
      default: return 'Unknown';
    }
  };

  return (
    <div className="recovery-status-card">
      <h3>Recovery Status</h3>
      <div className="status-indicator" style={{ color: getStatusColor(status.status) }}>
        <div className="status-score">{status.score}%</div>
        <div className="status-text">{getStatusText(status.status)}</div>
      </div>
      <div className="status-factors">
        <h4>Factors:</h4>
        <ul>
          {status.factors.map((factor, i) => (
            <li key={i}>{factor}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// Readiness recommendation card component
function ReadinessCard({ recommendation }) {
  const getRecommendationColor = (rec) => {
    switch (rec) {
      case 'train_hard': return '#10b981';
      case 'maintain': return '#f59e0b';
      case 'rest': return '#ef4444';
      default: return '#64748b';
    }
  };

  const getRecommendationText = (rec) => {
    switch (rec) {
      case 'train_hard': return 'Train Hard';
      case 'maintain': return 'Maintain';
      case 'rest': return 'Rest';
      default: return 'Unknown';
    }
  };

  return (
    <div className="readiness-card">
      <h3>Readiness Recommendation</h3>
      <div className="recommendation-indicator" style={{ color: getRecommendationColor(recommendation.recommendation) }}>
        <div className="recommendation-text">{getRecommendationText(recommendation.recommendation)}</div>
        <div className="confidence-score">{recommendation.confidence}% confidence</div>
      </div>
      <div className="reasoning">
        <h4>Reasoning:</h4>
        <p>{recommendation.reasoning}</p>
      </div>
    </div>
  );
}

// Combined Recovery Status Card with Agent Analysis
function CombinedRecoveryCard({ agentAnalysis, onRefresh, isRefreshing }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return '#10b981';
      case 'medium': return '#f59e0b';
      case 'bad': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'good': return 'Good Recovery';
      case 'medium': return 'Moderate Recovery';
      case 'bad': return 'Poor Recovery';
      default: return 'Unknown Status';
    }
  };

  const getRecommendationText = (status) => {
    switch (status) {
      case 'good': return 'Continue with current training plan';
      case 'medium': return 'Consider reducing training intensity or adding recovery days';
      case 'bad': return 'Recommend rest day or very light training. Focus on sleep and recovery';
      default: return 'No recommendation available';
    }
  };

  if (!agentAnalysis) {
    return (
      <div className="recovery-status-card">
        <div className="card-header">
          <h3>Recovery Status</h3>
          <button 
            onClick={onRefresh} 
            disabled={isRefreshing}
            className="refresh-btn"
            title="Refresh Analysis"
          >
            {isRefreshing ? '⏳' : '🔄'}
          </button>
        </div>
        <div className="no-analysis">
          <p>No agent analysis available</p>
          <button onClick={onRefresh} disabled={isRefreshing} className="primary-btn">
            {isRefreshing ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="recovery-status-card">
      <div className="card-header">
        <h3>Recovery Status</h3>
        <button 
          onClick={onRefresh} 
          disabled={isRefreshing}
          className="refresh-btn"
          title="Refresh Analysis"
        >
          {isRefreshing ? '⏳' : '🔄'}
        </button>
      </div>
      
      <div className="status-section">
        <div className="status-indicator" style={{ backgroundColor: getStatusColor(agentAnalysis.status) }}>
          {getStatusText(agentAnalysis.status)}
        </div>
        <div className="last-updated">
          Last updated: {new Date(agentAnalysis.last_updated).toLocaleString()}
        </div>
      </div>

      <div className="detailed-reasoning">
        <h4>Analysis Details</h4>
        <p>{agentAnalysis.detailed_reasoning}</p>
      </div>

      <div className="recommendation-section">
        <h4>Recommendation</h4>
        <p>{getRecommendationText(agentAnalysis.status)}</p>
      </div>

      {agentAnalysis.agent_analysis && agentAnalysis.agent_analysis.trend_analysis && (
        <div className="trend-summary">
          <h4>Trend Summary</h4>
          <div className="trend-items">
            {agentAnalysis.agent_analysis.trend_analysis.rhr_trend && (
              <div className="trend-item">
                <span className="trend-label">RHR:</span>
                <span className={`trend-value ${agentAnalysis.agent_analysis.trend_analysis.rhr_trend.direction}`}>
                  {agentAnalysis.agent_analysis.trend_analysis.rhr_trend.direction}
                </span>
              </div>
            )}
            {agentAnalysis.agent_analysis.trend_analysis.hrv_trend && (
              <div className="trend-item">
                <span className="trend-label">HRV:</span>
                <span className={`trend-value ${agentAnalysis.agent_analysis.trend_analysis.hrv_trend.direction}`}>
                  {agentAnalysis.agent_analysis.trend_analysis.hrv_trend.direction}
                </span>
              </div>
            )}
            {agentAnalysis.agent_analysis.trend_analysis.sleep_trend && (
              <div className="trend-item">
                <span className="trend-label">Sleep:</span>
                <span className={`trend-value ${agentAnalysis.agent_analysis.trend_analysis.sleep_trend.direction}`}>
                  {agentAnalysis.agent_analysis.trend_analysis.sleep_trend.direction}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// PMC Dashboard component
function PMCDashboard() {
  const [pmcData, setPmcData] = useState(null);
  const [workoutsData, setWorkoutsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [athleteId, setAthleteId] = useState("");
  const [monthOffset, setMonthOffset] = useState(0);
  const [timeframe, setTimeframe] = useState(30);

  // Fetch athleteId from profile
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/profile');
        if (!response.ok) throw new Error('Failed to fetch profile');
        const data = await response.json();
        setAthleteId(data.athlete_id);
      } catch (err) {
        setError('Failed to load athlete profile');
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  // Fetch PMC data
  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    setError(null);
    
    const month = getMonthDates(monthOffset);
    const start = month.dates[0].toISOString().slice(0, 10);
    const end = month.dates[month.dates.length - 1].toISOString().slice(0, 10);
    
    Promise.all([
      fetch(`http://localhost:8000/api/metrics/pmc?athlete_id=${athleteId}&start_date=${start}&end_date=${end}`),
      fetch(`http://localhost:8000/api/workouts?athlete_id=${athleteId}&start_date=${start}&end_date=${end}`)
    ])
      .then(responses => Promise.all(responses.map(res => {
        if (!res.ok) throw new Error('Failed to fetch data');
        return res.json();
      })))
      .then(([pmcResponse, workoutsResponse]) => {
        setPmcData(pmcResponse);
        setWorkoutsData(workoutsResponse || []);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [athleteId, monthOffset]);

  const goToPreviousMonth = () => setMonthOffset(prev => prev - 1);
  const goToNextMonth = () => setMonthOffset(prev => prev + 1);
  const goToCurrentMonth = () => setMonthOffset(0);

  const formatMonthDisplay = () => {
    const month = getMonthDates(monthOffset);
    return month.monthName + ' ' + month.year;
  };

  if (loading) {
    return (
      <div className="pmc-container">
        <div className="loading-spinner">Loading PMC data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pmc-container">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!pmcData || !pmcData.metrics || pmcData.metrics.length === 0) {
    return (
      <div className="pmc-container">
        <div className="error-message">No PMC data available</div>
      </div>
    );
  }

  return (
    <div className="pmc-container">
      <div className="pmc-header">
        <div className="pmc-header-content">
          <button
            className="week-nav-btn"
            onClick={goToPreviousMonth}
            title="Previous Month"
          >
            ←
          </button>
          <div>
            <h2>Performance Management Chart</h2>
            <p>Your training load and readiness {formatMonthDisplay()} (Timeframe: {timeframe} days)</p>
          </div>
          <button
            className="week-nav-btn"
            onClick={goToNextMonth}
            title="Next Month"
          >
            →
          </button>
          {monthOffset !== 0 && (
            <button
              className="current-week-btn"
              onClick={goToCurrentMonth}
              title="Go to Current Month"
            >
              Today
            </button>
          )}
        </div>
      </div>

      <div className="pmc-content">
        <div className="pmc-summary">
          <div className="pmc-summary-card">
            <h3>CTL (Fitness)</h3>
            <div className="pmc-value">{pmcData.summary.ctl}</div>
            <p>Chronic Training Load</p>
          </div>
          <div className="pmc-summary-card">
            <h3>ATL (Fatigue)</h3>
            <div className="pmc-value">{pmcData.summary.atl}</div>
            <p>Acute Training Load</p>
          </div>
          <div className="pmc-summary-card">
            <h3>TSB (Readiness)</h3>
            <div className={`pmc-value ${pmcData.summary.tsb > 0 ? 'positive' : 'negative'}`}>
              {pmcData.summary.tsb}
            </div>
            <p>Training Stress Balance</p>
          </div>
        </div>



        <div className="pmc-chart-wrapper">
          <PMCChart 
            pmcData={pmcData.metrics} 
            workoutsData={workoutsData} 
            timeframe={timeframe} 
            setTimeframe={setTimeframe}
          />
        </div>
      </div>
    </div>
  );
}

// Health and Recovery Analysis component
function HealthAnalysis() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [athleteId, setAthleteId] = useState("");
  const [monthOffset, setMonthOffset] = useState(0);
  const [agentAnalysis, setAgentAnalysis] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch athleteId from profile
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/profile');
        if (!response.ok) throw new Error('Failed to fetch profile');
        const data = await response.json();
        setAthleteId(data.athlete_id);
      } catch (err) {
        setError('Failed to load athlete profile');
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  // Fetch health analysis data
  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    setError(null);
    
    const month = getMonthDates(monthOffset);
    const start = month.dates[0].toISOString().slice(0, 10);
    const end = month.dates[month.dates.length - 1].toISOString().slice(0, 10);
    
    fetch(`http://localhost:8000/api/health/analysis?start_date=${start}&end_date=${end}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch health analysis');
        return res.json();
      })
      .then(data => {
        setHealthData(data);
        setAgentAnalysis(data.agent_analysis);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [athleteId, monthOffset]);

  // Trigger agent analysis
  const handleRefreshAnalysis = async () => {
    setIsRefreshing(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/health/agent-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to trigger agent analysis');
      }
      
      const result = await response.json();
      setAgentAnalysis({
        status: result.status,
        detailed_reasoning: result.detailed_reasoning,
        last_updated: result.last_updated,
        agent_analysis: result
      });
      
      // Refresh health data to get updated analysis
      const month = getMonthDates(monthOffset);
      const start = month.dates[0].toISOString().slice(0, 10);
      const end = month.dates[month.dates.length - 1].toISOString().slice(0, 10);
      
      const healthResponse = await fetch(`http://localhost:8000/api/health/analysis?start_date=${start}&end_date=${end}`);
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setHealthData(healthData);
      }
      
    } catch (err) {
      setError(`Agent analysis failed: ${err.message}`);
    } finally {
      setIsRefreshing(false);
    }
  };

  const goToPreviousMonth = () => setMonthOffset(prev => prev - 1);
  const goToNextMonth = () => setMonthOffset(prev => prev + 1);
  const goToCurrentMonth = () => setMonthOffset(0);

  const formatMonthDisplay = () => {
    const month = getMonthDates(monthOffset);
    return month.monthName + ' ' + month.year;
  };

  if (loading) {
    return (
      <div className="health-container">
        <div className="loading-spinner">Loading health analysis...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="health-container">
        <div className="error-message">{error}</div>
        <button onClick={handleRefreshAnalysis} disabled={isRefreshing} className="primary-btn">
          {isRefreshing ? 'Retrying...' : 'Retry Analysis'}
        </button>
      </div>
    );
  }

  if (!healthData) {
    return (
      <div className="health-container">
        <div className="error-message">No health data available</div>
      </div>
    );
  }

  return (
    <div className="health-container">
      <div className="health-header">
        <div className="health-header-content">
          <button
            className="week-nav-btn"
            onClick={goToPreviousMonth}
            title="Previous Month"
          >
            ←
          </button>
          <div>
            <h2>Health Analysis</h2>
            <div className="month-navigation">
              <button onClick={goToPreviousMonth}>&lt; Previous Month</button>
              <button onClick={goToCurrentMonth} className="current-btn">Current Month</button>
              <button onClick={goToNextMonth}>Next Month &gt;</button>
            </div>
            <div className="month-display">{formatMonthDisplay()}</div>
          </div>
          <button
            className="week-nav-btn"
            onClick={goToNextMonth}
            title="Next Month"
          >
            →
          </button>
          {monthOffset !== 0 && (
            <button
              className="current-week-btn"
              onClick={goToCurrentMonth}
              title="Go to Current Month"
            >
              Today
            </button>
          )}
        </div>
      </div>

      <div className="health-content">
        {/* Recovery Analysis Card - Top Center */}
        <div className="recovery-section">
          <div className="analysis-grid">
            <CombinedRecoveryCard 
              agentAnalysis={agentAnalysis} 
              onRefresh={handleRefreshAnalysis} 
              isRefreshing={isRefreshing}
            />
          </div>
        </div>

        <div className="trends-section">
          <h3>Health Trends</h3>
          <div className="trends-grid">
            <HealthTrendPlot 
              data={healthData.trends.sleep} 
              title="Sleep Quality" 
              color="#06b6d4" 
              unit="score"
            />
            <HealthTrendPlot 
              data={healthData.trends.hrv} 
              title="Heart Rate Variability" 
              color="#10b981" 
              unit="ms"
            />
            <HealthTrendPlot 
              data={healthData.trends.rhr} 
              title="Resting Heart Rate" 
              color="#f59e0b" 
              unit="bpm"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [selectedItem, setSelectedItem] = useState('pmc');
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    document.body.classList.toggle('dark', darkMode);
  }, [darkMode]);

  const renderMainContent = () => {
    switch (selectedItem) {
      case 'pmc':
        return <PMCDashboard />;
      case 'sync':
        return <SyncData />;
      case 'profile':
        return <ViewProfile />;
      case 'workouts':
        return <WorkoutsView />;
      case 'plan':
        return <TrainingPlanDesigner />;
      case 'health':
        return <HealthAnalysis />;
      default:
        return <PMCDashboard />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar selectedItem={selectedItem} onItemSelect={setSelectedItem} />
      <div className="main-content">
        <div className="top-bar">
          <button
            className="theme-toggle"
            onClick={() => setDarkMode(!darkMode)}
          >
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
        {renderMainContent()}
      </div>
    </div>
  );
}

export default App; 