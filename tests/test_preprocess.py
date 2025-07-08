import pytest
from pathlib import Path
from services.preprocess import extract_workout_targets_from_fit


def test_extract_workout_targets_from_fit_bike():
    """
    Test that extract_workout_targets_from_fit correctly extracts target info from a real bike FIT file.
    """
    fit_path = Path("bike_workout.fit")
    assert fit_path.exists(), "Test FIT file does not exist!"
    target_info = extract_workout_targets_from_fit(fit_path)
    # There should be at least one workout step with target info
    steps = target_info.get("workout_steps", [])
    assert isinstance(steps, list)
    assert len(steps) > 0, "No workout steps found in FIT file."
    # At least one step should have a target_type and a target value or range
    found_target = False
    for step in steps:
        if step.get("target_type") is not None and (
            step.get("target_value") is not None or (
                step.get("custom_target_value_low") is not None and step.get("custom_target_value_high") is not None
            )
        ):
            found_target = True
            break
    assert found_target, "No workout step with target_type and target value/range found."
    # Optionally, print for debug
    print("Extracted target info:", target_info)