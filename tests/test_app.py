"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test"""
    # Import here to avoid circular imports
    from app import activities
    
    # Store original state
    original_activities = {
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
        },
        "Basketball Team": {
            "description": "Competitive basketball team for interscholastic games",
            "schedule": "Mondays, Wednesdays, Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn and practice tennis skills with teammates",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 10,
            "participants": []
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and develop acting skills",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Mondays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["maya@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop argumentation and public speaking skills through competitive debate",
            "schedule": "Tuesdays and Fridays, 3:30 PM - 4:45 PM",
            "max_participants": 16,
            "participants": ["ryan@mergington.edu", "sarah@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore STEM concepts",
            "schedule": "Wednesdays, 4:00 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["aiden@mergington.edu"]
        }
    }
    
    # Reset to original state
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
    
    def test_root_redirect_followed(self, client):
        """Test that root endpoint can be followed to static HTML"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test that we can retrieve all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
    
    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_activities_have_correct_initial_participants(self, client):
        """Test that activities have correct initial participant data"""
        response = client.get("/activities")
        activities = response.json()
        
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "emma@mergington.edu" in activities["Programming Class"]["participants"]
        assert len(activities["Tennis Club"]["participants"]) == 0


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Tennis%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Signed up newstudent@mergington.edu for Tennis Club"
    
    def test_signup_updates_participant_list(self, client):
        """Test that signup actually adds the student to the participant list"""
        # Sign up a new student
        response = client.post(
            "/activities/Tennis%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Tennis Club"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_duplicate_signup(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
    
    def test_signup_multiple_students(self, client):
        """Test that multiple students can sign up for the same activity"""
        # Sign up first student
        response1 = client.post(
            "/activities/Tennis%20Club/signup?email=student1@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Sign up second student
        response2 = client.post(
            "/activities/Tennis%20Club/signup?email=student2@mergington.edu"
        )
        assert response2.status_code == 200
        
        # Verify both students are in the list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "student1@mergington.edu" in activities["Tennis Club"]["participants"]
        assert "student2@mergington.edu" in activities["Tennis Club"]["participants"]
        assert len(activities["Tennis Club"]["participants"]) == 2


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_from_activity_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Unregistered michael@mergington.edu from Chess Club"
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the student from the participant list"""
        # Unregister a student
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 1
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistering from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_nonexistent_student(self, client):
        """Test unregistering a student who is not in the activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"
    
    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering from an activity"""
        email = "testuser@mergington.edu"
        activity = "Tennis%20Club"
        
        # Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Verify signup
        activities1 = client.get("/activities").json()
        assert email in activities1["Tennis Club"]["participants"]
        
        # Unregister
        response2 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        
        # Verify unregistration
        activities2 = client.get("/activities").json()
        assert email not in activities2["Tennis Club"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""
    
    def test_full_workflow(self, client):
        """Test a complete workflow: get activities, sign up, unregister"""
        # Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        initial_count = len(activities["Tennis Club"]["participants"])
        
        # Sign up for activity
        email = "integration@mergington.edu"
        response = client.post(f"/activities/Tennis%20Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signup
        activities = client.get("/activities").json()
        assert email in activities["Tennis Club"]["participants"]
        assert len(activities["Tennis Club"]["participants"]) == initial_count + 1
        
        # Unregister from activity
        response = client.delete(f"/activities/Tennis%20Club/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify unregistration
        activities = client.get("/activities").json()
        assert email not in activities["Tennis Club"]["participants"]
        assert len(activities["Tennis Club"]["participants"]) == initial_count
    
    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple students signing up and unregistering"""
        students = [f"student{i}@mergington.edu" for i in range(3)]
        
        # All students sign up
        for student in students:
            response = client.post(f"/activities/Tennis%20Club/signup?email={student}")
            assert response.status_code == 200
        
        # Verify all are signed up
        activities = client.get("/activities").json()
        for student in students:
            assert student in activities["Tennis Club"]["participants"]
        
        # Unregister first and last
        client.delete(f"/activities/Tennis%20Club/unregister?email={students[0]}")
        client.delete(f"/activities/Tennis%20Club/unregister?email={students[2]}")
        
        # Verify correct students remain
        activities = client.get("/activities").json()
        assert students[0] not in activities["Tennis Club"]["participants"]
        assert students[1] in activities["Tennis Club"]["participants"]
        assert students[2] not in activities["Tennis Club"]["participants"]
