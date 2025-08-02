"""
Unit tests for services modules.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from services.pmc_metrics import calculate_pmc_metrics
from services.zone_database import get_athlete_zones
from services.garmin_auth import get_garmin_credentials
from services.sync import sync_last_n_days, sync_since_last_entry


class TestPMCMetrics:
    """Test PMC (Performance Management Chart) metrics calculation."""
    
    def test_calculate_pmc_metrics_no_workouts(self):
        """Test PMC calculation with no workouts."""
        workouts = []
        
        result = calculate_pmc_metrics(workouts)
        
        assert 'metrics' in result
        assert 'summary' in result
        assert len(result['metrics']) == 0
        assert result['summary']['ctl'] == 0
        assert result['summary']['atl'] == 0
        assert result['summary']['tsb'] == 0
    
    def test_calculate_pmc_metrics_single_workout(self):
        """Test PMC calculation with single workout."""
        workouts = [
            {
                'timestamp': datetime.now(),
                'tss': 85.5,
                'duration_sec': 3600
            }
        ]
        
        result = calculate_pmc_metrics(workouts)
        
        assert 'metrics' in result
        assert 'summary' in result
        assert len(result['metrics']) > 0
        assert result['summary']['ctl'] > 0
        assert result['summary']['atl'] > 0
        assert 'tsb' in result['summary']
    
    def test_calculate_pmc_metrics_multiple_workouts(self):
        """Test PMC calculation with multiple workouts."""
        base_time = datetime.now()
        workouts = [
            {
                'timestamp': base_time - timedelta(days=7),
                'tss': 85.5,
                'duration_sec': 3600
            },
            {
                'timestamp': base_time - timedelta(days=5),
                'tss': 65.2,
                'duration_sec': 2700
            },
            {
                'timestamp': base_time - timedelta(days=3),
                'tss': 95.8,
                'duration_sec': 4200
            },
            {
                'timestamp': base_time - timedelta(days=1),
                'tss': 45.3,
                'duration_sec': 1800
            }
        ]
        
        result = calculate_pmc_metrics(workouts)
        
        assert 'metrics' in result
        assert 'summary' in result
        assert len(result['metrics']) > 0
        assert result['summary']['ctl'] > 0
        assert result['summary']['atl'] > 0
        assert 'tsb' in result['summary']
    
    def test_calculate_pmc_metrics_with_zero_tss(self):
        """Test PMC calculation with zero TSS workouts."""
        workouts = [
            {
                'timestamp': datetime.now(),
                'tss': 0,
                'duration_sec': 3600
            }
        ]
        
        result = calculate_pmc_metrics(workouts)
        
        assert 'metrics' in result
        assert 'summary' in result
        # Should handle zero TSS gracefully
        assert len(result['metrics']) >= 0


class TestZoneDatabase:
    """Test zone database functions."""
    
    @patch('services.zone_database.get_db_conn')
    def test_get_athlete_zones_success(self, mock_get_db_conn):
        """Test successful athlete zones retrieval."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock zone data
        mock_cur.fetchone.return_value = (
            180,  # lt_heartrate
            120, 130,  # hr_zone_z1
            130, 140,  # hr_zone_z2
            140, 150,  # hr_zone_zx
            150, 160,  # hr_zone_z3
            160, 170,  # hr_zone_zy
            170, 180,  # hr_zone_z4
            180, 190,  # hr_zone_z5
            250,  # bike_ftp_power
            200, 210,  # bike_power_zone_z1
            210, 220,  # bike_power_zone_z2
            220, 230,  # bike_power_zone_zx
            230, 240,  # bike_power_zone_z3
            240, 250,  # bike_power_zone_zy
            250, 260,  # bike_power_zone_z4
            260, 270   # bike_power_zone_z5
        )
        
        result = get_athlete_zones('Jan')
        
        assert 'heart_rate' in result
        assert 'power' in result
        assert result['heart_rate']['lt_hr'] == 180
        assert result['power']['ftp'] == 250
        assert len(result['heart_rate']['zones']) == 6
        assert len(result['power']['zones']) == 6
    
    @patch('services.zone_database.get_db_conn')
    def test_get_athlete_zones_not_found(self, mock_get_db_conn):
        """Test athlete zones not found."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        mock_cur.fetchone.return_value = None
        
        with pytest.raises(Exception):
            get_athlete_zones('Unknown')


class TestGarminAuth:
    """Test Garmin authentication functions."""
    
    @patch('services.garmin_auth.os.getenv')
    def test_get_garmin_credentials_success(self, mock_getenv):
        """Test successful Garmin credentials retrieval."""
        mock_getenv.side_effect = lambda key: {
            'GARMIN_EMAIL': 'test@example.com',
            'GARMIN_PASSWORD': 'testpassword'
        }.get(key)
        
        credentials = get_garmin_credentials()
        
        assert credentials['email'] == 'test@example.com'
        assert credentials['password'] == 'testpassword'
    
    @patch('services.garmin_auth.os.getenv')
    def test_get_garmin_credentials_missing_email(self, mock_getenv):
        """Test missing Garmin email."""
        mock_getenv.side_effect = lambda key: {
            'GARMIN_PASSWORD': 'testpassword'
        }.get(key)
        
        with pytest.raises(ValueError, match="Garmin email not found"):
            get_garmin_credentials()
    
    @patch('services.garmin_auth.os.getenv')
    def test_get_garmin_credentials_missing_password(self, mock_getenv):
        """Test missing Garmin password."""
        mock_getenv.side_effect = lambda key: {
            'GARMIN_EMAIL': 'test@example.com'
        }.get(key)
        
        with pytest.raises(ValueError, match="Garmin password not found"):
            get_garmin_credentials()


class TestSyncServices:
    """Test sync service functions."""
    
    @patch('services.sync.get_db_conn')
    @patch('services.sync.get_garmin_credentials')
    def test_sync_last_n_days_success(self, mock_get_credentials, mock_get_db_conn):
        """Test successful sync of last N days."""
        # Mock credentials
        mock_get_credentials.return_value = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        
        # Mock database connection
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock no existing workouts
        mock_cur.fetchone.return_value = None
        
        # Mock Garmin API response (simplified)
        with patch('services.sync.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'workouts': [
                    {
                        'id': 'workout-1',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'bike',
                        'tss': 85.5,
                        'duration': 3600
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            result = sync_last_n_days(7)
            
            assert result is True
    
    @patch('services.sync.get_db_conn')
    def test_sync_since_last_entry_success(self, mock_get_db_conn):
        """Test successful sync since last entry."""
        # Mock database connection
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock last workout timestamp
        mock_cur.fetchone.return_value = (datetime.now() - timedelta(days=1),)
        
        # Mock Garmin API response
        with patch('services.sync.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'workouts': [
                    {
                        'id': 'workout-2',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'run',
                        'tss': 65.2,
                        'duration': 2700
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            result = sync_since_last_entry()
            
            assert result is True
    
    @patch('services.sync.get_db_conn')
    def test_sync_no_new_workouts(self, mock_get_db_conn):
        """Test sync when no new workouts are available."""
        # Mock database connection
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock last workout timestamp
        mock_cur.fetchone.return_value = (datetime.now(),)
        
        # Mock empty Garmin API response
        with patch('services.sync.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {'workouts': []}
            mock_get.return_value = mock_response
            
            result = sync_since_last_entry()
            
            assert result is True  # Should still return True for no new workouts


class TestPreprocessServices:
    """Test preprocessing services."""
    
    def test_extract_workout_targets_from_fit_bike(self):
        """Test extracting workout targets from bike FIT file."""
        # This test would require a mock FIT file
        # For now, we'll test the function signature and basic behavior
        from services.preprocess import extract_workout_targets_from_fit
        
        # Mock FIT file path
        mock_fit_path = Mock()
        mock_fit_path.exists.return_value = True
        
        with patch('services.preprocess.fitparse.FitFile') as mock_fitfile:
            mock_fitfile.return_value.get_messages.return_value = []
            
            result = extract_workout_targets_from_fit(mock_fit_path)
            
            assert isinstance(result, dict)
            assert 'workout_steps' in result
    
    def test_map_targets_to_timestamps_bike(self):
        """Test mapping targets to timestamps for bike workouts."""
        from services.preprocess import map_targets_to_timestamps
        
        # Mock trackpoints
        trackpoints = [
            {
                'timestamp': '2025-08-01T10:00:00Z',
                'heart_rate': 120,
                'power': 200
            },
            {
                'timestamp': '2025-08-01T10:01:00Z',
                'heart_rate': 130,
                'power': 220
            }
        ]
        
        # Mock target info
        target_info = {
            'workout_steps': [
                {
                    'message_index': 0,
                    'duration_type': 'time',
                    'duration_value': 60000,  # 1 minute
                    'target_type': 'power_3s',
                    'custom_target_value_low': 200,
                    'custom_target_value_high': 250,
                    'intensity': 'active'
                }
            ]
        }
        
        result = map_targets_to_timestamps(trackpoints, target_info, 'bike')
        
        assert len(result) == 2
        assert 'target_power_low' in result[0]
        assert 'target_power_high' in result[0]
        assert 'workout_intensity' in result[0]
        assert result[0]['target_power_low'] == 200
        assert result[0]['target_power_high'] == 250
        assert result[0]['workout_intensity'] == 'active'
    
    def test_extract_swim_targets_from_step_name(self):
        """Test extracting swim targets from step name."""
        from services.preprocess import extract_swim_targets_from_step_name
        
        # Test various swim step names
        test_cases = [
            ("100m @ 1:45/100m", {"distance": 100, "pace": "1:45"}),
            ("200m @ 2:00/100m", {"distance": 200, "pace": "2:00"}),
            ("50m @ 1:30/100m", {"distance": 50, "pace": "1:30"}),
            ("400m @ 2:15/100m", {"distance": 400, "pace": "2:15"})
        ]
        
        for step_name, expected in test_cases:
            result = extract_swim_targets_from_step_name(step_name)
            assert result['distance'] == expected['distance']
            assert result['pace'] == expected['pace']
    
    def test_extract_swim_targets_invalid_format(self):
        """Test extracting swim targets with invalid format."""
        from services.preprocess import extract_swim_targets_from_step_name
        
        # Test invalid formats
        invalid_cases = [
            "Invalid format",
            "100m",
            "@ 1:45/100m",
            "100m @ invalid",
            ""
        ]
        
        for step_name in invalid_cases:
            result = extract_swim_targets_from_step_name(step_name)
            assert result is None or (result.get('distance') is None and result.get('pace') is None)


if __name__ == "__main__":
    pytest.main([__file__]) 