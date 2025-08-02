import pytest
from utils.database import execute_query, get_active_profile
from api.main import app
from fastapi.testclient import TestClient
from datetime import datetime

client = TestClient(app)

@pytest.fixture(scope="module")
def athlete_id():
    """Return a dummy athlete id (string) existing in seed DB or create one."""
    # Try to reuse name 'demo_athlete'
    name = "demo_athlete"
    # Ensure athlete row exists (will be created by update_profile if missing)
    return name


def test_profile_uniqueness(athlete_id):
    """PUT /api/profile twice and ensure only one row has valid_to IS NULL."""
    profile_payload = {
        "athlete_id": athlete_id,
        "last_updated": datetime.utcnow().isoformat(),
        "zones": {
            "heart_rate": {"lt_hr": 160, "zones": {"z1": [100,110], "z2": [110,120], "zx": [120,130], "z3": [130,140], "zy": [140,150], "z4": [150,160], "z5": [160,170]}},
            "bike_power": {"ftp": 250, "zones": {"z1": [0,100], "z2": [100,150], "zx": [150,200], "z3": [200,225], "zy": [225,250], "z4": [250,275], "z5": [275,350]}},
            "run_power": {"ltp": 200, "critical_power": 225, "zones": {"z1": [0,80], "z2": [80,120], "zx": [120,160], "z3": [160,180], "zy": [180,200], "z4": [200,230], "z5": [230,270]}},
            "run_pace": {"threshold_pace_per_km": "4:00", "zones": {"z1": ["6:00","5:30"], "z2": ["5:30","5:00"], "zx": ["5:00","4:40"], "z3": ["4:40","4:20"], "zy": ["4:20","4:05"], "z4": ["4:05","3:50"], "z5": ["3:50","3:30"]}},
            "swim": {"css_pace_per_100m": "1:40", "zones": {"z1": ["2:15","2:00"], "z2": ["2:00","1:55"], "zx": ["1:55","1:50"], "z3": ["1:50","1:45"], "zy": ["1:45","1:40"], "z4": ["1:40","1:35"], "z5": ["1:35","1:25"]}}
        },
        "test_dates": {"bike_ftp_test": None, "run_ltp_test": None, "swim_css_test": None}
    }

    # First insert
    res1 = client.put("/api/profile", json=profile_payload)
    assert res1.status_code == 200

    # Wait a second then insert updated ftp value
    profile_payload["zones"]["bike_power"]["ftp"] = 260
    res2 = client.put("/api/profile", json=profile_payload)
    assert res2.status_code == 200

    # Query DB: count active rows
    cnt = execute_query("SELECT COUNT(*) FROM athlete_profile WHERE json_athlete_id = %s AND valid_to IS NULL", (athlete_id,), fetch_one=True)[0]
    assert cnt == 1, "More than one active profile found"

    # Helper returns latest profile (ftp 260)
    active_profile = get_active_profile(athlete_id)
    assert active_profile["zones"]["bike_power"]["ftp"] == 260 