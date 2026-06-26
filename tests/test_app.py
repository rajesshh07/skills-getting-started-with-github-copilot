import copy
import os
import sys
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_available_activities():
    response = client.get("/activities")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "description" in data["Chess Club"]


def test_signup_for_activity_adds_participant():
    activity_name = "Chess Club"
    email = "teststudent@mergington.edu"
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_existing_student_returns_400():
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_unregister_participant_removes_student():
    activity_name = "Chess Club"
    email = "removed@mergington.edu"
    activities[activity_name]["participants"].append(email)

    response = client.delete(
        f"/activities/{quote(activity_name)}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_nonexistent_participant_returns_404():
    activity_name = "Chess Club"
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants",
        params={"email": "doesnotexist@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found for this activity"
