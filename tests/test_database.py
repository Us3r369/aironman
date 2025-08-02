"""
Unit tests for database utilities and functions.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from utils.database import (
    get_db_conn,
    get_active_profile,
    test_recovery_analysis_table
)
from utils.exceptions import ProfileNotFoundException, DatabaseException


class TestDatabaseConnection:
    """Test database connection utilities."""
    
    @patch('utils.database.psycopg2.connect')
    def test_get_db_conn_success(self, mock_connect):
        """Test successful database connection."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with get_db_conn() as conn:
            assert conn == mock_conn
        
        mock_connect.assert_called_once()
    
    @patch('utils.database.psycopg2.connect')
    def test_get_db_conn_failure(self, mock_connect):
        """Test database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")
        
        with pytest.raises(DatabaseException):
            with get_db_conn():
                pass


class TestGetActiveProfile:
    """Test the get_active_profile function."""
    
    @patch('utils.database.get_db_conn')
    def test_get_active_profile_success(self, mock_get_db_conn):
        """Test successful profile retrieval."""
        # Mock database connection
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock profile data
        mock_cur.fetchone.return_value = (
            'Jan',  # json_athlete_id
            date(2025, 8, 1),  # valid_from
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
            260, 270,  # bike_power_zone_z5
            300,  # run_ltp_power
            280,  # run_critical_power
            250, 260,  # run_power_zone_z1
            260, 270,  # run_power_zone_z2
            270, 280,  # run_power_zone_zx
            280, 290,  # run_power_zone_z3
            290, 300,  # run_power_zone_zy
            300, 310,  # run_power_zone_z4
            310, 320,  # run_power_zone_z5
            '04:30',  # run_threshold_pace
            '05:00', '05:30',  # run_pace_zone_z1
            '05:30', '06:00',  # run_pace_zone_z2
            '06:00', '06:30',  # run_pace_zone_zx
            '06:30', '07:00',  # run_pace_zone_z3
            '07:00', '07:30',  # run_pace_zone_zy
            '07:30', '08:00',  # run_pace_zone_z4
            '08:00', '08:30',  # run_pace_zone_z5
            '01:45',  # swim_css_pace_per_100
            '02:00', '02:15',  # swim_zone_z1
            '02:15', '02:30',  # swim_zone_z2
            '02:30', '02:45',  # swim_zone_zx
            '02:45', '03:00',  # swim_zone_z3
            '03:00', '03:15',  # swim_zone_zy
            '03:15', '03:30',  # swim_zone_z4
            '03:30', '03:45',  # swim_zone_z5
            date(2025, 1, 15),  # bike_ftp_test
            date(2025, 2, 15),  # run_ltp_test
            date(2025, 3, 15)   # swim_css_test
        )
        
        profile = get_active_profile()
        
        assert profile['athlete_id'] == 'Jan'
        assert profile['last_updated'] == '2025-08-01'
        assert profile['zones']['heart_rate']['lt_hr'] == 180
        assert profile['zones']['bike_power']['ftp'] == 250
        assert profile['zones']['run_power']['ltp'] == 300
        assert profile['zones']['run_power']['critical_power'] == 280
        assert profile['zones']['run_pace']['threshold_pace_per_km'] == '04:30'
        assert profile['zones']['swim']['css_pace_per_100m'] == '01:45'
        assert profile['test_dates']['bike_ftp_test'] == '2025-01-15'
        assert profile['test_dates']['run_ltp_test'] == '2025-02-15'
        assert profile['test_dates']['swim_css_test'] == '2025-03-15'
    
    @patch('utils.database.get_db_conn')
    def test_get_active_profile_not_found(self, mock_get_db_conn):
        """Test profile not found error."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        mock_cur.fetchone.return_value = None
        
        with pytest.raises(ProfileNotFoundException):
            get_active_profile()
    
    @patch('utils.database.get_db_conn')
    def test_get_active_profile_database_error(self, mock_get_db_conn):
        """Test database error handling."""
        mock_get_db_conn.side_effect = Exception("Database error")
        
        with pytest.raises(DatabaseException):
            get_active_profile()


class TestRecoveryAnalysisTable:
    """Test the recovery analysis table utilities."""
    
    @patch('utils.database.get_db_conn')
    def test_recovery_analysis_table_exists(self, mock_get_db_conn):
        """Test recovery analysis table exists."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock table exists
        mock_cur.fetchone.return_value = (True,)
        
        result = test_recovery_analysis_table()
        
        assert result is True
        mock_cur.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('utils.database.get_db_conn')
    def test_recovery_analysis_table_not_exists(self, mock_get_db_conn):
        """Test recovery analysis table does not exist."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock table does not exist
        mock_cur.fetchone.return_value = (False,)
        
        result = test_recovery_analysis_table()
        
        assert result is False
        mock_cur.execute.assert_called()
        mock_conn.commit.assert_not_called()


class TestDatabaseErrorHandling:
    """Test database error handling scenarios."""
    
    @patch('utils.database.get_db_conn')
    def test_database_connection_error(self, mock_get_db_conn):
        """Test database connection error."""
        mock_get_db_conn.side_effect = Exception("Connection failed")
        
        with pytest.raises(DatabaseException):
            get_active_profile()
    
    @patch('utils.database.get_db_conn')
    def test_database_query_error(self, mock_get_db_conn):
        """Test database query error."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock query error
        mock_cur.execute.side_effect = Exception("Query failed")
        
        with pytest.raises(DatabaseException):
            get_active_profile()


class TestProfileDataValidation:
    """Test profile data validation and formatting."""
    
    @patch('utils.database.get_db_conn')
    def test_profile_with_null_test_dates(self, mock_get_db_conn):
        """Test profile with null test dates."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock profile data with null test dates
        mock_cur.fetchone.return_value = (
            'Jan',  # json_athlete_id
            date(2025, 8, 1),  # valid_from
            180,  # lt_heartrate
            # ... (all zone data)
            None,  # bike_ftp_test
            None,  # run_ltp_test
            None   # swim_css_test
        )
        
        profile = get_active_profile()
        
        assert profile['test_dates']['bike_ftp_test'] is None
        assert profile['test_dates']['run_ltp_test'] is None
        assert profile['test_dates']['swim_css_test'] is None
    
    @patch('utils.database.get_db_conn')
    def test_profile_with_mixed_test_dates(self, mock_get_db_conn):
        """Test profile with some test dates and some null."""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        # Mock profile data with mixed test dates
        mock_cur.fetchone.return_value = (
            'Jan',  # json_athlete_id
            date(2025, 8, 1),  # valid_from
            180,  # lt_heartrate
            # ... (all zone data)
            date(2025, 1, 15),  # bike_ftp_test
            None,  # run_ltp_test
            date(2025, 3, 15)   # swim_css_test
        )
        
        profile = get_active_profile()
        
        assert profile['test_dates']['bike_ftp_test'] == '2025-01-15'
        assert profile['test_dates']['run_ltp_test'] is None
        assert profile['test_dates']['swim_css_test'] == '2025-03-15'


if __name__ == "__main__":
    pytest.main([__file__]) 