"""
Test suite for the Mergington High School API

Tests cover all endpoints including:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/unregister
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data) == 3

    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to the list"""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_duplicate_student(self, client):
        """Test that duplicate signup is prevented"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response1.status_code == 400
        data = response1.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_url_encoding(self, client):
        """Test that activity names with spaces are properly handled"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_email_with_special_chars(self, client):
        """Test signup with email containing special characters"""
        response = client.post(
            "/activities/Chess Club/signup?email=test%2Buser@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Removed" in data["message"] or "removed" in data["message"].lower()

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from the list"""
        client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]

    def test_unregister_not_signed_up(self, client):
        """Test unregistering a student who is not signed up"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notsignedup@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_url_encoding(self, client):
        """Test that activity names with spaces are properly handled"""
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=emma@mergington.edu"
        )
        assert response.status_code == 200


class TestIntegration:
    """Integration tests covering multiple operations"""

    def test_signup_and_unregister_flow(self, client):
        """Test complete flow: signup and then unregister"""
        # Signup
        signup_response = client.post(
            "/activities/Chess Club/signup?email=testuser@mergington.edu"
        )
        assert signup_response.status_code == 200

        # Verify signup
        get_response = client.get("/activities")
        assert "testuser@mergington.edu" in get_response.json()["Chess Club"]["participants"]

        # Unregister
        unregister_response = client.delete(
            "/activities/Chess Club/unregister?email=testuser@mergington.edu"
        )
        assert unregister_response.status_code == 200

        # Verify unregister
        final_response = client.get("/activities")
        assert "testuser@mergington.edu" not in final_response.json()["Chess Club"]["participants"]

    def test_multiple_signups_different_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multitask@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200

        # Signup for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200

        # Verify both signups
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]

    def test_participant_count_consistency(self, client):
        """Test that participant counts remain consistent across operations"""
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])

        # Add a participant
        client.post("/activities/Chess Club/signup?email=newuser@mergington.edu")
        after_signup_response = client.get("/activities")
        after_signup_count = len(after_signup_response.json()["Chess Club"]["participants"])
        assert after_signup_count == initial_count + 1

        # Remove a participant
        client.delete("/activities/Chess Club/unregister?email=newuser@mergington.edu")
        after_unregister_response = client.get("/activities")
        after_unregister_count = len(after_unregister_response.json()["Chess Club"]["participants"])
        assert after_unregister_count == initial_count


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
