"""Functional tests for saved address management endpoints."""

import uuid
import requests
import pytest

BASE_URL = "http://localhost:5000"
NS = f"ftrun_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def seeded_sender():
    """Save a sender address; delete it in teardown."""
    email = f"{NS}_sender@example.com"
    resp = requests.post(
        f"{BASE_URL}/save_sender",
        json={"email": email},
        timeout=10,
    )
    assert resp.status_code == 200
    yield email
    requests.post(
        f"{BASE_URL}/delete_sender",
        json={"email": email},
        timeout=10,
    )


@pytest.fixture
def seeded_recipient():
    """Save a recipient address; delete it in teardown."""
    email = f"{NS}_recipient@example.com"
    resp = requests.post(
        f"{BASE_URL}/save_recipient",
        json={"email": email},
        timeout=10,
    )
    assert resp.status_code == 200
    yield email
    requests.post(
        f"{BASE_URL}/delete_recipient",
        json={"email": email},
        timeout=10,
    )


class TestSaveSender:
    """POST /save_sender -- save a sender email address."""

    def test_save_sender_success(self):
        email = f"{NS}_save_s@example.com"
        resp = requests.post(
            f"{BASE_URL}/save_sender",
            json={"email": email},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

        # Cleanup
        requests.post(
            f"{BASE_URL}/delete_sender",
            json={"email": email},
            timeout=10,
        )

    def test_save_sender_invalid_email(self):
        resp = requests.post(
            f"{BASE_URL}/save_sender",
            json={"email": "not-an-email"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False

    def test_save_sender_empty_email(self):
        resp = requests.post(
            f"{BASE_URL}/save_sender",
            json={"email": ""},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False


class TestSaveRecipient:
    """POST /save_recipient -- save a recipient email address."""

    def test_save_recipient_success(self):
        email = f"{NS}_save_r@example.com"
        resp = requests.post(
            f"{BASE_URL}/save_recipient",
            json={"email": email},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

        # Cleanup
        requests.post(
            f"{BASE_URL}/delete_recipient",
            json={"email": email},
            timeout=10,
        )

    def test_save_recipient_invalid_email(self):
        resp = requests.post(
            f"{BASE_URL}/save_recipient",
            json={"email": "invalid@@email"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False


class TestDeleteSender:
    """POST /delete_sender -- delete a saved sender address."""

    def test_delete_existing_sender(self, seeded_sender):
        resp = requests.post(
            f"{BASE_URL}/delete_sender",
            json={"email": seeded_sender},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "deleted" in body["message"].lower()

    def test_delete_sender_no_data(self):
        resp = requests.post(
            f"{BASE_URL}/delete_sender",
            json={},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False

    def test_delete_sender_no_email_field(self):
        resp = requests.post(
            f"{BASE_URL}/delete_sender",
            json={"foo": "bar"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False


class TestDeleteRecipient:
    """POST /delete_recipient -- delete a saved recipient address."""

    def test_delete_existing_recipient(self, seeded_recipient):
        resp = requests.post(
            f"{BASE_URL}/delete_recipient",
            json={"email": seeded_recipient},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "deleted" in body["message"].lower()

    def test_delete_recipient_no_data(self):
        resp = requests.post(
            f"{BASE_URL}/delete_recipient",
            json={},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False

    def test_delete_recipient_no_email_field(self):
        resp = requests.post(
            f"{BASE_URL}/delete_recipient",
            json={"foo": "bar"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False


class TestAddressesPage:
    """GET /addresses -- verify addresses page renders."""

    def test_addresses_page_renders(self):
        resp = requests.get(f"{BASE_URL}/addresses", timeout=10)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("Content-Type", "")

    def test_addresses_page_shows_saved_sender(self, seeded_sender):
        resp = requests.get(f"{BASE_URL}/addresses", timeout=10)
        assert resp.status_code == 200
        assert seeded_sender in resp.text
