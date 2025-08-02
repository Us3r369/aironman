"""
Unit tests for the recovery analysis agent and its tools.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from agents.recovery_analysis_agent import (
    get_athlete_uuid,
    HealthMetricsTool,
    TrainingLoadTool,
    TrendAnalysisTool,
    RecoveryAssessmentTool,
    create_recovery_analysis_agent,
    execute_recovery_analysis
)


class TestGetAthleteUUID:
    """Test the get_athlete_uuid helper function."""
    
    @patch('agents.recovery_analysis_agent.get_db_conn')
    def test_get_athlete_uuid_success(self, mock_get_db_conn):
        """Test successful athlete UUID retrieval."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        
        # Set up context manager mocks properly
        mock_get_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock database response - return a tuple directly
        mock_cur.fetchone.return_value = ('1a5d4210-bfcc-4b1a-8b37-8e42e83524e9',)
        
        result = get_athlete_uuid('Jan')
        
        assert result == '1a5d4210-bfcc-4b1a-8b37-8e42e83524e9'
        mock_cur.execute.assert_called_once_with(
            "SELECT id FROM athlete WHERE name = %s", ('Jan',)
        )
    
    @patch('agents.recovery_analysis_agent.get_db_conn')
    def test_get_athlete_uuid_not_found(self, mock_get_db_conn):
        """Test athlete not found error."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        
        # Set up context manager mocks properly
        mock_get_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        mock_cur.fetchone.return_value = None
        
        with pytest.raises(ValueError, match="Athlete 'Unknown' not found in database"):
            get_athlete_uuid('Unknown')


class TestHealthMetricsTool:
    """Test the HealthMetricsTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = HealthMetricsTool()
    
    @patch('agents.recovery_analysis_agent.get_db_conn')
    def test_health_metrics_tool_success(self, mock_get_db_conn):
        """Test successful health metrics extraction."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        
        # Set up context manager mocks properly
        mock_get_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock RHR data
        mock_cur.fetchall.side_effect = [
            [  # RHR data
                (datetime.now().date(), {'restingHeartRate': 65}),
                ((datetime.now() - timedelta(days=1)).date(), {'restingHeartRate': 68})
            ],
            [  # HRV data
                (datetime.now().date(), {'hrv': 45}),
                ((datetime.now() - timedelta(days=1)).date(), {'hrv': 42})
            ],
            [  # Sleep data
                (datetime.now().date(), {'sleepQuality': 85}),
                ((datetime.now() - timedelta(days=1)).date(), {'sleepQuality': 82})
            ]
        ]
        
        result = self.tool._run('Jan')
        data = json.loads(result)
        
        assert data['analysis_period'] == '7 days'
        assert data['data_quality'] == 'good'
        assert len(data['rhr']) == 2
        assert len(data['hrv']) == 2
        assert len(data['sleep']) == 2
    
    @patch('agents.recovery_analysis_agent.get_db_conn')
    def test_health_metrics_tool_poor_data_quality(self, mock_get_db_conn):
        """Test health metrics with poor data quality."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        
        # Set up context manager mocks properly
        mock_get_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock minimal data
        mock_cur.fetchall.side_effect = [
            [  # RHR data - only 1 point
                (datetime.now().date(), {'restingHeartRate': 65})
            ],
            [],  # No HRV data
            []   # No sleep data
        ]
        
        result = self.tool._run('Jan')
        data = json.loads(result)
        
        assert data['data_quality'] == 'poor'
        assert len(data['rhr']) == 1
        assert len(data['hrv']) == 0
        assert len(data['sleep']) == 0


