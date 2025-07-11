import pytest
from pathlib import Path
from services.preprocess import (
    extract_workout_targets_from_fit, 
    map_targets_to_timestamps,
    extract_swim_targets_from_step_name
)


def test_extract_workout_targets_from_fit_bike():
    """
    Test that extract_workout_targets_from_fit correctly extracts target info from a real bike FIT file.
    """
    fit_path = Path("bike_workout.fit")
    assert fit_path.exists(), "Test FIT file does not exist!"
    
    target_info = extract_workout_targets_from_fit(fit_path)
    
    # There should be at least one workout step with target info
    steps = target_info.get("workout_steps", [])
    assert len(steps) > 0, "No workout steps found"
    
    # Check that at least one step has target information
    has_targets = False
    for step in steps:
        if (step.get("target_type") is not None or 
            step.get("custom_target_value_low") is not None or 
            step.get("custom_target_value_high") is not None):
            has_targets = True
            break
    
    assert has_targets, "No target information found in workout steps"
    
    # Check that step_timing is extracted
    assert "step_timing" in target_info, "Step timing information not extracted"


def test_map_targets_to_timestamps_bike():
    """
    Test that map_targets_to_timestamps correctly maps bike power targets to timestamps.
    """
    # Mock trackpoints with timestamps
    trackpoints = [
        {"timestamp": "2025-07-02T16:09:37.000Z", "heart_rate": 89, "power": 100},
        {"timestamp": "2025-07-02T16:09:38.000Z", "heart_rate": 92, "power": 120},
        {"timestamp": "2025-07-02T16:09:39.000Z", "heart_rate": 93, "power": 140},
    ]
    
    # Mock target info with workout steps
    target_info = {
        "workout_steps": [
            {
                "message_index": 0,
                "duration_type": "time",
                "duration_value": 2000,  # 2 seconds in milliseconds
                "target_type": "power_3s",
                "custom_target_value_low": 100,
                "custom_target_value_high": 150,
                "intensity": "warmup"
            },
            {
                "message_index": 1,
                "duration_type": "time", 
                "duration_value": 1000,  # 1 second in milliseconds
                "target_type": "power_3s",
                "custom_target_value_low": 150,
                "custom_target_value_high": 200,
                "intensity": "active"
            }
        ]
    }
    
    enhanced_trackpoints = map_targets_to_timestamps(trackpoints, target_info, "bike")
    
    # Check that targets were mapped correctly
    assert len(enhanced_trackpoints) == 3
    
    # First two points should have warmup targets
    assert enhanced_trackpoints[0]["target_power_low"] == 100
    assert enhanced_trackpoints[0]["target_power_high"] == 150
    assert enhanced_trackpoints[0]["workout_intensity"] == "warmup"
    assert enhanced_trackpoints[0]["workout_step_index"] == 0
    
    assert enhanced_trackpoints[1]["target_power_low"] == 100
    assert enhanced_trackpoints[1]["target_power_high"] == 150
    assert enhanced_trackpoints[1]["workout_intensity"] == "warmup"
    assert enhanced_trackpoints[1]["workout_step_index"] == 0
    
    # Third point should have active targets
    assert enhanced_trackpoints[2]["target_power_low"] == 150
    assert enhanced_trackpoints[2]["target_power_high"] == 200
    assert enhanced_trackpoints[2]["workout_intensity"] == "active"
    assert enhanced_trackpoints[2]["workout_step_index"] == 1


def test_map_targets_to_timestamps_run():
    """
    Test that map_targets_to_timestamps correctly maps run pace targets to timestamps.
    """
    # Mock trackpoints with timestamps
    trackpoints = [
        {"timestamp": "2025-07-02T16:09:37.000Z", "heart_rate": 89, "speed": 2.5},
        {"timestamp": "2025-07-02T16:09:38.000Z", "heart_rate": 92, "speed": 3.0},
        {"timestamp": "2025-07-02T16:09:39.000Z", "heart_rate": 93, "speed": 3.5},
    ]
    
    # Mock target info with speed targets (in m/s*1000)
    target_info = {
        "workout_steps": [
            {
                "message_index": 0,
                "duration_type": "time",
                "duration_value": 2000,  # 2 seconds in milliseconds
                "target_type": "speed",
                "custom_target_value_low": 2500,  # 2.5 m/s * 1000
                "custom_target_value_high": 3000,  # 3.0 m/s * 1000
                "intensity": "warmup"
            },
            {
                "message_index": 1,
                "duration_type": "time",
                "duration_value": 1000,  # 1 second in milliseconds
                "target_type": "speed", 
                "custom_target_value_low": 3000,  # 3.0 m/s * 1000
                "custom_target_value_high": 3500,  # 3.5 m/s * 1000
                "intensity": "active"
            }
        ]
    }
    
    enhanced_trackpoints = map_targets_to_timestamps(trackpoints, target_info, "run")
    
    # Check that targets were mapped correctly
    assert len(enhanced_trackpoints) == 3
    
    # First two points should have warmup targets
    assert enhanced_trackpoints[0]["target_speed_low"] == 2500
    assert enhanced_trackpoints[0]["target_speed_high"] == 3000
    assert enhanced_trackpoints[0]["target_pace_high"] == 400.0  # 1000/2.5
    assert enhanced_trackpoints[0]["target_pace_low"] == 333.33  # 1000/3.0
    assert enhanced_trackpoints[0]["workout_intensity"] == "warmup"
    
    # Third point should have active targets
    assert enhanced_trackpoints[2]["target_speed_low"] == 3000
    assert enhanced_trackpoints[2]["target_speed_high"] == 3500
    assert enhanced_trackpoints[2]["target_pace_high"] == 333.33  # 1000/3.0
    assert enhanced_trackpoints[2]["target_pace_low"] == 285.71  # 1000/3.5
    assert enhanced_trackpoints[2]["workout_intensity"] == "active"


