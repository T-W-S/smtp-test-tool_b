"""Tests for the config_service module (profile, template, log, settings CRUD)."""

from __future__ import annotations

import pytest

from smtp_tool.services import config_service


# ========================================================================
# Profile CRUD
# ========================================================================


class TestProfileCRUD:
    """Profile create, read, update, delete operations."""

    def _make_profile(self, name="test-profile", **overrides):
        data = {
            "name": name,
            "server": "smtp.example.com",
            "port": 587,
            "use_tls": True,
            "use_ssl": False,
            "no_tls_verify": False,
            "username": "user",
            "password": "pass",
        }
        data.update(overrides)
        return data

    def test_add_profile(self, app):
        with app.app_context():
            result = config_service.add_profile(self._make_profile())
            assert result is True

    def test_get_profile(self, app):
        with app.app_context():
            config_service.add_profile(self._make_profile())
            profile = config_service.get_profile("test-profile")
            assert profile is not None
            assert profile["server"] == "smtp.example.com"
            assert profile["port"] == 587
            assert profile["use_tls"] is True

    def test_get_profile_nonexistent(self, app):
        with app.app_context():
            assert config_service.get_profile("nonexistent") is None

    def test_get_all_profiles(self, app):
        with app.app_context():
            config_service.add_profile(self._make_profile("profile-a"))
            config_service.add_profile(self._make_profile("profile-b"))
            profiles = config_service.get_profiles()
            assert len(profiles) == 2
            assert "profile-a" in profiles
            assert "profile-b" in profiles

    def test_update_profile_upsert(self, app):
        with app.app_context():
            config_service.add_profile(self._make_profile())
            config_service.add_profile(
                self._make_profile(server="new-server.com", port=465)
            )
            profile = config_service.get_profile("test-profile")
            assert profile["server"] == "new-server.com"
            assert profile["port"] == 465

    def test_delete_profile(self, app):
        with app.app_context():
            config_service.add_profile(self._make_profile())
            result = config_service.delete_profile("test-profile")
            assert result is True
            assert config_service.get_profile("test-profile") is None

    def test_delete_nonexistent_profile(self, app):
        with app.app_context():
            result = config_service.delete_profile("nonexistent")
            assert result is False


# ========================================================================
# Template CRUD
# ========================================================================


class TestTemplateCRUD:
    """Template create, read, update, delete operations."""

    def _make_template(self, name="test-template", **overrides):
        data = {
            "name": name,
            "subject": "Test Subject",
            "body_type": "plain",
            "body": "Hello, world!",
        }
        data.update(overrides)
        return data

    def test_add_template(self, app):
        with app.app_context():
            result = config_service.add_template(self._make_template())
            assert result is True

    def test_get_template(self, app):
        with app.app_context():
            config_service.add_template(self._make_template())
            tpl = config_service.get_template("test-template")
            assert tpl is not None
            assert tpl["subject"] == "Test Subject"
            assert tpl["body"] == "Hello, world!"

    def test_get_template_nonexistent(self, app):
        with app.app_context():
            assert config_service.get_template("nonexistent") is None

    def test_get_all_templates(self, app):
        with app.app_context():
            # Note: create_app seeds default templates, so we add on top
            config_service.add_template(self._make_template("tpl-x"))
            config_service.add_template(self._make_template("tpl-y"))
            templates = config_service.get_templates()
            assert "tpl-x" in templates
            assert "tpl-y" in templates

    def test_update_template_upsert(self, app):
        with app.app_context():
            config_service.add_template(self._make_template())
            config_service.add_template(
                self._make_template(subject="Updated Subject")
            )
            tpl = config_service.get_template("test-template")
            assert tpl["subject"] == "Updated Subject"

    def test_delete_template(self, app):
        with app.app_context():
            config_service.add_template(self._make_template())
            result = config_service.delete_template("test-template")
            assert result is True
            assert config_service.get_template("test-template") is None

    def test_delete_nonexistent_template(self, app):
        with app.app_context():
            result = config_service.delete_template("nonexistent")
            assert result is False


# ========================================================================
# Log CRUD
# ========================================================================