class TestTrainingLoadTool:
    """Test the TrainingLoadTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = TrainingLoadTool()
    
    @patch('agents.recovery_analysis_agent.get_db_conn')
    def test_training_load_tool_success(self, mock_get_db_conn):
        """Test successful training load extraction."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        
        # Set up context manager mocks properly
        mock_get_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock training status data
        mock_cur.fetchall.side_effect = [
            [  # Training status
                (datetime.now().date(), {'tsb': 15, 'ctl': 80, 'atl': 65}),
                ((datetime.now() - timedelta(days=1)).date(), {'tsb': 12, 'ctl': 78, 'atl': 70})
            ],
            [  # Recent workouts
                (datetime.now(), 'bike', {'tss': 85}),
                ((datetime.now() - timedelta(days=1)), 'run', {'tss': 45})
            ]
        ]
        
        result = self.tool._run('Jan')
        data = json.loads(result)
        
        assert data['load_assessment'] == 'recovery'
        assert data['analysis_period'] == '7 days'
        assert len(data['training_status']) == 2
        assert len(data['recent_workouts']) == 2
        assert data['load_context']['recent_tss'] == 130
        assert data['load_context']['workout_count'] == 2
    
    @patch('agents.recovery_analysis_agent.get_db_conn')
    def test_training_load_tool_high_stress(self, mock_get_db_conn):
        """Test training load with high stress assessment."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        
        # Set up context manager mocks properly
        mock_get_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        
        # Mock high stress data
        mock_cur.fetchall.side_effect = [
            [  # Training status with negative TSB
                (datetime.now().date(), {'tsb': -15, 'ctl': 90, 'atl': 105})
            ],
            []  # No recent workouts
        ]
        
        result = self.tool._run('Jan')
        data = json.loads(result)
        
        assert data['load_assessment'] == 'high_stress'


class TestTrendAnalysisTool:
    """Test the TrendAnalysisTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = TrendAnalysisTool()
    
    def test_trend_analysis_tool_improving_rhr(self):
        """Test trend analysis with improving RHR."""
        health_metrics = {
            "rhr": [
                {"date": "2025-08-01", "value": 70, "unit": "bpm"},
                {"date": "2025-08-02", "value": 68, "unit": "bpm"},
                {"date": "2025-08-03", "value": 65, "unit": "bpm"}
            ],
            "hrv": [
                {"date": "2025-08-01", "value": 40, "unit": "ms"},
                {"date": "2025-08-02", "value": 42, "unit": "ms"},
                {"date": "2025-08-03", "value": 45, "unit": "ms"}
            ],
            "sleep": [
                {"date": "2025-08-01", "value": 80, "unit": "score"},
                {"date": "2025-08-02", "value": 82, "unit": "score"},
                {"date": "2025-08-03", "value": 85, "unit": "score"}
            ]
        }
        
        result = self.tool._run(json.dumps(health_metrics))
        data = json.loads(result)
        
        assert data['rhr_trend']['direction'] == 'improving'
        assert data['hrv_trend']['direction'] == 'improving'
        assert data['sleep_trend']['direction'] == 'improving'
        assert data['overall_trend'] == 'improving'
    
    def test_trend_analysis_tool_declining_metrics(self):
        """Test trend analysis with declining metrics."""
        health_metrics = {
            "rhr": [
                {"date": "2025-08-01", "value": 65, "unit": "bpm"},
                {"date": "2025-08-02", "value": 68, "unit": "bpm"},
                {"date": "2025-08-03", "value": 72, "unit": "bpm"}
            ],
            "hrv": [
                {"date": "2025-08-01", "value": 45, "unit": "ms"},
                {"date": "2025-08-02", "value": 42, "unit": "ms"},
                {"date": "2025-08-03", "value": 38, "unit": "ms"}
            ],
            "sleep": [
                {"date": "2025-08-01", "value": 85, "unit": "score"},
                {"date": "2025-08-02", "value": 82, "unit": "score"},
                {"date": "2025-08-03", "value": 78, "unit": "score"}
            ]
        }
        
        result = self.tool._run(json.dumps(health_metrics))
        data = json.loads(result)
        
        assert data['rhr_trend']['direction'] == 'declining'
        assert data['hrv_trend']['direction'] == 'declining'
        assert data['sleep_trend']['direction'] == 'declining'
        assert data['overall_trend'] == 'declining'
    
    def test_trend_analysis_tool_insufficient_data(self):
        """Test trend analysis with insufficient data."""
        health_metrics = {
            "rhr": [
                {"date": "2025-08-01", "value": 65, "unit": "bpm"}
            ],
            "hrv": [],
            "sleep": []
        }
        
        result = self.tool._run(json.dumps(health_metrics))
        data = json.loads(result)
        
        assert data['rhr_trend']['direction'] == 'insufficient_data'
        assert data['hrv_trend']['direction'] == 'insufficient_data'
        assert data['sleep_trend']['direction'] == 'insufficient_data'
        assert data['overall_trend'] == 'insufficient_data'


