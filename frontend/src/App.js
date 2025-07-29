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
          📈 Performance Chart
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
function getWeekDates(weekOffset = 0) {
  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - today.getDay() + 1); // Monday
  // Add week offset
  monday.setDate(monday.getDate() + (weekOffset * 7));
  const week = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    week.push(d);
  }
  return week;
}

// Get current week dates (for backward compatibility)
function getCurrentWeekDates() {
  return getWeekDates(0);
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
  const [weekOffset, setWeekOffset] = useState(0); // 0 = current week, -1 = previous week, etc.

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

  // Fetch workouts for selected week
  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    setError(null);
    const week = getWeekDates(weekOffset);
    const start = week[0].toISOString().slice(0, 10);
    const end = week[6].toISOString().slice(0, 10);
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
  }, [athleteId, weekOffset]);

  // Fetch workout detail when selected
  useEffect(() => {
    if (!selectedWorkout) return;
    setDetailLoading(true);
    setDetailError(null);
    setWorkoutDetail(null);
    fetch(`http://localhost:8000/api/workouts/${selectedWorkout}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch workout detail');
        return res.json();
      })
      .then(data => {
        setWorkoutDetail(data);
        setDetailLoading(false);
      })
      .catch(err => {
        setDetailError(err.message);
        setDetailLoading(false);
      });
  }, [selectedWorkout]);

  const week = getWeekDates(weekOffset);
  // Group workouts by date (YYYY-MM-DD)
  const workoutsByDate = {};
  workouts.forEach(w => {
    const date = w.timestamp.slice(0, 10);
    if (!workoutsByDate[date]) workoutsByDate[date] = [];
    workoutsByDate[date].push(w);
  });

  // Navigation functions
  const goToPreviousWeek = () => {
    setWeekOffset(weekOffset - 1);
  };

  const goToNextWeek = () => {
    setWeekOffset(weekOffset + 1);
  };

  const goToCurrentWeek = () => {
    setWeekOffset(0);
  };

  // Format week display
  const formatWeekDisplay = () => {
    const startDate = week[0];
    const endDate = week[6];
    const isCurrentWeek = weekOffset === 0;
    
    if (isCurrentWeek) {
      return "This Week";
    } else if (weekOffset === -1) {
      return "Last Week";
    } else if (weekOffset === 1) {
      return "Next Week";
    } else {
      return `${startDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} - ${endDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`;
    }
  };

  return (
    <div className="workouts-container">
      <div className="workouts-header">
        <button 
          className="week-nav-btn" 
          onClick={goToPreviousWeek}
          title="Previous Week"
        >
          ←
        </button>
        <h2>Workouts {formatWeekDisplay()}</h2>
        <button 
          className="week-nav-btn" 
          onClick={goToNextWeek}
          title="Next Week"
        >
          →
        </button>
        {weekOffset !== 0 && (
          <button 
            className="current-week-btn" 
            onClick={goToCurrentWeek}
            title="Go to Current Week"
          >
            Today
          </button>
        )}
      </div>
      {loading ? (
        <div className="loading-spinner">Loading workouts...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <table className="calendar-table">
          <thead>
            <tr>
              {week.map(d => (
                <th key={d.toISOString().slice(0, 10)}>
                  {d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {week.map(d => {
                const dateStr = d.toISOString().slice(0, 10);
                const dayWorkouts = workoutsByDate[dateStr] || [];
                return (
                  <td key={dateStr} className="calendar-cell">
                    {dayWorkouts.length === 0 ? (
                      <span className="no-workout">-</span>
                    ) : (
                      <ul className="workout-list">
                        {dayWorkouts.map(w => (
                          <li key={w.id} className="workout-item" onClick={() => setSelectedWorkout(w.id)}>
                            <span className="workout-type">{w.workout_type}</span>
                            {w.tss !== null && <span className="workout-tss">TSS: {w.tss}</span>}
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      )}
      {/* Workout detail modal */}
      {selectedWorkout && (
        <div className="workout-modal-overlay" onClick={() => setSelectedWorkout(null)}>
          <div className="workout-modal" onClick={e => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setSelectedWorkout(null)}>&times;</button>
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
                {/* Tabular data from json_file if available */}
                {workoutDetail.json_file && workoutDetail.json_file.data && Array.isArray(workoutDetail.json_file.data) && (
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
                {/* Optionally, add a simple plot (e.g., time vs. heart_rate or power) */}
                {workoutDetail.json_file && workoutDetail.json_file.data && Array.isArray(workoutDetail.json_file.data) && (
                  <SimpleWorkoutPlot data={workoutDetail.json_file.data} />
                )}
                {/* Pretty-printed JSON for the full json_file */}
                {workoutDetail.json_file && (
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

// Simple plot using SVG (time vs. heart_rate or power if available)
function SimpleWorkoutPlot({ data }) {
  // Try to plot time vs. heart_rate or power
  const metric = data[0].heart_rate ? 'heart_rate' : (data[0].power ? 'power' : null);
  if (!metric) return null;
  // X: index, Y: metric
  const points = data.slice(0, 100).map((d, i) => [i, d[metric]]).filter(([i, y]) => y !== undefined && y !== null);
  if (points.length < 2) return null;
  const width = 300, height = 100;
  const minY = Math.min(...points.map(p => p[1]));
  const maxY = Math.max(...points.map(p => p[1]));
  const scaleY = y => height - ((y - minY) / (maxY - minY + 1e-6)) * height;
  const scaleX = x => (x / (points.length - 1)) * width;
  return (
    <div className="workout-plot-container">
      <h4>{metric.replace('_', ' ').toUpperCase()} Plot</h4>
      <svg width={width} height={height} style={{ background: '#f8f8f8', border: '1px solid #ccc' }}>
        <polyline
          fill="none"
          stroke="#0074d9"
          strokeWidth="2"
          points={points.map(([x, y]) => `${scaleX(x)},${scaleY(y)}`).join(' ')}
        />
      </svg>
    </div>
  );
}

// PMC Chart component - Professional Performance Management Chart
function PMCChart({ pmcData, workoutsData }) {
  if (!pmcData || pmcData.length === 0) {
    return (
      <div className="pmc-chart-container">
        <div className="no-data">No PMC data available</div>
      </div>
    );
  }

  const width = 800;
  const height = 400;
  const padding = { top: 40, right: 80, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Parse dates and calculate ranges
  const dates = pmcData.map(d => new Date(d.date));
  const minDate = new Date(Math.min(...dates));
  const maxDate = new Date(Math.max(...dates));
  
  // Calculate ranges for dual Y-axes
  const ctlValues = pmcData.map(d => d.ctl);
  const atlValues = pmcData.map(d => d.atl);
  const tsbValues = pmcData.map(d => d.tsb);
  
  const maxTSS = Math.max(...ctlValues, ...atlValues, 100); // Ensure minimum range
  const minTSB = Math.min(...tsbValues, -20); // Ensure negative range
  const maxTSB = Math.max(...tsbValues, 20);  // Ensure positive range

  // Scale functions
  const scaleX = x => padding.left + ((x - minDate) / (maxDate - minDate)) * chartWidth;
  const scaleYTSS = y => padding.top + (1 - (y / maxTSS)) * chartHeight;
  const scaleYTSB = y => padding.top + (1 - ((y - minTSB) / (maxTSB - minTSB))) * chartHeight;

  // Format date for display
  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Create paths for each metric
  const createPath = (data, scaleY, key) => {
    return data.map((d, i) => {
      const x = scaleX(new Date(d.date));
      const y = scaleY(d[key]);
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };

  const ctlPath = createPath(pmcData, scaleYTSS, 'ctl');
  const atlPath = createPath(pmcData, scaleYTSS, 'atl');
  const tsbPath = createPath(pmcData, scaleYTSB, 'tsb');

  // Create workout scatter points
  const workoutPoints = workoutsData ? workoutsData.map(w => ({
    x: scaleX(new Date(w.date)),
    y: scaleYTSS(w.tss),
    tss: w.tss,
    date: w.date
  })) : [];

  // Generate Y-axis labels
  const tssLabels = [0, 50, 100, 150, 200, 250, 300];
  const tsbLabels = [-60, -40, -20, 0, 20, 40, 60];

  return (
    <div className="pmc-chart-container">
      <h3>Performance Management Chart</h3>
      <svg width={width} height={height} style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
        {/* Grid lines for TSS */}
        {tssLabels.map(tss => {
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

        {/* CTL line with shaded area */}
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

        {/* ATL line */}
        <path
          d={atlPath}
          fill="none"
          stroke="#f97316"
          strokeWidth="2"
        />

        {/* TSB line */}
        <path
          d={tsbPath}
          fill="none"
          stroke="#ec4899"
          strokeWidth="2"
        />

        {/* Workout scatter points */}
        {workoutPoints.map((point, i) => (
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

        {/* X-axis labels */}
        {pmcData.filter((_, i) => i % 3 === 0 || i === pmcData.length - 1).map((d, i) => {
          const x = scaleX(new Date(d.date));
          return (
            <text
              key={`x-label-${i}`}
              x={x}
              y={height - padding.bottom + 20}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
              transform={`rotate(-45, ${x}, ${height - padding.bottom + 20})`}
            >
              {formatDate(new Date(d.date))}
            </text>
          );
        })}

        {/* Left Y-axis (TSS) */}
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
          stroke="#64748b"
          strokeWidth="2"
        />

        {/* Left Y-axis labels */}
        {tssLabels.map(tss => {
          const y = scaleYTSS(tss);
          return (
            <text
              key={`y-tss-${tss}`}
              x={padding.left - 10}
              y={y + 4}
              textAnchor="end"
              fontSize="10"
              fill="#64748b"
            >
              {tss}
            </text>
          );
        })}

        {/* Right Y-axis (TSB) */}
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
              x={width - padding.right + 10}
              y={y + 4}
              textAnchor="start"
              fontSize="10"
              fill="#64748b"
            >
              {tsb}
            </text>
          );
        })}

        {/* Axis titles */}
        <text
          x={padding.left - 30}
          y={height / 2}
          textAnchor="middle"
          transform={`rotate(-90, ${padding.left - 30}, ${height / 2})`}
          fontSize="12"
          fill="#374151"
          fontWeight="600"
        >
          TSS/d
        </text>

        <text
          x={width - padding.right + 30}
          y={height / 2}
          textAnchor="middle"
          transform={`rotate(90, ${width - padding.right + 30}, ${height / 2})`}
          fontSize="12"
          fill="#374151"
          fontWeight="600"
        >
          Form (TSB)
        </text>

        {/* Legend */}
        <g transform={`translate(${padding.left}, ${padding.top - 20})`}>
          <circle cx="0" cy="0" r="4" fill="#374151"/>
          <text x="15" y="4" fontSize="10" fill="#374151">CTL</text>
          
          <circle cx="80" cy="0" r="4" fill="#f97316"/>
          <text x="95" y="4" fontSize="10" fill="#f97316">ATL</text>
          
          <circle cx="140" cy="0" r="4" fill="#ec4899"/>
          <text x="155" y="4" fontSize="10" fill="#ec4899">TSB</text>
          
          <circle cx="200" cy="0" r="3" fill="#3b82f6" opacity="0.7"/>
          <text x="215" y="4" fontSize="10" fill="#3b82f6">Daily TSS</text>
        </g>
      </svg>
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

  // Parse dates and get min/max values
  const dates = data.map(d => new Date(d.date));
  const values = data.map(d => d.value);
  const minDate = new Date(Math.min(...dates));
  const maxDate = new Date(Math.max(...dates));
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);

  // Scale functions
  const scaleX = x => padding + ((x - minDate) / (maxDate - minDate)) * (width - 2 * padding);
  const scaleY = y => height - padding - ((y - minValue) / (maxValue - minValue)) * (height - 2 * padding);

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

  // Format date for display
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

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
        
        {/* X-axis date labels */}
        {dateLabels.map((point, i) => (
          <text
            key={`label-${i}`}
            x={point.x}
            y={height + 15}
            textAnchor="end"
            fontSize="10"
            fill="#64748b"
            transform={`rotate(-45, ${point.x}, ${height + 15})`}
          >
            {formatDate(point.date)}
          </text>
        ))}
        
        {/* Y-axis labels */}
        <text x="10" y={height/2} textAnchor="middle" transform={`rotate(-90, 10, ${height/2})`} fontSize="12" fill="#64748b">
          {unit}
        </text>
        
        {/* Y-axis value labels */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
          const value = minValue + (maxValue - minValue) * ratio;
          const y = height - padding - (height - 2 * padding) * ratio;
          return (
            <text
              key={`y-label-${i}`}
              x={padding - 5}
              y={y + 4}
              textAnchor="end"
              fontSize="10"
              fill="#64748b"
            >
              {Math.round(value)}
            </text>
          );
        })}
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

// PMC Dashboard component
function PMCDashboard() {
  const [pmcData, setPmcData] = useState(null);
  const [workoutsData, setWorkoutsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [athleteId, setAthleteId] = useState("");
  const [weekOffset, setWeekOffset] = useState(0);

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

  // Fetch PMC data and workouts
  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    setError(null);
    
    // Calculate date range based on week offset
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() + (weekOffset * 7) - 30);
    const endDate = new Date(today);
    endDate.setDate(today.getDate() + (weekOffset * 7) + 7);
    
    const start = startDate.toISOString().slice(0, 10);
    const end = endDate.toISOString().slice(0, 10);
    
    // Fetch PMC data
    const fetchPMCData = fetch(`http://localhost:8000/api/metrics/pmc?athlete_id=${athleteId}&start_date=${start}&end_date=${end}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch PMC data');
        return res.json();
      });
    
    // Fetch workouts data for scatter plot
    const fetchWorkoutsData = fetch(`http://localhost:8000/api/workouts?athlete_id=${athleteId}&start_date=${start}&end_date=${end}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch workouts data');
        return res.json();
      })
      .then(workouts => workouts.map(w => ({
        date: w.timestamp,
        tss: w.tss || 0
      })));
    
    // Wait for both requests to complete
    Promise.all([fetchPMCData, fetchWorkoutsData])
      .then(([pmc, workouts]) => {
        setPmcData(pmc);
        setWorkoutsData(workouts);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [athleteId, weekOffset]);

  // Navigation functions
  const goToPreviousWeek = () => setWeekOffset(prev => prev - 1);
  const goToNextWeek = () => setWeekOffset(prev => prev + 1);
  const goToCurrentWeek = () => setWeekOffset(0);

  const formatWeekDisplay = () => {
    if (weekOffset === 0) return "This Week";
    if (weekOffset === -1) return "Last Week";
    if (weekOffset === 1) return "Next Week";
    if (weekOffset < 0) return `${Math.abs(weekOffset)} Weeks Ago`;
    return `${weekOffset} Weeks Ahead`;
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

  if (!pmcData) {
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
            onClick={goToPreviousWeek}
            title="Previous Week"
          >
            ←
          </button>
          <div>
            <h2>Performance Management Chart</h2>
            <p>Your training load and readiness {formatWeekDisplay()}</p>
          </div>
          <button
            className="week-nav-btn"
            onClick={goToNextWeek}
            title="Next Week"
          >
            →
          </button>
          {weekOffset !== 0 && (
            <button
              className="current-week-btn"
              onClick={goToCurrentWeek}
              title="Go to Current Week"
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
          <PMCChart pmcData={pmcData.metrics} workoutsData={workoutsData} />
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
  const [weekOffset, setWeekOffset] = useState(0); // 0 = current week, -1 = previous week, etc.

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
    
    // Calculate date range based on week offset
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() + (weekOffset * 7) - 30); // 30 days before the target week
    const endDate = new Date(today);
    endDate.setDate(today.getDate() + (weekOffset * 7) + 7); // 7 days after the target week
    
    const start = startDate.toISOString().slice(0, 10);
    const end = endDate.toISOString().slice(0, 10);
    
    fetch(`http://localhost:8000/api/health/analysis?athlete_id=${athleteId}&start_date=${start}&end_date=${end}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch health data');
        return res.json();
      })
      .then(data => {
        setHealthData(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [athleteId, weekOffset]);

  // Navigation functions
  const goToPreviousWeek = () => setWeekOffset(prev => prev - 1);
  const goToNextWeek = () => setWeekOffset(prev => prev + 1);
  const goToCurrentWeek = () => setWeekOffset(0);

  const formatWeekDisplay = () => {
    if (weekOffset === 0) return "This Week";
    if (weekOffset === -1) return "Last Week";
    if (weekOffset === 1) return "Next Week";
    if (weekOffset < 0) return `${Math.abs(weekOffset)} Weeks Ago`;
    return `${weekOffset} Weeks Ahead`;
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
            onClick={goToPreviousWeek}
            title="Previous Week"
          >
            ←
          </button>
          <div>
            <h2>Health & Recovery Analysis</h2>
            <p>Analysis of your sleep, HRV, and RHR trends {formatWeekDisplay()}</p>
          </div>
          <button
            className="week-nav-btn"
            onClick={goToNextWeek}
            title="Next Week"
          >
            →
          </button>
          {weekOffset !== 0 && (
            <button
              className="current-week-btn"
              onClick={goToCurrentWeek}
              title="Go to Current Week"
            >
              Today
            </button>
          )}
        </div>
      </div>

      <div className="health-content">
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

        <div className="analysis-section">
          <div className="analysis-grid">
            <RecoveryStatusCard status={healthData.recovery_status} />
            <ReadinessCard recommendation={healthData.readiness_recommendation} />
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [selectedItem, setSelectedItem] = useState('pmc');

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
        {renderMainContent()}
      </div>
    </div>
  );
}

export default App; 