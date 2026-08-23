"""Tests for the email_validator module."""

from __future__ import annotations

import pytest

from smtp_tool.services.email_validator import validate_email


# ---------------------------------------------------------------------------
# Valid emails
# ---------------------------------------------------------------------------


def test_valid_email_passes():
    assert validate_email("user@example.com") is True


def test_valid_email_with_plus():
    assert validate_email("user+tag@example.com") is True


def test_valid_email_with_dots_in_local():
    assert validate_email("first.last@example.com") is True


def test_valid_email_with_subdomain():
    assert validate_email("user@mail.example.co.uk") is True


def test_valid_email_with_numbers():
    assert validate_email("user123@example456.com") is True


def test_valid_email_with_hyphens_in_domain():
    assert validate_email("user@my-domain.com") is True


def test_valid_email_stripped_whitespace():
    assert validate_email("  user@example.com  ") is True


# ---------------------------------------------------------------------------
# Empty / missing
# ---------------------------------------------------------------------------


def test_empty_email_raises():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_email("")


def test_whitespace_only_raises():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_email("   ")


# ---------------------------------------------------------------------------
# Length constraints
# ---------------------------------------------------------------------------


def test_email_too_long_raises():
    local = "a" * 64
    domain = "b" * 186 + ".com"  # total > 254
    email = f"{local}@{domain}"
    assert len(email) > 254
    with pytest.raises(ValueError, match="too long"):
        validate_email(email)


def test_local_part_too_long_raises():
    local = "a" * 65  # > 64
    email = f"{local}@example.com"
    # The email is 65 + 1 + 11 = 77 chars, under 254 total
    with pytest.raises(ValueError, match="too long"):
        validate_email(email)


# ---------------------------------------------------------------------------
# Format violations
# ---------------------------------------------------------------------------


def test_consecutive_dots_in_local_raises():
    with pytest.raises(ValueError, match="consecutive dots"):
        validate_email("user..name@example.com")


def test_consecutive_dots_in_domain_raises():
    with pytest.raises(ValueError, match="consecutive dots"):
        validate_email("user@example..com")


def test_domain_without_dot_raises():
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("user@localhost")


def test_missing_at_sign_raises():
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("userexample.com")


def test_double_at_sign_raises():
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("user@@example.com")


def test_no_local_part_raises():
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("@example.com")


def test_no_domain_raises():
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("user@")


def test_special_characters_raises():
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("user name@example.com")


def test_unicode_in_local_part_raises():
    with pytest.raises(ValueError, match="format is invalid"):
        validate_email("uüser@example.com")
