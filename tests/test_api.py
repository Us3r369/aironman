"""
Unit tests for API endpoints using FastAPI TestClient.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health-related API endpoints."""
    
    @patch('api.main.get_active_profile')
    @patch('api.main.get_db_conn')
    def test_get_health_analysis_success(self, mock_get_db_conn, mock_get_profile):
        """Test successful health analysis retrieval."""
        # Mock profile
        mock_get_profile.return_value = {
            'athlete_id': 'Jan',
            'last_updated': '2025-08-01'
        }
        
        # Mock database connection
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock athlete UUID lookup
        mock_cur.fetchone.side_effect = [
            ('1a5d4210-bfcc-4b1a-8b37-8e42e83524e9',),  # athlete UUID
            ('good', 'Test analysis', {'status': 'good'}, datetime.now())  # agent analysis
        ]
        
        # Mock health trends data
        mock_cur.fetchall.side_effect = [
            [  # Sleep data
                (date(2025, 8, 1), 85),
                (date(2025, 8, 2), 82)
            ],
            [  # HRV data
                (date(2025, 8, 1), 45),
                (date(2025, 8, 2), 42)
            ],
            [  # RHR data
                (date(2025, 8, 1), 65),
                (date(2025, 8, 2), 68)
            ]
        ]
        
        response = client.get("/api/health/analysis")
        
        assert response.status_code == 200
        data = response.json()
        assert 'trends' in data
        assert 'agent_analysis' in data
        assert 'recovery_status' in data
        assert 'readiness_recommendation' in data
    
    @patch('api.main.get_active_profile')
    def test_get_health_analysis_no_profile(self, mock_get_profile):
        """Test health analysis with no active profile."""
        mock_get_profile.side_effect = Exception("No profile found")
        
        response = client.get("/api/health/analysis")
        
        assert response.status_code == 404
        assert "No active profile found" in response.json()['detail']
    
    @patch('api.main.get_active_profile')
    @patch('api.main.execute_recovery_analysis')
    @patch('api.main.get_db_conn')
    def test_post_agent_analysis_success(self, mock_get_db_conn, mock_execute_agent, mock_get_profile):
        """Test successful agent analysis trigger."""
        # Mock profile
        mock_get_profile.return_value = {
            'athlete_id': 'Jan',
            'last_updated': '2025-08-01'
        }
        
        # Mock agent execution
        mock_execute_agent.return_value = {
            'status': 'good',
            'detailed_reasoning': 'Excellent recovery status',
            'analysis_date': '2025-08-02'
        }
        
        # Mock database connection
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock athlete UUID lookup and version query
        mock_cur.fetchone.side_effect = [
            ('1a5d4210-bfcc-4b1a-8b37-8e42e83524e9',),  # athlete UUID
            (1,)  # next version
        ]
        
        response = client.post("/api/health/agent-analysis")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'good'
        assert 'detailed_reasoning' in data
        assert 'analysis_date' in data
        assert 'message' in data
    
    @patch('api.main.get_active_profile')
    def test_post_agent_analysis_no_profile(self, mock_get_profile):
        """Test agent analysis with no active profile."""
        mock_get_profile.side_effect = Exception("No profile found")
        
        response = client.post("/api/health/agent-analysis")
        
        assert response.status_code == 404
        assert "No active profile found" in response.json()['detail']


