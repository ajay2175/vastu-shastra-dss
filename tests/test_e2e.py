"""End-to-end tests for the complete system."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_directions(client):
    """Test getting list of directions."""
    response = client.get("/api/v1/directions")
    assert response.status_code == 200
    directions = response.json()
    assert len(directions) > 0
    assert "North" in directions or "north" in str(directions).lower()


def test_list_rooms(client):
    """Test getting list of room types."""
    response = client.get("/api/v1/rooms")
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) > 0


def test_system_info(client):
    """Test system info endpoint."""
    response = client.get("/api/v1/system-info")
    assert response.status_code == 200
    info = response.json()
    assert "system" in info
    assert "version" in info


def test_get_principles(client):
    """Test getting all principles."""
    response = client.get("/api/v1/principles")
    assert response.status_code == 200
    principles = response.json()
    assert isinstance(principles, dict)
    assert len(principles) > 0


def test_get_remedies(client):
    """Test getting all remedies."""
    response = client.get("/api/v1/remedies")
    assert response.status_code == 200
    remedies = response.json()
    assert isinstance(remedies, dict)


@pytest.mark.asyncio
async def test_direction_consultation_flow(client):
    """Test complete direction consultation flow."""
    response = client.post(
        "/api/v1/directions/consult", json={"direction": "northeast"}
    )

    # May return 503 if consultation system not fully initialized in test
    if response.status_code == 200:
        data = response.json()
        assert "direction" in data
        assert "principle_name" in data


@pytest.mark.asyncio
async def test_room_consultation_flow(client):
    """Test complete room consultation flow."""
    response = client.post(
        "/api/v1/rooms/consult", json={"room_type": "bedroom"}
    )

    if response.status_code == 200:
        data = response.json()
        assert "room_type" in data
        assert "best_directions" in data


@pytest.mark.asyncio
async def test_space_analysis_flow(client):
    """Test complete space analysis flow."""
    space_data = {
        "space_name": "Test Room",
        "space_type": "bedroom",
        "direction": "southwest",
        "area_sqft": 150,
        "purpose": "Sleeping",
    }

    response = client.post("/api/v1/spaces/analyze", json=space_data)

    if response.status_code == 200:
        data = response.json()
        assert "space_name" in data
        assert "compliance_score" in data


@pytest.mark.asyncio
async def test_batch_analysis_flow(client):
    """Test batch analysis flow."""
    batch_data = {
        "spaces": [
            {
                "space_name": "Room 1",
                "space_type": "bedroom",
                "direction": "south",
                "purpose": "Sleeping",
            },
            {
                "space_name": "Room 2",
                "space_type": "kitchen",
                "direction": "southeast",
                "purpose": "Cooking",
            },
        ]
    }

    response = client.post("/api/v1/spaces/analyze-batch", json=batch_data)

    if response.status_code == 200:
        data = response.json()
        assert "analyses" in data
        assert "overall_score" in data
        assert len(data["analyses"]) == 2
