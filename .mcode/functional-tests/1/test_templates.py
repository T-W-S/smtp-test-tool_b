"""Functional tests for Template CRUD endpoints."""

import uuid
import requests
import pytest

BASE_URL = "http://localhost:5000"
NS = f"ftrun_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def seeded_template():
    """Create a test template via the app's own API; delete it in teardown."""
    template_name = f"{NS}_testtemplate"
    data = {
        "name": template_name,
        "subject": "Test Subject",
        "body_type": "plain",
        "body": "This is a test template body.",
    }
    resp = requests.post(
        f"{BASE_URL}/add_template",
        data=data,
        timeout=10,
        allow_redirects=False,
    )
    assert resp.status_code == 302
    yield template_name
    # Teardown
    requests.post(
        f"{BASE_URL}/delete_template/{template_name}",
        timeout=10,
        allow_redirects=False,
    )


class TestAddTemplate:
    """POST /add_template -- create email template."""

    def test_add_template_success(self):
        template_name = f"{NS}_addtpl"
        data = {
            "name": template_name,
            "subject": "Hello World",
            "body_type": "plain",
            "body": "Test body content.",
        }
        resp = requests.post(
            f"{BASE_URL}/add_template",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/templates" in resp.headers.get("Location", "")

        # Cleanup
        requests.post(
            f"{BASE_URL}/delete_template/{template_name}",
            timeout=10,
            allow_redirects=False,
        )

    def test_add_template_html_body_type(self):
        template_name = f"{NS}_htmltpl"
        data = {
            "name": template_name,
            "subject": "HTML Template",
            "body_type": "html",
            "body": "<h1>Hello</h1><p>Test HTML body.</p>",
        }
        resp = requests.post(
            f"{BASE_URL}/add_template",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302

        # Verify template was created
        get_resp = requests.get(
            f"{BASE_URL}/get_template/{template_name}",
            timeout=10,
        )
        body = get_resp.json()
        assert body["success"] is True
        assert body["template"]["body_type"] == "html"

        # Cleanup
        requests.post(
            f"{BASE_URL}/delete_template/{template_name}",
            timeout=10,
            allow_redirects=False,
        )

    def test_add_template_missing_name(self):
        data = {
            "subject": "No Name",
            "body": "Body without name.",
        }
        resp = requests.post(
            f"{BASE_URL}/add_template",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        # Returns JSON error (not a redirect) when validation fails
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "required" in body["message"].lower()

    def test_add_template_missing_body(self):
        data = {
            "name": f"{NS}_nobody",
            "subject": "No Body Template",
        }
        resp = requests.post(
            f"{BASE_URL}/add_template",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "required" in body["message"].lower()


class TestGetTemplate:
    """GET /get_template/<name> -- retrieve template JSON."""

    def test_get_existing_template(self, seeded_template):
        resp = requests.get(
            f"{BASE_URL}/get_template/{seeded_template}",
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "template" in body
        tpl = body["template"]
        assert "subject" in tpl
        assert "body" in tpl
        assert "body_type" in tpl

    def test_get_nonexistent_template(self):
        resp = requests.get(
            f"{BASE_URL}/get_template/nonexistent_template_xyz999",
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "not found" in body["message"].lower()


class TestDeleteTemplate:
    """POST /delete_template/<name> -- delete template."""

    def test_delete_existing_template(self, seeded_template):
        resp = requests.post(
            f"{BASE_URL}/delete_template/{seeded_template}",
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/templates" in resp.headers.get("Location", "")

        # Verify it's gone
        get_resp = requests.get(
            f"{BASE_URL}/get_template/{seeded_template}",
            timeout=10,
        )
        assert get_resp.json()["success"] is False

    def test_delete_nonexistent_template(self):
        resp = requests.post(
            f"{BASE_URL}/delete_template/nonexistent_tpl_abc",
            timeout=10,
            allow_redirects=False,
        )
        assert resp.status_code == 302


class TestTemplatesPage:
    """GET /templates -- verify templates page renders."""

    def test_templates_page_renders(self):
        resp = requests.get(f"{BASE_URL}/templates", timeout=10)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("Content-Type", "")

    def test_templates_page_shows_template(self, seeded_template):
        resp = requests.get(f"{BASE_URL}/templates", timeout=10)
        assert resp.status_code == 200
        assert seeded_template in resp.text