class TestRecoveryAssessmentTool:
    """Test the RecoveryAssessmentTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = RecoveryAssessmentTool()
    
    def test_recovery_assessment_good_status(self):
        """Test recovery assessment with good status."""
        health_metrics = {
            "rhr": [{"date": "2025-08-01", "value": 65, "unit": "bpm"}],
            "hrv": [{"date": "2025-08-01", "value": 45, "unit": "ms"}],
            "sleep": [{"date": "2025-08-01", "value": 85, "unit": "score"}],
            "data_quality": "good"
        }
        
        training_load = {
            "load_assessment": "recovery",
            "load_context": {"tsb": 15, "ctl": 80, "atl": 65}
        }
        
        trend_analysis = {
            "rhr_trend": {"direction": "improving", "change_percent": -5.0},
            "hrv_trend": {"direction": "improving", "change_percent": 10.0},
            "sleep_trend": {"direction": "improving", "change_percent": 8.0},
            "acute_changes": []
        }
        
        result = self.tool._run(
            json.dumps(health_metrics),
            json.dumps(training_load),
            json.dumps(trend_analysis)
        )
        data = json.loads(result)
        
        assert data['status'] == 'good'
        assert data['score'] >= 60
        assert 'improving' in data['detailed_reasoning']
    
    def test_recovery_assessment_bad_status(self):
        """Test recovery assessment with bad status."""
        health_metrics = {
            "rhr": [{"date": "2025-08-01", "value": 75, "unit": "bpm"}],
            "hrv": [{"date": "2025-08-01", "value": 35, "unit": "ms"}],
            "sleep": [{"date": "2025-08-01", "value": 70, "unit": "score"}],
            "data_quality": "good"
        }
        
        training_load = {
            "load_assessment": "high_stress",
            "load_context": {"tsb": -15, "ctl": 90, "atl": 105}
        }
        
        trend_analysis = {
            "rhr_trend": {"direction": "declining", "change_percent": 10.0},
            "hrv_trend": {"direction": "declining", "change_percent": -15.0},
            "sleep_trend": {"direction": "declining", "change_percent": -12.0},
            "acute_changes": [{"metric": "RHR", "change": "spike"}]
        }
        
        result = self.tool._run(
            json.dumps(health_metrics),
            json.dumps(training_load),
            json.dumps(trend_analysis)
        )
        data = json.loads(result)
        
        assert data['status'] == 'bad'
        assert data['score'] < 30
        assert 'rest day' in data['detailed_reasoning']


class TestRecoveryAnalysisAgent:
    """Test the complete recovery analysis agent."""
    
    @patch('agents.recovery_analysis_agent.get_db_conn')
    def test_execute_recovery_analysis_success(self, mock_get_db_conn):
        """Test successful recovery analysis execution."""
        # Mock database connections for all tools
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        
        # Set up context manager mocks properly
        mock_get_db_conn.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value = mock_cur
        mock_cur.__enter__.return_value = mock_cur
        mock_cur.__exit__.return_value = None
        
        # Mock health data
        mock_cur.fetchall.side_effect = [
            [  # RHR data
                (datetime.now().date(), {'restingHeartRate': 65})
            ],
            [  # HRV data
                (datetime.now().date(), {'hrv': 45})
            ],
            [  # Sleep data
                (datetime.now().date(), {'sleepQuality': 85})
            ],
            [  # Training status
                (datetime.now().date(), {'tsb': 10, 'ctl': 80, 'atl': 70})
            ],
            []  # No recent workouts
        ]
        
        result = execute_recovery_analysis('Jan')
        
        assert 'status' in result
        assert 'detailed_reasoning' in result
        assert 'analysis_date' in result
        assert result['status'] in ['good', 'medium', 'bad']
    
    @patch('agents.recovery_analysis_agent.get_db_conn')
    def test_execute_recovery_analysis_athlete_not_found(self, mock_get_db_conn):
        """Test recovery analysis with athlete not found."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        
        # Set up context manager mocks properly
        mock_get_db_conn.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value = mock_cur
        mock_cur.__enter__.return_value = mock_cur
        mock_cur.__exit__.return_value = None
        
        # Mock athlete not found
        mock_cur.fetchone.return_value = None
        
        result = execute_recovery_analysis('Unknown')
        
        assert result['status'] == 'unknown'
        assert 'Unable to retrieve data' in result['detailed_reasoning']


if __name__ == "__main__":
    pytest.main([__file__]) 