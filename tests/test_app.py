"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from src.app import activities
    initial_activities = {
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
        "Tennis Team": {
            "description": "Competitive tennis training and tournaments",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 16,
            "participants": []
        },
    }
    
    activities.clear()
    activities.update(initial_activities)
    yield
    activities.clear()
    activities.update(initial_activities)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that the endpoint returns all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Tennis Team" in data

    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """Test that each activity contains all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club

    def test_get_activities_participants_are_lists(self, client, reset_activities):
        """Test that participants are lists"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Tennis%20Team/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "student@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Tennis%20Team/signup?email={email}")
        
        response = client.get("/activities")
        activities_data = response.json()
        assert email in activities_data["Tennis Team"]["participants"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_registration_fails(self, client, reset_activities):
        """Test that signing up twice returns error"""
        email = "michael@mergington.edu"
        
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_different_activities_allowed(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities"""
        email = "student@mergington.edu"
        
        # Sign up for Tennis Team
        response1 = client.post(
            f"/activities/Tennis%20Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        activities_data = response.json()
        assert email in activities_data["Tennis Team"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint"""

    def test_successful_unregister(self, client, reset_activities):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"
        
        response = client.delete(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        
        # Verify participant exists
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Chess%20Club/signup?email={email}")
        
        # Verify participant removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregister for student not signed up returns 404"""
        response = client.delete(
            "/activities/Tennis%20Team/signup?email=notstudent@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]

    def test_signup_after_unregister(self, client, reset_activities):
        """Test that student can re-signup after unregistering"""
        email = "michael@mergington.edu"
        
        # Unregister
        client.delete(f"/activities/Chess%20Club/signup?email={email}")
        
        # Re-signup should succeed
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant is back
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests for signup and unregister workflows"""

    def test_complete_workflow(self, client, reset_activities):
        """Test complete workflow: signup, check list, unregister"""
        email = "workflow@mergington.edu"
        activity = "Tennis%20Team"
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Check activities list
        response = client.get("/activities")
        assert email in response.json()["Tennis Team"]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Tennis Team"]["participants"]

    def test_multiple_students_same_activity(self, client, reset_activities):
        """Test multiple students can sign up for the same activity"""
        students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for student in students:
            response = client.post(
                f"/activities/Tennis%20Team/signup?email={student}"
            )
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        for student in students:
            assert student in response.json()["Tennis Team"]["participants"]