class TestLogCRUD:
    """Log add, get, clear, and cap enforcement."""

    def _make_log_entry(self, **overrides):
        data = {
            "timestamp": "2024-01-01 12:00:00",
            "profile": "default",
            "server": "smtp.example.com:587",
            "sender": "sender@example.com",
            "recipients": ["recipient@example.com"],
            "cc": [],
            "bcc": [],
            "subject": "Test",
            "status": "Success",
            "smtp_log": [],
            "attachments": [],
        }
        data.update(overrides)
        return data

    def test_add_log_entry(self, app):
        with app.app_context():
            result = config_service.add_log_entry(self._make_log_entry())
            assert result is True

    def test_get_logs(self, app):
        with app.app_context():
            config_service.add_log_entry(self._make_log_entry(subject="Email 1"))
            config_service.add_log_entry(self._make_log_entry(subject="Email 2"))
            logs = config_service.get_logs()
            assert len(logs) == 2
            subjects = [log["subject"] for log in logs]
            assert "Email 1" in subjects
            assert "Email 2" in subjects

    def test_clear_logs(self, app):
        with app.app_context():
            config_service.add_log_entry(self._make_log_entry())
            result = config_service.clear_logs()
            assert result is True
            assert config_service.get_logs() == []

    def test_log_entry_cap_enforcement(self, app):
        """Adding more than MAX_LOG_ENTRIES should trim oldest entries."""
        with app.app_context():
            for i in range(config_service.MAX_LOG_ENTRIES + 5):
                config_service.add_log_entry(
                    self._make_log_entry(subject=f"Email {i}")
                )
            logs = config_service.get_logs()
            assert len(logs) == config_service.MAX_LOG_ENTRIES

    def test_log_entry_stores_error(self, app):
        with app.app_context():
            config_service.add_log_entry(
                self._make_log_entry(status="Failed", error="Connection refused")
            )
            logs = config_service.get_logs()
            assert logs[0]["error"] == "Connection refused"

    def test_log_entry_stores_message_id(self, app):
        with app.app_context():
            config_service.add_log_entry(
                self._make_log_entry(message_id="<abc@example.com>")
            )
            logs = config_service.get_logs()
            assert logs[0]["message_id"] == "<abc@example.com>"


# ========================================================================
# Settings CRUD
# ========================================================================


class TestSettingsCRUD:
    """Settings get, update, and saved address operations."""

    def test_get_settings_defaults(self, app):
        with app.app_context():
            settings = config_service.get_settings()
            # Default settings should be populated
            assert "send_hostname" in settings
            assert "default_sender" in settings
            assert "log_level" in settings
            assert "saved_senders" in settings
            assert "saved_recipients" in settings

    def test_update_settings(self, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            result = config_service.update_settings({"log_level": "DEBUG"})
            assert result is True
            settings = config_service.get_settings()
            assert settings["log_level"] == "DEBUG"

    def test_update_settings_ignores_address_lists(self, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            config_service.update_settings(
                {"saved_senders": ["should@not.overwrite"]}
            )
            settings = config_service.get_settings()
            # The saved_senders list should not have been overwritten
            assert "should@not.overwrite" not in settings["saved_senders"]

    def test_saved_senders_default(self, app):
        with app.app_context():
            settings = config_service.get_settings()
            assert isinstance(settings["saved_senders"], list)
            assert len(settings["saved_senders"]) >= 1

    def test_saved_recipients_default(self, app):
        with app.app_context():
            settings = config_service.get_settings()
            assert isinstance(settings["saved_recipients"], list)
            assert "recipient@example.com" in settings["saved_recipients"]

    def test_add_saved_sender(self, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            result = config_service.add_saved_sender("new@sender.com")
            assert result is True
            settings = config_service.get_settings()
            assert "new@sender.com" in settings["saved_senders"]

    def test_add_saved_sender_duplicate_noop(self, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            config_service.add_saved_sender("dup@sender.com")
            config_service.add_saved_sender("dup@sender.com")
            settings = config_service.get_settings()
            count = settings["saved_senders"].count("dup@sender.com")
            assert count == 1

    def test_remove_saved_sender(self, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            config_service.add_saved_sender("removeme@sender.com")
            result = config_service.remove_saved_sender("removeme@sender.com")
            assert result is True
            settings = config_service.get_settings()
            assert "removeme@sender.com" not in settings["saved_senders"]

    def test_remove_nonexistent_sender(self, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            result = config_service.remove_saved_sender("no@such.com")
            assert result is False

    def test_add_saved_recipient(self, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            result = config_service.add_saved_recipient("new@recipient.com")
            assert result is True
            settings = config_service.get_settings()
            assert "new@recipient.com" in settings["saved_recipients"]

    def test_remove_saved_recipient(self, app):
        with app.app_context():
            config_service.get_settings()  # seed defaults
            config_service.add_saved_recipient("gone@recipient.com")
            result = config_service.remove_saved_recipient("gone@recipient.com")
            assert result is True
            settings = config_service.get_settings()
            assert "gone@recipient.com" not in settings["saved_recipients"]


# ========================================================================
# Default template initialization
# ========================================================================


class TestDefaultTemplates:
    """init_default_templates seeds the DB when it is empty."""

    def test_default_templates_created(self, app):
        with app.app_context():
            # create_app already calls init_default_templates
            templates = config_service.get_templates()
            assert len(templates) >= 4
            assert "Plain Text Example" in templates
            assert "HTML Example" in templates

    def test_init_default_templates_idempotent(self, app):
        with app.app_context():
            before = len(config_service.get_templates())
            config_service.init_default_templates()
            after = len(config_service.get_templates())
            assert before == after
