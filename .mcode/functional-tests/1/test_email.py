"""Functional tests for Email-related endpoints."""

import uuid
import requests
import pytest

BASE_URL = "http://localhost:5000"
NS = f"ftrun_{uuid.uuid4().hex[:8]}"


class TestMainPage:
    """GET / -- main email form page."""

    def test_main_page_returns_200(self):
        resp = requests.get(f"{BASE_URL}/", timeout=10)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("Content-Type", "")


class TestGetTestData:
    """GET /get_test_data -- retrieve test email data."""

    def test_get_pdf_test_data(self):
        resp = requests.get(
            f"{BASE_URL}/get_test_data",
            params={"test_type": "pdf"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "test_data" in body
        td = body["test_data"]
        assert td["subject"] == "PDF Attachment Test"
        assert "special_attachment" in td
        assert td["special_attachment"]["type"] == "pdf"

    def test_get_eicar_test_data(self):
        resp = requests.get(
            f"{BASE_URL}/get_test_data",
            params={"test_type": "eicar"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        td = body["test_data"]
        assert td["subject"] == "EICAR Antivirus Test File"
        assert td["special_attachment"]["type"] == "eicar"

    def test_get_pdf_malformed_test_data(self):
        resp = requests.get(
            f"{BASE_URL}/get_test_data",
            params={"test_type": "pdf-malformed"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        td = body["test_data"]
        assert td["subject"] == "Malformed PDF Test"
        assert td["special_attachment"]["malformed"] is True

    def test_get_pdf_active_test_data(self):
        resp = requests.get(
            f"{BASE_URL}/get_test_data",
            params={"test_type": "pdf-active"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        td = body["test_data"]
        assert td["subject"] == "PDF with Active Content Test"
        assert td["special_attachment"]["active_content"] is True

    def test_get_spf_test_data(self):
        resp = requests.get(
            f"{BASE_URL}/get_test_data",
            params={"test_type": "spf"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "test_data" in body

    def test_get_unknown_test_type(self):
        resp = requests.get(
            f"{BASE_URL}/get_test_data",
            params={"test_type": "unknown_type_xyz"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "unknown test type" in body["message"].lower()

    def test_get_test_data_with_recipient(self):
        resp = requests.get(
            f"{BASE_URL}/get_test_data",
            params={"test_type": "pdf", "recipient": "custom@example.com"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        td = body["test_data"]
        assert "custom@example.com" in td["recipients"]


class TestSendEmail:
    """POST /send_email -- send email (requires profile to exist)."""

    @pytest.fixture(autouse=True)
    def _setup_profile(self):
        """Seed a test SMTP profile for send_email tests."""
        self.profile_name = f"{NS}_sendprofile"
        data = {
            "name": self.profile_name,
            "server": "smtp.example.com",
            "port": "587",
            "use_tls": "on",
            "username": "user",
            "password": "pass",
        }
        requests.post(
            f"{BASE_URL}/add_profile",
            data=data,
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=10,
        )
        yield
        requests.post(
            f"{BASE_URL}/delete_profile/{self.profile_name}",
            timeout=10,
            allow_redirects=False,
        )

    def test_send_email_missing_profile(self):
        """send_email with a non-existent profile returns failure."""
        data = {
            "profile": "nonexistent_profile_abc",
            "sender": "sender@example.com",
            "recipients": "recipient@example.com",
            "subject": "Test",
            "body": "Test body",
            "body_type": "plain",
        }
        resp = requests.post(
            f"{BASE_URL}/send_email",
            data=data,
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "not found" in body["message"].lower()

    def test_send_email_invalid_recipient(self):
        """send_email with an invalid email address returns failure."""
        data = {
            "profile": self.profile_name,
            "sender": "sender@example.com",
            "recipients": "not-valid-email",
            "subject": "Test",
            "body": "Body",
            "body_type": "plain",
        }
        resp = requests.post(
            f"{BASE_URL}/send_email",
            data=data,
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "invalid" in body["message"].lower()


class TestTestConnection:
    """POST /test_connection -- test SMTP connection."""

    def test_connection_missing_profile(self):
        """test_connection with a non-existent profile returns failure."""
        resp = requests.post(
            f"{BASE_URL}/test_connection",
            data={"profile": "nonexistent_profile_xyz"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "not found" in body["message"].lower()