def test_extract_swim_targets_from_step_name():
    """
    Test that extract_swim_targets_from_step_name correctly parses swim pace targets.
    """
    # Test valid pace format
    step_name = "Pace 2:26–2:43/100 yards"
    targets = extract_swim_targets_from_step_name(step_name)
    
    assert targets["target_pace_low"] == 146  # 2:26 = 146 seconds
    assert targets["target_pace_high"] == 163  # 2:43 = 163 seconds
    assert targets["target_distance"] == 100
    assert targets["target_unit"] == "yards"
    
    # Test meters format
    step_name_meters = "Pace 1:45–2:00/50 meters"
    targets_meters = extract_swim_targets_from_step_name(step_name_meters)
    
    assert targets_meters["target_pace_low"] == 105  # 1:45 = 105 seconds
    assert targets_meters["target_pace_high"] == 120  # 2:00 = 120 seconds
    assert targets_meters["target_distance"] == 50
    assert targets_meters["target_unit"] == "meters"
    
    # Test invalid format
    invalid_step = "Just some text"
    invalid_targets = extract_swim_targets_from_step_name(invalid_step)
    assert invalid_targets == {}
    
    # Test empty string
    empty_targets = extract_swim_targets_from_step_name("")
    assert empty_targets == {}


def test_map_targets_to_timestamps_no_targets():
    """
    Test that map_targets_to_timestamps handles cases with no target information.
    """
    trackpoints = [
        {"timestamp": "2025-07-02T16:09:37.000Z", "heart_rate": 89},
        {"timestamp": "2025-07-02T16:09:38.000Z", "heart_rate": 92},
    ]
    
    # No target info
    enhanced_trackpoints = map_targets_to_timestamps(trackpoints, {}, "bike")
    assert enhanced_trackpoints == trackpoints
    
    # Empty workout steps
    target_info = {"workout_steps": []}
    enhanced_trackpoints = map_targets_to_timestamps(trackpoints, target_info, "bike")
    assert enhanced_trackpoints == trackpoints


def test_map_targets_to_timestamps_open_duration():
    """
    Test that map_targets_to_timestamps handles open duration steps correctly.
    """
    trackpoints = [
        {"timestamp": "2025-07-02T16:09:37.000Z", "heart_rate": 89},
        {"timestamp": "2025-07-02T16:09:38.000Z", "heart_rate": 92},
        {"timestamp": "2025-07-02T16:09:39.000Z", "heart_rate": 93},
    ]
    
    target_info = {
        "workout_steps": [
            {
                "message_index": 0,
                "duration_type": "time",
                "duration_value": 1000,  # 1 second
                "target_type": "power_3s",
                "custom_target_value_low": 100,
                "custom_target_value_high": 150,
                "intensity": "warmup"
            },
            {
                "message_index": 1,
                "duration_type": "open",  # Open duration
                "target_type": "power_3s",
                "custom_target_value_low": 150,
                "custom_target_value_high": 200,
                "intensity": "cooldown"
            }
        ]
    }
    
    enhanced_trackpoints = map_targets_to_timestamps(trackpoints, target_info, "bike")
    
    # First point should have warmup targets
    assert enhanced_trackpoints[0]["workout_step_index"] == 0
    assert enhanced_trackpoints[0]["workout_intensity"] == "warmup"
    
    # Last two points should have cooldown targets (open duration)
    assert enhanced_trackpoints[1]["workout_step_index"] == 1
    assert enhanced_trackpoints[1]["workout_intensity"] == "cooldown"
    assert enhanced_trackpoints[2]["workout_step_index"] == 1
    assert enhanced_trackpoints[2]["workout_intensity"] == "cooldown"