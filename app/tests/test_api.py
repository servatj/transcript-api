import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"


def test_health_endpoint():
    """Test the health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ping_endpoint():
    """Test the ping endpoint."""
    response = client.get("/api/v1/health/ping")
    assert response.status_code == 200
    assert response.json()["ping"] == "pong"


def test_transcript_endpoint_unauthorized():
    """Test the transcript endpoint without API key."""
    response = client.post(
        "/api/v1/transcript",
        json={
            "provider": "youtube",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
    )
    assert response.status_code == 401
    assert "detail" in response.json() 