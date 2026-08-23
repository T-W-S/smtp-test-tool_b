"""Functional tests for GET /health_check endpoint."""

import requests

BASE_URL = "http://localhost:5000"


class TestHealthCheck:
    """GET /health_check -- verify app health and DB connectivity."""

    def test_health_check_returns_200(self):
        resp = requests.get(f"{BASE_URL}/health_check", timeout=10)
        assert resp.status_code == 200

    def test_health_check_json_structure(self):
        resp = requests.get(f"{BASE_URL}/health_check", timeout=10)
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data

    def test_health_check_content_type(self):
        resp = requests.get(f"{BASE_URL}/health_check", timeout=10)
        assert "application/json" in resp.headers.get("Content-Type", "")
