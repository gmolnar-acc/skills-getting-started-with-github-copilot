import pytest
from fastapi.testclient import TestClient
from urllib.parse import quote

from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestActivitiesRetrieval:
    """Test cases for retrieving activities."""

    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        expected_activity_count = 9

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_activity_count
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_includes_activity_details(self, client):
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        activity = data[activity_name]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    """Test cases for student signup functionality."""

    def test_signup_successful_adds_participant(self, client):
        # Arrange
        email = "test_signup@example.com"
        activity = "Chess Club"
        encoded_activity = quote(activity)

        # Act
        response = client.post(f"/activities/{encoded_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "Signed up" in result["message"]
        assert email in result["message"]

        # Verify participant was added
        response2 = client.get("/activities")
        data = response2.json()
        assert email in data[activity]["participants"]

    def test_signup_duplicate_email_returns_error(self, client):
        # Arrange
        email = "duplicate@example.com"
        activity = "Programming Class"
        encoded_activity = quote(activity)

        # First signup
        client.post(f"/activities/{encoded_activity}/signup?email={email}")

        # Act - Second signup with same email
        response = client.post(f"/activities/{encoded_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_nonexistent_activity_returns_error(self, client):
        # Arrange
        email = "test@example.com"
        nonexistent_activity = "NonExistent Activity"
        encoded_activity = quote(nonexistent_activity)

        # Act
        response = client.post(f"/activities/{encoded_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]


class TestParticipantRemoval:
    """Test cases for removing participants from activities."""

    def test_delete_participant_successful_removes_participant(self, client):
        # Arrange
        email = "test_delete@example.com"
        activity = "Gym Class"
        encoded_activity = quote(activity)

        # Add participant first
        client.post(f"/activities/{encoded_activity}/signup?email={email}")

        # Act
        response = client.delete(f"/activities/{encoded_activity}/participants/{email}")

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "Removed" in result["message"]
        assert email in result["message"]

        # Verify participant was removed
        response2 = client.get("/activities")
        data = response2.json()
        assert email not in data[activity]["participants"]

    def test_delete_participant_nonexistent_activity_returns_error(self, client):
        # Arrange
        email = "test@example.com"
        nonexistent_activity = "NonExistent Activity"
        encoded_activity = quote(nonexistent_activity)

        # Act
        response = client.delete(f"/activities/{encoded_activity}/participants/{email}")

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_delete_participant_not_in_activity_returns_error(self, client):
        # Arrange
        email = "not_participant@example.com"
        activity = "Art Studio"
        encoded_activity = quote(activity)

        # Act
        response = client.delete(f"/activities/{encoded_activity}/participants/{email}")

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Participant not found" in result["detail"]


class TestRootRedirect:
    """Test cases for root endpoint redirect."""

    def test_root_redirects_to_static_index(self, client):
        # Arrange

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"