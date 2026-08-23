"""Integration test: end-to-end email sending flow.

Verifies that submitting the send_email form with a mocked SMTP backend
results in a log entry being persisted in the database.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from smtp_tool.services import config_service


class TestEmailFlow:
    """End-to-end flow: create profile -> send email -> verify log entry."""

    def _setup_profile(self, app):
        with app.app_context():
            config_service.add_profile(
                {
                    "name": "integration-profile",
                    "server": "smtp.test.local",
                    "port": 587,
                    "use_tls": True,
                    "use_ssl": False,
                    "no_tls_verify": False,
                    "username": "testuser",
                    "password": "testpass",
                }
            )

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_creates_log_entry(self, mock_smtp_cls, client, app):
        """Full flow: POST /send_email -> SMTP mock sends -> log entry created."""
        self._setup_profile(app)

        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.esmtp_features = {"auth": "PLAIN LOGIN"}
        mock_smtp.sock = MagicMock()
        mock_smtp.sock.cipher.return_value = ("TLS_AES_256", "TLSv1.3", 256)
        mock_smtp.sock.version.return_value = "TLSv1.3"
        mock_smtp.sock.getpeercert.return_value = None

        # Send the email
        response = client.post(
            "/send_email",
            data={
                "profile": "integration-profile",
                "sender": "integration@example.com",
                "recipients": "dest@example.com",
                "cc": "cc@example.com",
                "subject": "Integration Test Email",
                "body": "This is an integration test.",
                "body_type": "plain",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "Email sent"

        # Verify SMTP interactions
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("testuser", "testpass")
        mock_smtp.sendmail.assert_called_once()

        # Verify the sendmail call included all recipients (to + cc)
        sendmail_args = mock_smtp.sendmail.call_args[0]
        assert sendmail_args[0] == "integration@example.com"  # sender
        assert "dest@example.com" in sendmail_args[1]
        assert "cc@example.com" in sendmail_args[1]

        # Verify log entry was created
        with app.app_context():
            logs = config_service.get_logs()
            assert len(logs) == 1
            log = logs[0]
            assert log["profile"] == "integration-profile"
            assert log["sender"] == "integration@example.com"
            assert "dest@example.com" in log["recipients"]
            assert log["subject"] == "Integration Test Email"
            assert log["status"] == "Success"
            assert log["server"] == "smtp.test.local:587"

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_failed_send_creates_log_entry_with_error(
        self, mock_smtp_cls, client, app
    ):
        """Failed SMTP send still creates a log entry with error details."""
        self._setup_profile(app)

        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.esmtp_features = {"auth": "PLAIN"}
        mock_smtp.sock = MagicMock()
        mock_smtp.sock.cipher.return_value = ("TLS_AES_256", "TLSv1.3", 256)
        mock_smtp.sock.version.return_value = "TLSv1.3"
        mock_smtp.sock.getpeercert.return_value = None
        mock_smtp.login.side_effect = Exception("Authentication failed")

        response = client.post(
            "/send_email",
            data={
                "profile": "integration-profile",
                "sender": "integration@example.com",
                "recipients": "dest@example.com",
                "subject": "Should Fail",
                "body": "This should fail.",
                "body_type": "plain",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False

        with app.app_context():
            logs = config_service.get_logs()
            assert len(logs) == 1
            log = logs[0]
            assert log["status"] == "Failed"
            assert "Authentication failed" in log["error"]

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_then_clear_logs(self, mock_smtp_cls, client, app):
        """Send an email, verify log exists, then clear logs."""
        self._setup_profile(app)

        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.esmtp_features = {"auth": "PLAIN"}
        mock_smtp.sock = MagicMock()
        mock_smtp.sock.cipher.return_value = ("TLS_AES_256", "TLSv1.3", 256)
        mock_smtp.sock.version.return_value = "TLSv1.3"
        mock_smtp.sock.getpeercert.return_value = None

        client.post(
            "/send_email",
            data={
                "profile": "integration-profile",
                "sender": "test@example.com",
                "recipients": "dest@example.com",
                "subject": "Log Then Clear",
                "body": "body",
                "body_type": "plain",
            },
        )

        with app.app_context():
            assert len(config_service.get_logs()) == 1

        client.post("/clear_logs")

        with app.app_context():
            assert len(config_service.get_logs()) == 0
