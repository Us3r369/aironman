import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import "./App.css";

function Sidebar({ selectedItem, onItemSelect }) {
  return (
    <div className="sidebar">
      <div className="sidebar-title">AIronman</div>
      <ul>
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

// Calendar utility: get dates for current week (Monday-Sunday)
function getCurrentWeekDates() {
  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - today.getDay() + 1); // Monday
  const week = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    week.push(d);
  }
  return week;
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

  // Fetch workouts for current week
  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    setError(null);
    const week = getCurrentWeekDates();
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
  }, [athleteId]);

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

  const week = getCurrentWeekDates();
  // Group workouts by date (YYYY-MM-DD)
  const workoutsByDate = {};
  workouts.forEach(w => {
    const date = w.timestamp.slice(0, 10);
    if (!workoutsByDate[date]) workoutsByDate[date] = [];
    workoutsByDate[date].push(w);
  });

  return (
    <div className="workouts-container">
      <h2>Workouts This Week</h2>
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

function App() {
  const [selectedItem, setSelectedItem] = useState('sync');

  const renderMainContent = () => {
    switch (selectedItem) {
      case 'sync':
        return <SyncData />;
      case 'profile':
        return <ViewProfile />;
      case 'workouts':
        return <WorkoutsView />;
      default:
        return <div>Select an option from the sidebar</div>;
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