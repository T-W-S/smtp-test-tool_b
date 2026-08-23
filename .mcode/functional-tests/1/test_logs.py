"""Functional tests for Logs endpoints."""

import requests

BASE_URL = "http://localhost:5000"


class TestLogsPage:
    """GET /logs -- logs page renders."""

    def test_logs_page_returns_200(self):
        resp = requests.get(f"{BASE_URL}/logs", timeout=10)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("Content-Type", "")


class TestClearLogs:
    """POST /clear_logs -- clear all log entries."""

    def test_clear_logs_redirects(self):
        resp = requests.post(
            f"{BASE_URL}/clear_logs",
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/logs" in resp.headers.get("Location", "")
