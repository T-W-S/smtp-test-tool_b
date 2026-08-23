"""Tests for the SMTPService class with mocked smtplib."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from smtp_tool.services.smtp_service import EICAR_STRING, SMTPService


@pytest.fixture()
def smtp_service():
    return SMTPService()


# ========================================================================
# send_email
# ========================================================================


class TestSendEmail:
    """Test the send_email method with various configurations."""

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=587,
            use_tls=False,
            use_ssl=False,
            username="",
            password="",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            subject="Test Subject",
            body="Test Body",
        )

        assert result["success"] is True
        assert "message_id" in result
        assert isinstance(result["smtp_log"], list)
        mock_smtp.sendmail.assert_called_once()

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_with_authentication(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.esmtp_features = {"auth": "PLAIN LOGIN"}

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=587,
            use_tls=False,
            use_ssl=False,
            username="user",
            password="pass",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            subject="Auth Test",
            body="Body",
        )

        assert result["success"] is True
        mock_smtp.login.assert_called_once_with("user", "pass")

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_with_starttls(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.sock = MagicMock()
        mock_smtp.sock.cipher.return_value = ("TLS_AES_256", "TLSv1.3", 256)
        mock_smtp.sock.version.return_value = "TLSv1.3"
        mock_smtp.sock.getpeercert.return_value = None

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=587,
            use_tls=True,
            use_ssl=False,
            username="",
            password="",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            subject="TLS Test",
            body="Body",
        )

        assert result["success"] is True
        mock_smtp.starttls.assert_called_once()

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP_SSL")
    def test_send_email_with_ssl(self, mock_smtp_ssl_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_ssl_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.sock = MagicMock()
        mock_smtp.sock.cipher.return_value = ("TLS_AES_256", "TLSv1.3", 256)
        mock_smtp.sock.version.return_value = "TLSv1.3"
        mock_smtp.sock.getpeercert.return_value = None

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=465,
            use_tls=False,
            use_ssl=True,
            username="",
            password="",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            subject="SSL Test",
            body="Body",
        )

        assert result["success"] is True
        mock_smtp_ssl_cls.assert_called_once()
        mock_smtp.sendmail.assert_called_once()

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_with_cc_bcc(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=25,
            use_tls=False,
            use_ssl=False,
            username="",
            password="",
            sender="sender@example.com",
            recipients=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            subject="CC/BCC Test",
            body="Body",
        )

        assert result["success"] is True
        # All recipients (to + cc + bcc) should be passed to sendmail
        call_args = mock_smtp.sendmail.call_args
        all_recipients = call_args[0][1]
        assert "to@example.com" in all_recipients
        assert "cc@example.com" in all_recipients
        assert "bcc@example.com" in all_recipients

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_html_body(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=25,
            use_tls=False,
            use_ssl=False,
            username="",
            password="",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            subject="HTML Test",
            body="<p>Hello</p>",
            body_type="html",
        )

        assert result["success"] is True

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_custom_headers(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=25,
            use_tls=False,
            use_ssl=False,
            username="",
            password="",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            subject="Header Test",
            body="Body",
            custom_headers={"X-Custom": "value"},
        )

        assert result["success"] is True

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_failure(self, mock_smtp_cls, smtp_service):
        mock_smtp_cls.side_effect = ConnectionRefusedError("Connection refused")

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=25,
            use_tls=False,
            use_ssl=False,
            username="",
            password="",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            subject="Fail Test",
            body="Body",
        )

        assert result["success"] is False
        assert "error" in result
        assert "Connection refused" in result["error"]

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_send_email_with_ehlo(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.esmtp_features = {"size": "10485760", "auth": "PLAIN"}

        result = smtp_service.send_email(
            server="smtp.example.com",
            port=25,
            use_tls=False,
            use_ssl=False,
            username="",
            password="",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            subject="EHLO Test",
            body="Body",
            ehlo_as="myhost.local",
        )

        assert result["success"] is True
        mock_smtp.ehlo.assert_called_with("myhost.local")


# ========================================================================
# test_connection
# ========================================================================


class TestTestConnection:
    """Test the test_connection method."""

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_connection_success(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.ehlo.return_value = (
            250,
            [b"smtp.example.com", b"SIZE 10485760", b"AUTH PLAIN LOGIN"],
        )

        result = smtp_service.test_connection(
            server="smtp.example.com",
            port=587,
            use_tls=False,
            use_ssl=False,
            username="",
            password="",
        )

        assert result["success"] is True
        assert result["message"] == "Connection successful"
        assert isinstance(result["capabilities"], list)

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_connection_failure(self, mock_smtp_cls, smtp_service):
        mock_smtp_cls.side_effect = ConnectionRefusedError("Connection refused")

        result = smtp_service.test_connection(
            server="smtp.example.com",
            port=587,
            use_tls=False,
            use_ssl=False,
            username="",
            password="",
        )

        assert result["success"] is False
        assert "error" in result
        assert "Connection refused" in result["error"]

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP_SSL")
    def test_connection_ssl(self, mock_smtp_ssl_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_ssl_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.ehlo.return_value = (250, [b"OK"])

        result = smtp_service.test_connection(
            server="smtp.example.com",
            port=465,
            use_tls=False,
            use_ssl=True,
            username="",
            password="",
        )

        assert result["success"] is True
        mock_smtp_ssl_cls.assert_called_once()

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_connection_with_auth(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.ehlo.return_value = (250, [b"OK"])

        result = smtp_service.test_connection(
            server="smtp.example.com",
            port=587,
            use_tls=False,
            use_ssl=False,
            username="user",
            password="pass",
        )

        assert result["success"] is True
        mock_smtp.login.assert_called_once_with("user", "pass")

    @patch("smtp_tool.services.smtp_service.smtplib.SMTP")
    def test_connection_with_starttls(self, mock_smtp_cls, smtp_service):
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value = mock_smtp
        mock_smtp._print_debug = MagicMock()
        mock_smtp.ehlo.return_value = (250, [b"OK"])

        result = smtp_service.test_connection(
            server="smtp.example.com",
            port=587,
            use_tls=True,
            use_ssl=False,
            username="",
            password="",
        )

        assert result["success"] is True
        mock_smtp.starttls.assert_called_once()


# ========================================================================
# Attachment helpers
# ========================================================================


class TestAttachmentHelpers:
    """Test EICAR, PDF, and SPF test email generation."""

    def test_create_eicar_attachment(self, smtp_service):
        filename, data = smtp_service.create_eicar_attachment()
        assert filename == "eicar.com"
        assert isinstance(data, bytes)
        assert data.decode("utf-8") == EICAR_STRING

    def test_create_pdf_attachment(self, smtp_service):
        filename, data = smtp_service.create_pdf_attachment()
        assert filename == "test.pdf"
        assert isinstance(data, bytes)
        assert data[:5] == b"%PDF-"

    def test_create_pdf_attachment_custom_filename(self, smtp_service):
        filename, data = smtp_service.create_pdf_attachment(filename="report.pdf")
        assert filename == "report.pdf"
        assert data[:5] == b"%PDF-"

    def test_create_pdf_attachment_malformed(self, smtp_service):
        filename, data = smtp_service.create_pdf_attachment(malformed=True)
        assert filename == "test.pdf"
        assert isinstance(data, bytes)
        assert b"intentionally malformed" in data

    def test_create_pdf_attachment_active_content(self, smtp_service):
        filename, data = smtp_service.create_pdf_attachment(active_content=True)
        assert filename == "test.pdf"
        assert isinstance(data, bytes)
        # Active content PDFs should still be valid PDF data
        assert len(data) > 0

    def test_create_spf_test_email(self, smtp_service):
        result = smtp_service.create_spf_test_email("target@example.com")
        assert result["sender"] == "spf-test@gmail.com"
        assert result["recipients"] == ["target@example.com"]
        assert result["subject"] == "SPF Test Email"
        assert result["body_type"] == "plain"
        assert "SPF" in result["body"]
        assert "custom_headers" in result
        assert result["custom_headers"]["X-SMTP-Test"] == "SPF-Test"
