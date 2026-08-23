"""Tests for page-rendering (GET) routes across all blueprints."""

from __future__ import annotations

import pytest


class TestPageRoutes:
    """Verify that all main GET routes return 200 and render without errors."""

    def test_index_page(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_settings_page(self, client):
        response = client.get("/settings")
        assert response.status_code == 200

    def test_templates_page(self, client):
        response = client.get("/templates")
        assert response.status_code == 200

    def test_logs_page(self, client):
        response = client.get("/logs")
        assert response.status_code == 200

    def test_addresses_page(self, client):
        response = client.get("/addresses")
        assert response.status_code == 200

    def test_advanced_settings_page(self, client):
        response = client.get("/advanced_settings")
        assert response.status_code == 200

    def test_health_check(self, client):
        response = client.get("/health_check")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data
