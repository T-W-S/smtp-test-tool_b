"""Tests for settings and template management routes."""

from __future__ import annotations

import pytest

from smtp_tool.services import config_service


class TestSettingsRoutes:
    """Test POST /update_settings."""

    def test_update_settings_redirect(self, client):
        response = client.post(
            "/update_settings",
            data={
                "send_hostname": "myhost",
                "default_sender": "sender@example.com",
                "log_level": "DEBUG",
                "log_retention_days": "60",
                "log_smtp_traffic": "on",
                "max_attachment_size_mb": "20",
            },
        )
        # Should redirect to advanced_settings
        assert response.status_code == 302

    def test_update_settings_persists(self, client, app):
        client.post(
            "/update_settings",
            data={
                "send_hostname": "custom-host",
                "default_sender": "custom@example.com",
                "log_level": "WARNING",
                "log_retention_days": "7",
                "max_attachment_size_mb": "5",
            },
        )

        with app.app_context():
            settings = config_service.get_settings()
            assert settings["send_hostname"] == "custom-host"
            assert settings["default_sender"] == "custom@example.com"
            assert settings["log_level"] == "WARNING"


class TestTemplateRoutes:
    """Test template add/delete/get routes."""

    def test_add_template_redirect(self, client):
        response = client.post(
            "/add_template",
            data={
                "name": "My Template",
                "subject": "Test Subject",
                "body_type": "plain",
                "body": "Template body text",
            },
        )
        assert response.status_code == 302

    def test_add_template_persists(self, client, app):
        client.post(
            "/add_template",
            data={
                "name": "Persisted Template",
                "subject": "Subject",
                "body_type": "html",
                "body": "<p>Hello</p>",
            },
        )

        with app.app_context():
            tpl = config_service.get_template("Persisted Template")
            assert tpl is not None
            assert tpl["subject"] == "Subject"
            assert tpl["body_type"] == "html"

    def test_add_template_missing_required(self, client):
        response = client.post(
            "/add_template",
            data={
                "name": "",
                "body": "",
            },
        )
        # Missing name/body returns JSON error
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False

    def test_delete_template(self, client, app):
        with app.app_context():
            config_service.add_template(
                {
                    "name": "deleteme",
                    "subject": "s",
                    "body_type": "plain",
                    "body": "b",
                }
            )

        response = client.post("/delete_template/deleteme")
        assert response.status_code == 302

        with app.app_context():
            assert config_service.get_template("deleteme") is None

    def test_get_template_json(self, client, app):
        with app.app_context():
            config_service.add_template(
                {
                    "name": "fetchme",
                    "subject": "Fetch Subject",
                    "body_type": "plain",
                    "body": "Fetch Body",
                }
            )

        response = client.get("/get_template/fetchme")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["template"]["subject"] == "Fetch Subject"

    def test_get_template_not_found(self, client):
        response = client.get("/get_template/nonexistent")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False


class TestLogRoutes:
    """Test log-related routes."""

    def test_clear_logs_redirect(self, client):
        response = client.post("/clear_logs")
        assert response.status_code == 302

    def test_clear_logs_clears_data(self, client, app):
        with app.app_context():
            config_service.add_log_entry(
                {
                    "timestamp": "2024-01-01 00:00:00",
                    "profile": "p",
                    "server": "s",
                    "sender": "sender@example.com",
                    "recipients": [],
                    "subject": "Test",
                    "status": "Success",
                    "smtp_log": [],
                }
            )
            assert len(config_service.get_logs()) == 1

        client.post("/clear_logs")

        with app.app_context():
            assert len(config_service.get_logs()) == 0
