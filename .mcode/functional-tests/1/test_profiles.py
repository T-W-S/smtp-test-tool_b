"""Functional tests for SMTP Profile CRUD endpoints."""

import uuid
import requests
import pytest

BASE_URL = "http://localhost:5000"
NS = f"ftrun_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def seeded_profile():
    """Create a test profile via the app's own API; delete it in teardown."""
    profile_name = f"{NS}_testprofile"
    data = {
        "name": profile_name,
        "server": "smtp.example.com",
        "port": "587",
        "use_tls": "on",
        "username": "testuser",
        "password": "testpass",
    }
    resp = requests.post(
        f"{BASE_URL}/add_profile",
        data=data,
        headers={"X-Requested-With": "XMLHttpRequest"},
        timeout=10,
        allow_redirects=False,
    )
    assert resp.status_code == 200
    yield profile_name
    # Teardown: delete the profile
    requests.post(
        f"{BASE_URL}/delete_profile/{profile_name}",
        timeout=10,
        allow_redirects=False,
    )


class TestAddProfile:
    """POST /add_profile -- create SMTP profile."""

    def test_add_profile_ajax_success(self):
        profile_name = f"{NS}_addprofile"
        data = {
            "name": profile_name,
            "server": "smtp.test.com",
            "port": "25",
        }
        resp = requests.post(
            f"{BASE_URL}/add_profile",
            data=data,
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "saved successfully" in body["message"]

        # Cleanup
        requests.post(
            f"{BASE_URL}/delete_profile/{profile_name}",
            timeout=10,
            allow_redirects=False,
        )

    def test_add_profile_missing_name(self):
        data = {
            "server": "smtp.test.com",
            "port": "25",
        }
        resp = requests.post(
            f"{BASE_URL}/add_profile",
            data=data,
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "required" in body["message"].lower()

    def test_add_profile_missing_server(self):
        data = {
            "name": f"{NS}_noserver",
            "port": "25",
        }
        resp = requests.post(
            f"{BASE_URL}/add_profile",
            data=data,
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "required" in body["message"].lower()

    def test_add_profile_form_redirect(self):
        profile_name = f"{NS}_formprofile"
        data = {
            "name": profile_name,
            "server": "smtp.redirect.com",
            "port": "587",
        }
        resp = requests.post(
            f"{BASE_URL}/add_profile",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/settings" in resp.headers.get("Location", "")

        # Cleanup
        requests.post(
            f"{BASE_URL}/delete_profile/{profile_name}",
            timeout=10,
            allow_redirects=False,
        )

    def test_add_profile_with_tls_ssl_options(self):
        profile_name = f"{NS}_tlsprofile"
        data = {
            "name": profile_name,
            "server": "smtp.secure.com",
            "port": "465",
            "use_ssl": "on",
            "no_tls_verify": "on",
            "username": "secureuser",
            "password": "securepass",
        }
        resp = requests.post(
            f"{BASE_URL}/add_profile",
            data=data,
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

        # Cleanup
        requests.post(
            f"{BASE_URL}/delete_profile/{profile_name}",
            timeout=10,
            allow_redirects=False,
        )


class TestDeleteProfile:
    """POST /delete_profile/<name> -- delete SMTP profile."""

    def test_delete_existing_profile(self, seeded_profile):
        resp = requests.post(
            f"{BASE_URL}/delete_profile/{seeded_profile}",
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/settings" in resp.headers.get("Location", "")

    def test_delete_nonexistent_profile(self):
        resp = requests.post(
            f"{BASE_URL}/delete_profile/nonexistent_profile_xyz123",
            timeout=10,
            allow_redirects=False,
        )
        # Should redirect even for non-existent (app doesn't 404 on this)
        assert resp.status_code == 302


class TestSettingsPage:
    """GET /settings -- verify settings page renders with profiles."""

    def test_settings_page_renders(self):
        resp = requests.get(f"{BASE_URL}/settings", timeout=10)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("Content-Type", "")

    def test_settings_page_shows_profile(self, seeded_profile):
        resp = requests.get(f"{BASE_URL}/settings", timeout=10)
        assert resp.status_code == 200
        assert seeded_profile in resp.text