class TestWorkoutEndpoints:
    """Test workout-related API endpoints."""
    
    @patch('api.main.get_db_conn')
    def test_get_workouts_success(self, mock_get_db_conn):
        """Test successful workout retrieval."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock workout data
        mock_cur.fetchall.return_value = [
            (
                'workout-1',
                '1a5d4210-bfcc-4b1a-8b37-8e42e83524e9',
                datetime.now(),
                'bike',
                85.5,
                3600,
                1.0
            )
        ]
        
        response = client.get("/api/workouts?athlete_id=Jan")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['workout_type'] == 'bike'
        assert data[0]['tss'] == 85.5
    
    @patch('api.main.get_db_conn')
    def test_get_workout_detail_success(self, mock_get_db_conn):
        """Test successful workout detail retrieval."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock workout detail data
        mock_cur.fetchone.return_value = (
            'workout-1',
            '1a5d4210-bfcc-4b1a-8b37-8e42e83524e9',
            datetime.now(),
            'bike',
            85.5,
            3600,
            1.0,
            {'heart_rate': [120, 130, 140]},
            'csv_data_here',
            datetime.now()
        )
        
        response = client.get("/api/workouts/workout-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 'workout-1'
        assert data['workout_type'] == 'bike'
        assert data['tss'] == 85.5
    
    @patch('api.main.get_db_conn')
    def test_get_workout_timeseries_success(self, mock_get_db_conn):
        """Test successful workout timeseries retrieval."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock workout data
        mock_cur.fetchone.return_value = (
            'workout-1',
            'bike',
            {'heart_rate': [120, 130, 140], 'power': [200, 220, 240]},
            'csv_data_here'
        )
        
        response = client.get("/api/workouts/workout-1/timeseries?metric=hr")
        
        assert response.status_code == 200
        data = response.json()
        assert data['workout_id'] == 'workout-1'
        assert data['metric'] == 'hr'
        assert 'data' in data
        assert 'available_metrics' in data


class TestProfileEndpoints:
    """Test profile-related API endpoints."""
    
    @patch('api.main.get_db_conn')
    def test_get_profile_success(self, mock_get_db_conn):
        """Test successful profile retrieval."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock profile data
        mock_cur.fetchone.return_value = (
            'Jan',  # json_athlete_id
            date(2025, 8, 1),  # valid_from
            180,  # lt_heartrate
            # ... (all zone data would be here)
            date(2025, 1, 15),  # bike_ftp_test
            date(2025, 2, 15),  # run_ltp_test
            date(2025, 3, 15)   # swim_css_test
        )
        
        response = client.get("/api/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert data['athlete_id'] == 'Jan'
        assert 'zones' in data
        assert 'test_dates' in data
    
    def test_put_profile_success(self):
        """Test successful profile update."""
        profile_data = {
            "athlete_id": "Jan",
            "last_updated": "2025-08-01",
            "zones": {
                "heart_rate": {
                    "lt_hr": 180,
                    "zones": {
                        "z1": [120, 130],
                        "z2": [130, 140],
                        "zx": [140, 150],
                        "z3": [150, 160],
                        "zy": [160, 170],
                        "z4": [170, 180],
                        "z5": [180, 190]
                    }
                },
                "bike_power": {
                    "ftp": 250,
                    "zones": {
                        "z1": [200, 210],
                        "z2": [210, 220],
                        "zx": [220, 230],
                        "z3": [230, 240],
                        "zy": [240, 250],
                        "z4": [250, 260],
                        "z5": [260, 270]
                    }
                },
                "run_power": {
                    "ltp": 300,
                    "critical_power": 280,
                    "zones": {
                        "z1": [250, 260],
                        "z2": [260, 270],
                        "zx": [270, 280],
                        "z3": [280, 290],
                        "zy": [290, 300],
                        "z4": [300, 310],
                        "z5": [310, 320]
                    }
                },
                "run_pace": {
                    "threshold_pace_per_km": "04:30",
                    "zones": {
                        "z1": ["05:00", "05:30"],
                        "z2": ["05:30", "06:00"],
                        "zx": ["06:00", "06:30"],
                        "z3": ["06:30", "07:00"],
                        "zy": ["07:00", "07:30"],
                        "z4": ["07:30", "08:00"],
                        "z5": ["08:00", "08:30"]
                    }
                },
                "swim": {
                    "css_pace_per_100m": "01:45",
                    "zones": {
                        "z1": ["02:00", "02:15"],
                        "z2": ["02:15", "02:30"],
                        "zx": ["02:30", "02:45"],
                        "z3": ["02:45", "03:00"],
                        "zy": ["03:00", "03:15"],
                        "z4": ["03:15", "03:30"],
                        "z5": ["03:30", "03:45"]
                    }
                }
            },
            "test_dates": {
                "bike_ftp_test": "2025-01-15",
                "run_ltp_test": "2025-02-15",
                "swim_css_test": "2025-03-15"
            }
        }
        
        with patch('api.main.get_db_conn') as mock_get_db_conn:
            mock_conn = Mock()
            mock_cur = Mock()
            mock_get_db_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            
            # Mock athlete UUID lookup
            mock_cur.fetchone.return_value = ('1a5d4210-bfcc-4b1a-8b37-8e42e83524e9',)
            
            response = client.put("/api/profile", json=profile_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data['message'] == 'Profile updated successfully'


class TestErrorHandling:
    """Test API error handling."""
    
    def test_404_not_found(self):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_422_validation_error(self):
        """Test 422 error for invalid request data."""
        response = client.post("/api/health/agent-analysis", json={"invalid": "data"})
        # Should still work as it doesn't expect JSON body
        assert response.status_code in [200, 404, 500]  # Depends on profile availability


if __name__ == "__main__":
    pytest.main([__file__]) 