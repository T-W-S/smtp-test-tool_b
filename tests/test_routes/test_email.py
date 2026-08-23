"""Tests for email sending and connection testing routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from smtp_tool.services import config_service


class TestSendEmailRoute:
    """Test POST /send_email."""

    def _setup_profile(self, app, name="test-profile"):
        """Helper to create a profile in the DB."""
        with app.app_context():
            config_service.add_profile(
                {
                    "name": name,
                    "server": "smtp.example.com",
                    "port": 587,
                    "use_tls": True,
                    "use_ssl": False,
                    "no_tls_verify": False,
                    "username": "user",
                    "password": "pass",
                }
            )

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_cls, client, app):
        self._setup_profile(app)

        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.esmtp_features = {"auth": "PLAIN"}
        mock_smtp.sock = MagicMock()
        mock_smtp.sock.cipher.return_value = ("TLS_AES_256", "TLSv1.3", 256)
        mock_smtp.sock.version.return_value = "TLSv1.3"
        mock_smtp.sock.getpeercert.return_value = None

        response = client.post(
            "/send_email",
            data={
                "profile": "test-profile",
                "sender": "sender@example.com",
                "recipients": "recipient@example.com",
                "subject": "Test",
                "body": "Hello",
                "body_type": "plain",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_send_email_invalid_profile(self, client):
        response = client.post(
            "/send_email",
            data={
                "profile": "nonexistent",
                "sender": "sender@example.com",
                "recipients": "recipient@example.com",
                "subject": "Test",
                "body": "Hello",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
        assert "not found" in data["message"]

    def test_send_email_invalid_address(self, client, app):
        self._setup_profile(app)

        response = client.post(
            "/send_email",
            data={
                "profile": "test-profile",
                "sender": "not-an-email",
                "recipients": "recipient@example.com",
                "subject": "Test",
                "body": "Hello",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
        assert "Invalid email" in data["message"]

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_smtp_failure(self, mock_smtp_cls, client, app):
        self._setup_profile(app)

        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.esmtp_features = {"auth": "PLAIN"}
        mock_smtp.sock = MagicMock()
        mock_smtp.sock.cipher.return_value = ("TLS_AES_256", "TLSv1.3", 256)
        mock_smtp.sock.version.return_value = "TLSv1.3"
        mock_smtp.sock.getpeercert.return_value = None
        mock_smtp.sendmail.side_effect = Exception("SMTP error")

        response = client.post(
            "/send_email",
            data={
                "profile": "test-profile",
                "sender": "sender@example.com",
                "recipients": "recipient@example.com",
                "subject": "Fail Test",
                "body": "Hello",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False


class TestTestConnectionRoute:
    """Test POST /test_connection."""

    def _setup_profile(self, app, name="test-profile"):
        with app.app_context():
            config_service.add_profile(
                {
                    "name": name,
                    "server": "smtp.example.com",
                    "port": 587,
                    "use_tls": False,
                    "use_ssl": False,
                    "no_tls_verify": False,
                    "username": "",
                    "password": "",
                }
            )

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_connection_success(self, mock_smtp_cls, client, app):
        self._setup_profile(app)

        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.ehlo.return_value = (250, [b"OK"])

        response = client.post(
            "/test_connection",
            data={"profile": "test-profile"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_connection_missing_profile(self, client):
        response = client.post(
            "/test_connection",
            data={"profile": "nonexistent"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False


class TestGetTestData:
    """Test GET /get_test_data."""

    def test_get_test_data_spf(self, client):
        response = client.get("/get_test_data?test_type=spf&recipient=test@example.com")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["test_data"]["sender"] == "spf-test@gmail.com"

    def test_get_test_data_eicar(self, client):
        response = client.get("/get_test_data?test_type=eicar")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "EICAR" in data["test_data"]["subject"]

    def test_get_test_data_pdf(self, client):
        response = client.get("/get_test_data?test_type=pdf")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["test_data"]["special_attachment"]["type"] == "pdf"

    def test_get_test_data_unknown_type(self, client):
        response = client.get("/get_test_data?test_type=unknown")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
