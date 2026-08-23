"""Shared fixtures for SMTP Test Tool functional tests."""

import uuid
import requests
import pytest

BASE_URL = "http://localhost:5000"
NS = f"ftrun_{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def health_check():
    """Confirm the app is reachable before running tests."""
    resp = requests.get(f"{BASE_URL}/health_check", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
