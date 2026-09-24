"""Tests for profile CRUD routes."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from smtp_tool.services import config_service


class TestProfileRoutes:
    """Test POST /add_profile and POST /delete_profile/<name>."""

    def test_add_profile_ajax(self, client, app):
        response = client.post(
            "/add_profile",
            data={
                "name": "test-profile",
                "server": "smtp.example.com",
                "port": "587",
                "use_tls": "on",
                "username": "user",
                "password": "pass",
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        # Verify it was persisted
        with app.app_context():
            profile = config_service.get_profile("test-profile")
            assert profile is not None
            assert profile["server"] == "smtp.example.com"

    def test_add_profile_missing_name_ajax(self, client):
        response = client.post(
            "/add_profile",
            data={
                "server": "smtp.example.com",
                "port": "587",
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False

    def test_add_profile_form_redirect(self, client):
        response = client.post(
            "/add_profile",
            data={
                "name": "form-profile",
                "server": "smtp.example.com",
                "port": "25",
            },
        )
        # Non-AJAX should redirect
        assert response.status_code == 302

    @patch(
        "smtp_tool.blueprints.profiles.config_service.add_profile",
        return_value=False,
    )
    def test_add_profile_db_failure_ajax(self, mock_add_profile, client):
        response = client.post(
            "/add_profile",
            data={
                "name": "fail-profile",
                "server": "smtp.example.com",
                "port": "587",
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
        assert "Failed to save profile to the database" in data["message"]

    @patch(
        "smtp_tool.blueprints.profiles.config_service.add_profile",
        return_value=False,
    )
    def test_add_profile_db_failure_form(self, mock_add_profile, client):
        response = client.post(
            "/add_profile",
            data={
                "name": "fail-profile",
                "server": "smtp.example.com",
                "port": "587",
            },
        )
        assert response.status_code == 302

    def test_delete_profile(self, client, app):
        # First create a profile
        with app.app_context():
            config_service.add_profile(
                {
                    "name": "deleteme",
                    "server": "smtp.example.com",
                    "port": 25,
                    "use_tls": False,
                    "use_ssl": False,
                    "username": "",
                    "password": "",
                }
            )

        response = client.post("/delete_profile/deleteme")
        assert response.status_code == 302  # redirect

        with app.app_context():
            assert config_service.get_profile("deleteme") is None
