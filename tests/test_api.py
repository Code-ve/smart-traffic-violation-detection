"""Tests for API endpoints using FastAPI's test client."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(temp_db):
    """Create a test client with a temporary database."""
    from app.main import create_app
    app = create_app()
    return TestClient(app)


class TestPageRoutes:
    """Tests for HTML page serving."""

    def test_home_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "TrafficVision" in resp.text

    def test_upload_page(self, client):
        resp = client.get("/upload")
        assert resp.status_code == 200
        assert "Upload" in resp.text

    def test_violations_page(self, client):
        resp = client.get("/violations")
        assert resp.status_code == 200

    def test_analytics_page(self, client):
        resp = client.get("/analytics")
        assert resp.status_code == 200

    def test_evaluation_page(self, client):
        resp = client.get("/evaluation")
        assert resp.status_code == 200


class TestAPIEndpoints:
    """Tests for JSON API endpoints."""

    def test_get_sessions_empty(self, client):
        resp = client.get("/api/sessions")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_violations_empty(self, client):
        resp = client.get("/api/violations")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_config(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "confidence_threshold" in data
        assert "signal_state" in data

    def test_update_config(self, client):
        resp = client.post(
            "/api/config",
            json={"signal_state": "RED", "red_light_line_y": 500},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated"]["signal_state"] == "RED"

    def test_analytics_summary(self, client):
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sessions" in data

    def test_analytics_traffic(self, client):
        resp = client.get("/api/analytics/traffic")
        assert resp.status_code == 200

    def test_analytics_violations(self, client):
        resp = client.get("/api/analytics/violations")
        assert resp.status_code == 200

    def test_upload_no_file(self, client):
        resp = client.post("/api/upload")
        assert resp.status_code == 422  # FastAPI validation error

    def test_upload_unsupported_file(self, client):
        resp = client.post(
            "/api/upload",
            files={"file": ("test.exe", b"fake content", "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_get_nonexistent_session(self, client):
        resp = client.get("/api/sessions/nonexistent")
        assert resp.status_code == 404

    def test_violation_status_update_invalid(self, client):
        resp = client.patch(
            "/api/violations/99999/status",
            json={"status": "Reviewed"},
        )
        assert resp.status_code == 404
