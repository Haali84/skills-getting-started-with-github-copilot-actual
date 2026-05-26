"""
Tests for the Mergington High School Activities API
"""

import copy
import pytest
from starlette.testclient import TestClient

from src.app import app, activities as original_activities


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient with a fresh copy of the activities database.
    This ensures each test starts with clean state and doesn't affect other tests.
    """
    # Deep copy the original activities to avoid test pollution
    app.state.activities = copy.deepcopy(original_activities)
    
    # Monkey patch the app's activities to use the test copy
    import src.app
    src.app.activities = app.state.activities
    
    yield TestClient(app)
    
    # Restore original activities after test
    src.app.activities = original_activities


def test_root_redirect(client):
    """Test that GET / redirects to /static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test that GET /activities returns all activities with correct structure"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) == 9
    
    # Verify at least one activity has the expected structure
    assert "Chess Club" in activities
    chess_club = activities["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity(client):
    """Test that POST /activities/{activity_name}/signup successfully adds a participant"""
    activity_name = "Programming Class"
    email = "newstudent@mergington.edu"
    
    # Get initial participants count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Sign up for the activity
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    new_count = len(activities_response.json()[activity_name]["participants"])
    assert new_count == initial_count + 1
    assert email in activities_response.json()[activity_name]["participants"]


def test_unregister_from_activity(client):
    """Test that DELETE /activities/{activity_name}/unregister successfully removes a participant"""
    activity_name = "Chess Club"
    # Use an existing participant from the initial data
    email = "michael@mergington.edu"
    
    # Verify the participant is initially registered
    initial_response = client.get("/activities")
    assert email in initial_response.json()[activity_name]["participants"]
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Unregister from the activity
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    new_count = len(activities_response.json()[activity_name]["participants"])
    assert new_count == initial_count - 1
    assert email not in activities_response.json()[activity_name]["participants"]
