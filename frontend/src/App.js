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
  const [zoneData, setZoneData] = useState(null);
  const [zoneLoading, setZoneLoading] = useState(false);
  const [zoneDefinitions, setZoneDefinitions] = useState(null);
  const [zoneDefsLoading, setZoneDefsLoading] = useState(false);

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
                
                {/* Heart Rate Plot for bike and run workouts */}
                {(workoutDetail.workout_type === 'bike' || workoutDetail.workout_type === 'run') && 
                 workoutDetail.json_file && workoutDetail.json_file.data && Array.isArray(workoutDetail.json_file.data) && (
                  <div>
                    {zoneLoading || zoneDefsLoading ? (
                      <div className="loading-spinner">Loading zone analysis...</div>
                    ) : (
                      <HeartRatePlot 
                        data={workoutDetail.json_file.data} 
                        zoneData={zoneData}
                        workoutType={workoutDetail.workout_type}
                        zoneDefinitions={zoneDefinitions}
                      />
                    )}
                  </div>
                )}
                
                {/* Tabular data for other workout types or when no heart rate data */}
                {((workoutDetail.workout_type !== 'bike' && workoutDetail.workout_type !== 'run') || 
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

// Sophisticated heart rate plot with zone visualization
function HeartRatePlot({ data, zoneData, workoutType, zoneDefinitions }) {
  const [hoverData, setHoverData] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  
  // Extract heart rate data
  const hrData = data.filter(d => d.heart_rate !== undefined && d.heart_rate !== null);
  if (hrData.length < 2) return null;
  
  const width = 800;
  const height = 400;
  const margin = { top: 40, right: 60, bottom: 80, left: 80 }; // Increased bottom margin for x-axis labels
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  
  // Calculate scales
  const minHR = Math.min(...hrData.map(d => d.heart_rate));
  const maxHR = Math.max(...hrData.map(d => d.heart_rate));
  const hrRange = maxHR - minHR;
  
  const scaleY = (hr) => margin.top + plotHeight - ((hr - minHR) / hrRange) * plotHeight;
  const scaleX = (index) => margin.left + (index / (hrData.length - 1)) * plotWidth;
  
  // Zone colors
  const zoneColors = {
    z1: '#4ade80', // green
    z2: '#fbbf24', // yellow
    zx: '#f97316', // orange
    z3: '#ef4444', // red
    zy: '#dc2626', // dark red
    z4: '#7c2d12', // brown
    z5: '#581c87'  // purple
  };
  
  // Zone ranges from database (fallback to defaults if not available)
  const zoneRanges = zoneDefinitions?.heart_rate ? {
    z1: [zoneDefinitions.heart_rate.z1.lower, zoneDefinitions.heart_rate.z1.upper],
    z2: [zoneDefinitions.heart_rate.z2.lower, zoneDefinitions.heart_rate.z2.upper],
    zx: [zoneDefinitions.heart_rate.zx.lower, zoneDefinitions.heart_rate.zx.upper],
    z3: [zoneDefinitions.heart_rate.z3.lower, zoneDefinitions.heart_rate.z3.upper],
    zy: [zoneDefinitions.heart_rate.zy.lower, zoneDefinitions.heart_rate.zy.upper],
    z4: [zoneDefinitions.heart_rate.z4.lower, zoneDefinitions.heart_rate.z4.upper],
    z5: [zoneDefinitions.heart_rate.z5.lower, zoneDefinitions.heart_rate.z5.upper]
  } : {
    z1: [124, 139],
    z2: [139, 155],
    zx: [155, 163],
    z3: [163, 172],
    zy: [172, 175],
    z4: [175, 181],
    z5: [181, 255]
  };
  
  // Create zone background rectangles
  const zoneBackgrounds = Object.entries(zoneRanges).map(([zone, [min, max]]) => {
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
  
  // Create the heart rate line
  const linePoints = hrData.map((d, i) => `${scaleX(i)},${scaleY(d.heart_rate)}`).join(' ');
  
  // Create grid lines
  const gridLines = [];
  const hrStep = Math.ceil(hrRange / 10 / 10) * 10; // Round to nearest 10
  for (let hr = Math.floor(minHR / 10) * 10; hr <= maxHR; hr += hrStep) {
    const y = scaleY(hr);
    gridLines.push(
      <line
        key={hr}
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
  const timeStep = Math.ceil(hrData.length / 10);
  for (let i = 0; i < hrData.length; i += timeStep) {
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
  
  // Calculate time-based x-axis labels
  const totalDuration = hrData.length > 1 ? 
    (new Date(hrData[hrData.length - 1].timestamp) - new Date(hrData[0].timestamp)) / 1000 / 60 : 0; // minutes
  const labelInterval = Math.max(1, Math.ceil(totalDuration / 10)); // Show ~10 labels
  
  // Create time grid lines and labels
  const timeLabels = [];
  for (let i = 0; i < hrData.length; i += Math.ceil(hrData.length / 10)) {
    const x = scaleX(i);
    const dataPoint = hrData[i];
    if (dataPoint && dataPoint.timestamp) {
      const time = new Date(dataPoint.timestamp);
      const minutes = Math.floor((time - new Date(hrData[0].timestamp)) / 1000 / 60);
      
      // Only show labels at reasonable intervals
      if (minutes % labelInterval === 0 || i === 0 || i === hrData.length - 1) {
        timeLabels.push(
          <g key={`time-label-${i}`}>
            <line
              x1={x}
              y1={margin.top}
              x2={x}
              y2={margin.top + plotHeight}
              stroke="#e5e7eb"
              strokeWidth="1"
              opacity="0.5"
            />
            <text
              x={x}
              y={height - margin.bottom + 15}
              textAnchor="middle"
              fontSize="10"
              fill="#6b7280"
              transform={`rotate(-45, ${x}, ${height - margin.bottom + 15})`}
            >
              {`${Math.floor(minutes / 60)}:${(minutes % 60).toString().padStart(2, '0')}`}
            </text>
          </g>
        );
      }
    }
  }
  
  // Handle mouse events for hover
  const handleMouseMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Find closest data point with improved precision
    const index = Math.round(((x - margin.left) / plotWidth) * (hrData.length - 1));
    if (index >= 0 && index < hrData.length) {
      const dataPoint = hrData[index];
      const time = new Date(dataPoint.timestamp);
      const startTime = new Date(hrData[0].timestamp);
      const elapsedMinutes = Math.floor((time - startTime) / 1000 / 60);
      
      setHoverData({
        index,
        heartRate: dataPoint.heart_rate,
        timestamp: dataPoint.timestamp,
        elapsedTime: `${Math.floor(elapsedMinutes / 60)}:${(elapsedMinutes % 60).toString().padStart(2, '0')}`
      });
      setHoverPosition({ x: event.clientX, y: event.clientY });
    }
  };
  
  const handleMouseLeave = () => {
    setHoverData(null);
  };
  
  // Format time for display
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };
  
  return (
    <div className="heart-rate-plot-container">
      <h4>Heart Rate Analysis</h4>
      <div className="plot-wrapper" style={{ position: 'relative' }}>
        <svg 
          width={width} 
          height={height} 
          style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          {/* Zone backgrounds */}
          {zoneBackgrounds}
          
          {/* Grid lines */}
          {gridLines}
          
          {/* Time labels */}
          {timeLabels}
          
          {/* Heart rate line */}
          <polyline
            fill="none"
            stroke="#1f2937"
            strokeWidth="2"
            points={linePoints}
          />
          
          {/* Axis labels */}
          <text x={width / 2} y={height - 20} textAnchor="middle" fontSize="12" fill="#6b7280">
            Time (MM:SS)
          </text>
          <text x={20} y={height / 2} textAnchor="middle" fontSize="12" fill="#6b7280" transform={`rotate(-90, 20, ${height / 2})`}>
            Heart Rate (bpm)
          </text>
          
          {/* Y-axis tick marks and labels */}
          {Object.entries(zoneRanges).map(([zone, [min, max]]) => (
            <g key={`tick-${zone}`}>
              <line
                x1={margin.left - 5}
                y1={scaleY(max)}
                x2={margin.left}
                y2={scaleY(max)}
                stroke="#6b7280"
                strokeWidth={1}
              />
              <text
                x={margin.left - 10}
                y={scaleY(max)}
                textAnchor="end"
                fontSize="10"
                fill="#6b7280"
                dy="0.3em"
              >
                {max}
              </text>
            </g>
          ))}
          
          {/* Zone labels */}
          {Object.entries(zoneRanges).map(([zone, [min, max]], index) => {
            const y = scaleY((min + max) / 2);
            return (
              <text
                key={`label-${zone}`}
                x={margin.left + plotWidth + 10}
                y={y}
                fontSize="12"
                fill={zoneColors[zone]}
                fontWeight="bold"
                dy="0.3em"
              >
                {zone.toUpperCase()}
              </text>
            );
          })}
        </svg>
        
        {/* Enhanced hover tooltip */}
        {hoverData && (
          <div
            className="hover-tooltip"
            style={{
              position: 'absolute',
              left: hoverPosition.x + 10,
              top: hoverPosition.y - 10,
              background: 'rgba(0, 0, 0, 0.9)',
              color: 'white',
              padding: '8px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              pointerEvents: 'none',
              zIndex: 1000,
              whiteSpace: 'nowrap',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)'
            }}
          >
            <div><strong>Time:</strong> {hoverData.elapsedTime}</div>
            <div><strong>Heart Rate:</strong> {hoverData.heartRate} bpm</div>
            <div><strong>Point:</strong> {hoverData.index + 1}</div>
          </div>
        )}
      </div>
      
      {/* Enhanced zone summary table */}
      {zoneData && (
        <div className="zone-summary-table" style={{ marginTop: '20px' }}>
          <h5 style={{ marginBottom: '15px', color: '#374151', fontSize: '14px', fontWeight: '600' }}>
            Zone Summary
          </h5>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '15px',
            background: 'white',
            padding: '15px',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            {Object.entries(zoneData.heart_rate_zones)
              .filter(([zone, minutes]) => minutes > 0)
              .map(([zone, minutes]) => {
                const zoneName = zone.replace('_minutes', '');
                const zoneRange = zoneRanges[zoneName];
                const percentage = (minutes / zoneData.total_duration_minutes * 100).toFixed(1);
                return (
                  <div key={zone} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px',
                    padding: '10px',
                    background: '#f9fafb',
                    borderRadius: '6px',
                    border: `2px solid ${zoneColors[zoneName]}`
                  }}>
                    <div
                      style={{
                        width: '16px',
                        height: '16px',
                        backgroundColor: zoneColors[zoneName],
                        borderRadius: '3px'
                      }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', fontSize: '14px', color: '#374151' }}>
                        {zoneName.toUpperCase()}
                      </div>
                      <div style={{ fontSize: '12px', color: '#6b7280' }}>
                        {zoneRange ? `${zoneRange[0]}-${zoneRange[1]} bpm` : 'N/A'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: '600', fontSize: '14px', color: '#374151' }}>
                        {minutes.toFixed(1)} min
                      </div>
                      <div style={{ fontSize: '11px', color: '#6b7280' }}>
                        {percentage}%
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
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

          {/* Left Y-axis (TSS) - only if needed */}
          {needsTssAxis && (
            <>
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
                    x={padding.left - 15}
                    y={y + 4}
                    textAnchor="end"
                    fontSize="11"
                    fill="#64748b"
                  >
                    {tss}
                  </text>
                );
              })}

              {/* TSS Axis title */}
              <text
                x={padding.left - 40}
                y={height / 2}
                textAnchor="middle"
                transform={`rotate(-90, ${padding.left - 40}, ${height / 2})`}
                fontSize="14"
                fill="#374151"
                fontWeight="600"
              >
                TSS/d
              </text>
            </>
          )}

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
  const [timeframe, setTimeframe] = useState(30); // days



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
    
    // Calculate date range based on week offset and timeframe
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() + (weekOffset * 7) - timeframe);
    const endDate = new Date(today);
    endDate.setDate(today.getDate() + (weekOffset * 7) + 7);
    
    const start = startDate.toISOString().slice(0, 10);
    const end = endDate.toISOString().slice(0, 10);
    
    // Fetch PMC data with timeframe parameter
    const fetchPMCData = fetch(`http://localhost:8000/api/metrics/pmc?athlete_id=${athleteId}&start_date=${start}&end_date=${end}&days=${timeframe}`)
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
  }, [athleteId, weekOffset, timeframe]);

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
            <p>Your training load and readiness {formatWeekDisplay()} (Timeframe: {timeframe} days)</p>
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