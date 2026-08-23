"""Tests for saved address routes (senders and recipients)."""

from __future__ import annotations

import json

import pytest

from smtp_tool.services import config_service


class TestSaveSenderRoute:
    """Test POST /save_sender."""

    def test_save_sender_success(self, client, app):
        response = client.post(
            "/save_sender",
            data=json.dumps({"email": "newsender@example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        with app.app_context():
            settings = config_service.get_settings()
            assert "newsender@example.com" in settings["saved_senders"]

    def test_save_sender_invalid_email(self, client):
        response = client.post(
            "/save_sender",
            data=json.dumps({"email": "not-an-email"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False


class TestSaveRecipientRoute:
    """Test POST /save_recipient."""

    def test_save_recipient_success(self, client, app):
        response = client.post(
            "/save_recipient",
            data=json.dumps({"email": "newrecip@example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        with app.app_context():
            settings = config_service.get_settings()
            assert "newrecip@example.com" in settings["saved_recipients"]

    def test_save_recipient_invalid_email(self, client):
        response = client.post(
            "/save_recipient",
            data=json.dumps({"email": "bad"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False


class TestDeleteSenderRoute:
    """Test POST /delete_sender."""

    def test_delete_sender_success(self, client, app):
        # First add a sender
        with app.app_context():
            config_service.get_settings()  # seed defaults
            config_service.add_saved_sender("removeme@example.com")

        response = client.post(
            "/delete_sender",
            data=json.dumps({"email": "removeme@example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_delete_sender_no_data(self, client):
        response = client.post(
            "/delete_sender",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False

    def test_delete_sender_nonexistent(self, client):
        response = client.post(
            "/delete_sender",
            data=json.dumps({"email": "nosuch@example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False


class TestDeleteRecipientRoute:
    """Test POST /delete_recipient."""

    def test_delete_recipient_success(self, client, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            config_service.add_saved_recipient("removeme@example.com")

        response = client.post(
            "/delete_recipient",
            data=json.dumps({"email": "removeme@example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_delete_recipient_no_email(self, client):
        response = client.post(
            "/delete_recipient",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
