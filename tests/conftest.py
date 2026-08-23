"""Shared test fixtures for the SMTP Test Tool test suite."""

from __future__ import annotations

import pytest

from smtp_tool import create_app
from smtp_tool.models import db as _db


@pytest.fixture()
def app():
    """Create a Flask application configured for testing with in-memory SQLite."""
    application = create_app(
        test_config={
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "SERVER_NAME": "localhost",
        }
    )
    yield application


@pytest.fixture()
def client(app):
    """Flask test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Provide a database session with tables created; drop all after test."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def runner(app):
    """Flask CLI test runner."""
    return app.test_cli_runner()
