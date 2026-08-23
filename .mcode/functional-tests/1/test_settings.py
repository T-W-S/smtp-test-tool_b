"""Functional tests for Settings endpoints."""

import requests

BASE_URL = "http://localhost:5000"


class TestSettingsPage:
    """GET /settings -- settings page renders."""

    def test_settings_page_returns_200(self):
        resp = requests.get(f"{BASE_URL}/settings", timeout=10)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("Content-Type", "")


class TestAdvancedSettings:
    """GET /advanced_settings -- advanced settings page renders."""

    def test_advanced_settings_returns_200(self):
        resp = requests.get(f"{BASE_URL}/advanced_settings", timeout=10)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("Content-Type", "")


class TestUpdateSettings:
    """POST /update_settings -- update application settings."""

    def test_update_settings_success(self):
        data = {
            "send_hostname": "testhost.local",
            "default_sender": "test@example.com",
            "log_level": "DEBUG",
            "log_retention_days": "60",
            "log_smtp_traffic": "on",
            "max_attachment_size_mb": "25",
        }
        resp = requests.post(
            f"{BASE_URL}/update_settings",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/advanced_settings" in resp.headers.get("Location", "")

    def test_update_settings_default_hostname(self):
        """When send_hostname is empty, app should use socket.gethostname()."""
        data = {
            "send_hostname": "",
            "default_sender": "noreply@example.com",
            "log_level": "INFO",
            "log_retention_days": "30",
            "max_attachment_size_mb": "10",
        }
        resp = requests.post(
            f"{BASE_URL}/update_settings",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302

    def test_update_settings_with_log_message_content(self):
        data = {
            "send_hostname": "testhost.local",
            "default_sender": "test@example.com",
            "log_level": "WARNING",
            "log_retention_days": "7",
            "log_smtp_traffic": "on",
            "log_message_content": "on",
            "max_attachment_size_mb": "5",
        }
        resp = requests.post(
            f"{BASE_URL}/update_settings",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302
