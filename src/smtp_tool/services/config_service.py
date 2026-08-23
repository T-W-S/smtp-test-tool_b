"""SQLAlchemy-backed configuration service.

Drop-in replacement for the legacy ConfigManager that persists all data in
SQLite via Flask-SQLAlchemy instead of flat JSON files.  Every public function
mirrors the original ConfigManager API so that callers can switch with a simple
import change::

    from smtp_tool.services import config_service

    profiles = config_service.get_profiles()
"""

from __future__ import annotations

import json
import logging
import socket
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from smtp_tool.models import (
    LogEntry,
    Profile,
    SavedAddress,
    Setting,
    Template,
    db,
)
from smtp_tool.services.smtp_service import DEFAULT_SMTP_PORT

logger = logging.getLogger(__name__)

MAX_LOG_ENTRIES: int = 1000

# ---------------------------------------------------------------------------
# Default settings applied when the settings table is empty
# ---------------------------------------------------------------------------

_DEFAULT_SETTINGS: dict[str, Any] = {
    "send_hostname": socket.gethostname(),
    "default_sender": f"smtp@{socket.getfqdn()}",
    "log_level": "INFO",
    "log_retention_days": 30,
    "log_smtp_traffic": True,
    "log_message_content": False,
    "max_attachment_size_mb": 10,
}


# ========================================================================
# Profile CRUD
# ========================================================================


def get_profiles() -> dict[str, dict[str, Any]]:
    """Return all profiles as a dict keyed by profile name."""
    try:
        profiles: list[Profile] = Profile.query.all()
        return {
            p.name: {
                "server": p.server,
                "port": p.port,
                "use_tls": p.use_tls,
                "use_ssl": p.use_ssl,
                "no_tls_verify": p.no_tls_verify,
                "username": p.username,
                "password": p.password,
            }
            for p in profiles
        }
    except Exception as e:
        logger.error(f"Failed to read profiles: {e}")
        return {}


def get_profile(name: str) -> dict[str, Any] | None:
    """Return a single profile dict or ``None``."""
    try:
        p: Profile | None = Profile.query.filter_by(name=name).first()
        if p is None:
            return None
        return {
            "server": p.server,
            "port": p.port,
            "use_tls": p.use_tls,
            "use_ssl": p.use_ssl,
            "no_tls_verify": p.no_tls_verify,
            "username": p.username,
            "password": p.password,
        }
    except Exception as e:
        logger.error(f"Failed to read profile '{name}': {e}")
        return None


def add_profile(profile_data: dict[str, Any]) -> bool:
    """Add or update (upsert) a profile by name."""
    try:
        name = profile_data["name"]
        existing: Profile | None = Profile.query.filter_by(name=name).first()

        if existing is not None:
            existing.server = profile_data["server"]
            existing.port = profile_data["port"]
            existing.use_tls = profile_data["use_tls"]
            existing.use_ssl = profile_data["use_ssl"]
            existing.no_tls_verify = profile_data.get("no_tls_verify", False)
            existing.username = profile_data["username"]
            existing.password = profile_data["password"]
            existing.updated_at = datetime.now(UTC)
        else:
            profile = Profile(
                name=name,
                server=profile_data["server"],
                port=profile_data["port"],
                use_tls=profile_data["use_tls"],
                use_ssl=profile_data["use_ssl"],
                no_tls_verify=profile_data.get("no_tls_verify", False),
                username=profile_data["username"],
                password=profile_data["password"],
            )
            db.session.add(profile)

        db.session.commit()
        logger.info(f"Profile '{name}' saved successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to save profile: {e}")
        return False


def delete_profile(name: str) -> bool:
    """Delete a profile by name. Returns ``False`` if not found."""
    try:
        profile: Profile | None = Profile.query.filter_by(name=name).first()
        if profile is None:
            logger.warning(f"Profile '{name}' not found")
            return False

        db.session.delete(profile)
        db.session.commit()
        logger.info(f"Profile '{name}' deleted successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete profile: {e}")
        return False


# ========================================================================
# Template CRUD
# ========================================================================


def get_templates() -> dict[str, dict[str, Any]]:
    """Return all templates as a dict keyed by template name."""
    try:
        templates: list[Template] = Template.query.all()
        return {
            t.name: {
                "subject": t.subject,
                "body_type": t.body_type,
                "body": t.body,
            }
            for t in templates
        }
    except Exception as e:
        logger.error(f"Failed to read templates: {e}")
        return {}


def get_template(name: str) -> dict[str, Any] | None:
    """Return a single template dict or ``None``."""
    try:
        t: Template | None = Template.query.filter_by(name=name).first()
        if t is None:
            return None
        return {
            "subject": t.subject,
            "body_type": t.body_type,
            "body": t.body,
        }
    except Exception as e:
        logger.error(f"Failed to read template '{name}': {e}")
        return None


def add_template(template_data: dict[str, Any]) -> bool:
    """Add or update (upsert) a template by name."""
    try:
        name = template_data["name"]
        existing: Template | None = Template.query.filter_by(name=name).first()

        if existing is not None:
            existing.subject = template_data.get("subject", "")
            existing.body_type = template_data.get("body_type", "plain")
            existing.body = template_data.get("body", "")
            existing.updated_at = datetime.now(UTC)
        else:
            template = Template(
                name=name,
                subject=template_data.get("subject", ""),
                body_type=template_data.get("body_type", "plain"),
                body=template_data.get("body", ""),
            )
            db.session.add(template)

        db.session.commit()
        logger.info(f"Template '{name}' saved successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to save template: {e}")
        return False


def delete_template(name: str) -> bool:
    """Delete a template by name. Returns ``False`` if not found."""
    try:
        template: Template | None = Template.query.filter_by(name=name).first()
        if template is None:
            logger.warning(f"Template '{name}' not found")
            return False

        db.session.delete(template)
        db.session.commit()
        logger.info(f"Template '{name}' deleted successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete template: {e}")
        return False


# ========================================================================
# Log CRUD
# ========================================================================


def get_logs() -> list[dict[str, Any]]:
    """Return all log entries as a list of dicts."""
    try:
        entries: list[LogEntry] = LogEntry.query.order_by(LogEntry.id.asc()).all()
        return [_log_entry_to_dict(e) for e in entries]
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return []


def add_log_entry(log_entry: dict[str, Any]) -> bool:
    """Add a log entry, capping at :data:`MAX_LOG_ENTRIES` rows."""
    try:
        timestamp = log_entry.get("timestamp") or datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        entry = LogEntry(
            timestamp=timestamp,
            profile_name=log_entry.get("profile", ""),
            server=log_entry.get("server", ""),
            sender=log_entry.get("sender", ""),
            recipients=log_entry.get("recipients", []),
            cc=log_entry.get("cc", []),
            bcc=log_entry.get("bcc", []),
            subject=log_entry.get("subject", ""),
            status=log_entry.get("status", ""),
            error=log_entry.get("error"),
            message_id=log_entry.get("message_id"),
            smtp_log=log_entry.get("smtp_log", []),
            attachments=log_entry.get("attachments", []),
            body=log_entry.get("body"),
            body_type=log_entry.get("body_type"),
        )
        db.session.add(entry)
        db.session.flush()  # assign id so we can count

        # Enforce cap: delete oldest entries exceeding MAX_LOG_ENTRIES
        total = LogEntry.query.count()
        if total > MAX_LOG_ENTRIES:
            excess = total - MAX_LOG_ENTRIES
            oldest = (
                LogEntry.query.order_by(LogEntry.id.asc()).limit(excess).all()
            )
            for old in oldest:
                db.session.delete(old)

        db.session.commit()
        logger.debug("Log entry added successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add log entry: {e}")
        return False


def clear_logs() -> bool:
    """Delete all log entries."""
    try:
        LogEntry.query.delete()
        db.session.commit()
        logger.info("Logs cleared successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to clear logs: {e}")
        return False


def get_detailed_logs(
    limit: int | None = None,
    search_text: str | None = None,
) -> list[dict[str, Any]]:
    """Return logs with optional text filtering and row limit.

    Results are sorted newest-first (descending timestamp).
    """
    try:
        query = LogEntry.query

        if search_text:
            like_pattern = f"%{search_text}%"
            query = query.filter(
                db.or_(
                    LogEntry.profile_name.ilike(like_pattern),
                    LogEntry.sender.ilike(like_pattern),
                    LogEntry.subject.ilike(like_pattern),
                    LogEntry.status.ilike(like_pattern),
                    LogEntry.error.ilike(like_pattern),
                )
            )

        # Newest first
        query = query.order_by(LogEntry.timestamp.desc())

        if limit is not None and isinstance(limit, int) and limit > 0:
            query = query.limit(limit)

        entries: list[LogEntry] = query.all()

        # Post-filter: also search inside JSON recipients field when search
        # text is provided (mirrors the original behaviour that searched the
        # joined recipients list).
        if search_text:
            needle = search_text.lower()
            filtered: list[dict[str, Any]] = []
            for e in entries:
                filtered.append(_log_entry_to_dict(e))

            # Also scan entries we might have missed because the recipients
            # match lives inside a JSON column.  Re-query without the SQL
            # filter and do a Python-side check for entries that were not
            # already included.
            all_query = LogEntry.query.order_by(LogEntry.timestamp.desc())
            if limit is not None and isinstance(limit, int) and limit > 0:
                all_query = all_query.limit(limit)
            all_entries = all_query.all()
            seen_ids = {e.id for e in entries}
            for e in all_entries:
                if e.id in seen_ids:
                    continue
                recipients_str = " ".join(e.recipients) if isinstance(e.recipients, list) else str(e.recipients or "")
                if needle in recipients_str.lower():
                    filtered.append(_log_entry_to_dict(e))
            return filtered

        return [_log_entry_to_dict(e) for e in entries]
    except Exception as e:
        logger.error(f"Failed to get detailed logs: {e}")
        return []


def _log_entry_to_dict(entry: LogEntry) -> dict[str, Any]:
    """Convert a :class:`LogEntry` ORM instance to a plain dict."""
    return {
        "timestamp": entry.timestamp,
        "profile": entry.profile_name,
        "server": entry.server,
        "sender": entry.sender,
        "recipients": entry.recipients,
        "cc": entry.cc,
        "bcc": entry.bcc,
        "subject": entry.subject,
        "status": entry.status,
        "error": entry.error,
        "message_id": entry.message_id,
        "smtp_log": entry.smtp_log,
        "attachments": entry.attachments,
        "body": entry.body,
        "body_type": entry.body_type,
    }


# ========================================================================
# Settings CRUD
# ========================================================================


def _ensure_default_settings() -> None:
    """Seed the settings table with defaults when it is empty."""
    if Setting.query.count() > 0:
        return

    try:
        for key, value in _DEFAULT_SETTINGS.items():
            db.session.add(Setting(key=key, value=value))

        # Seed default saved addresses (skip if already present)
        default_sender = f"smtp@{socket.getfqdn()}"
        for email, addr_type in [
            (default_sender, "sender"),
            ("test@example.com", "sender"),
            ("recipient@example.com", "recipient"),
        ]:
            if not SavedAddress.query.filter_by(email=email, address_type=addr_type).first():
                db.session.add(SavedAddress(email=email, address_type=addr_type))

        db.session.commit()
        logger.info("Initialized default settings")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to initialize default settings: {e}")


def get_settings() -> dict[str, Any]:
    """Reconstruct a flat settings dict from the key-value table + addresses.

    The returned dict has the same shape as the original JSON-backed
    ``get_settings()`` including ``saved_senders`` and ``saved_recipients``
    lists.
    """
    try:
        _ensure_default_settings()

        settings: dict[str, Any] = {}

        # Key-value pairs
        for s in Setting.query.all():
            settings[s.key] = s.value

        # Saved addresses
        senders = (
            SavedAddress.query.filter_by(address_type="sender")
            .order_by(SavedAddress.id.asc())
            .all()
        )
        recipients = (
            SavedAddress.query.filter_by(address_type="recipient")
            .order_by(SavedAddress.id.asc())
            .all()
        )
        settings["saved_senders"] = [a.email for a in senders]
        settings["saved_recipients"] = [a.email for a in recipients]

        return settings
    except Exception as e:
        logger.error(f"Failed to read settings: {e}")
        # Fallback defaults (mirrors original ConfigManager behaviour)
        return {
            **_DEFAULT_SETTINGS,
            "saved_senders": [f"smtp@{socket.getfqdn()}", "test@example.com"],
            "saved_recipients": ["recipient@example.com"],
        }


def update_settings(settings_data: dict[str, Any]) -> bool:
    """Upsert key-value settings.

    ``saved_senders`` and ``saved_recipients`` keys in *settings_data* are
    preserved (not overwritten) -- address list management is handled by the
    dedicated ``add_saved_*`` / ``remove_saved_*`` helpers.
    """
    try:
        _ensure_default_settings()

        for key, value in settings_data.items():
            # Skip address lists -- they are managed separately
            if key in ("saved_senders", "saved_recipients"):
                continue

            existing: Setting | None = Setting.query.filter_by(key=key).first()
            if existing is not None:
                existing.value = value
            else:
                db.session.add(Setting(key=key, value=value))

        db.session.commit()
        logger.info("Settings updated successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update settings: {e}")
        return False


# ========================================================================
# Saved address helpers
# ========================================================================


def add_saved_sender(email: str) -> bool:
    """Add *email* to saved senders (no-op if it already exists)."""
    return _add_saved_address(email, "sender")


def remove_saved_sender(email: str) -> bool:
    """Remove *email* from saved senders."""
    return _remove_saved_address(email, "sender")


def add_saved_recipient(email: str) -> bool:
    """Add *email* to saved recipients (no-op if it already exists)."""
    return _add_saved_address(email, "recipient")


def remove_saved_recipient(email: str) -> bool:
    """Remove *email* from saved recipients."""
    return _remove_saved_address(email, "recipient")


def _add_saved_address(email: str, address_type: str) -> bool:
    """Internal helper to add a saved address."""
    try:
        existing = SavedAddress.query.filter_by(
            email=email, address_type=address_type
        ).first()
        if existing is None:
            db.session.add(
                SavedAddress(email=email, address_type=address_type)
            )
            db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add saved {address_type}: {e}")
        return False


def _remove_saved_address(email: str, address_type: str) -> bool:
    """Internal helper to remove a saved address."""
    try:
        addr = SavedAddress.query.filter_by(
            email=email, address_type=address_type
        ).first()
        if addr is None:
            logger.warning(
                f"Cannot remove {address_type} {email}: not found"
            )
            return False

        db.session.delete(addr)
        db.session.commit()
        logger.info(f"Removed {email} from saved {address_type}s")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to remove saved {address_type} {email}: {e}")
        return False


# ========================================================================
# JSON -> SQLite migration
# ========================================================================


def migrate_from_json(config_dir: str) -> None:
    """Import data from legacy JSON files into the database.

    Only runs when the DB tables are empty **and** JSON files exist.  After a
    successful import each JSON file is renamed to ``*.json.migrated`` so that
    the migration is idempotent.
    """
    config_path = Path(config_dir)
    json_files = {
        "profiles": config_path / "profiles.json",
        "templates": config_path / "templates.json",
        "logs": config_path / "logs.json",
        "settings": config_path / "settings.json",
    }

    existing_files = {k: v for k, v in json_files.items() if v.is_file()}
    if not existing_files:
        return  # nothing to migrate

    migrated_any = False

    # --- Profiles ---
    if "profiles" in existing_files and Profile.query.count() == 0:
        try:
            with open(existing_files["profiles"], "r") as fh:
                profiles: dict[str, Any] = json.load(fh)
            for name, data in profiles.items():
                db.session.add(
                    Profile(
                        name=name,
                        server=data.get("server", ""),
                        port=int(data.get("port", DEFAULT_SMTP_PORT)),
                        use_tls=bool(data.get("use_tls", False)),
                        use_ssl=bool(data.get("use_ssl", False)),
                        no_tls_verify=bool(data.get("no_tls_verify", False)),
                        username=data.get("username", ""),
                        password=data.get("password", ""),
                    )
                )
            db.session.commit()
            _rename_migrated(existing_files["profiles"])
            migrated_any = True
            logger.info(f"Migrated {len(profiles)} profiles from JSON")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to migrate profiles: {e}")

    # --- Templates ---
    if "templates" in existing_files and Template.query.count() == 0:
        try:
            with open(existing_files["templates"], "r") as fh:
                templates: dict[str, Any] = json.load(fh)
            for name, data in templates.items():
                db.session.add(
                    Template(
                        name=name,
                        subject=data.get("subject", ""),
                        body_type=data.get("body_type", "plain"),
                        body=data.get("body", ""),
                    )
                )
            db.session.commit()
            _rename_migrated(existing_files["templates"])
            migrated_any = True
            logger.info(f"Migrated {len(templates)} templates from JSON")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to migrate templates: {e}")

    # --- Logs ---
    if "logs" in existing_files and LogEntry.query.count() == 0:
        try:
            with open(existing_files["logs"], "r") as fh:
                logs: list[dict[str, Any]] = json.load(fh)
            # Only keep the most recent MAX_LOG_ENTRIES
            if len(logs) > MAX_LOG_ENTRIES:
                logs = logs[-MAX_LOG_ENTRIES:]
            for log in logs:
                db.session.add(
                    LogEntry(
                        timestamp=log.get(
                            "timestamp",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                        profile_name=log.get("profile", ""),
                        server=log.get("server", ""),
                        sender=log.get("sender", ""),
                        recipients=log.get("recipients", []),
                        cc=log.get("cc", []),
                        bcc=log.get("bcc", []),
                        subject=log.get("subject", ""),
                        status=log.get("status", ""),
                        error=log.get("error"),
                        message_id=log.get("message_id"),
                        smtp_log=log.get("smtp_log", []),
                        attachments=log.get("attachments", []),
                        body=log.get("body"),
                        body_type=log.get("body_type"),
                    )
                )
            db.session.commit()
            _rename_migrated(existing_files["logs"])
            migrated_any = True
            logger.info(f"Migrated {len(logs)} log entries from JSON")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to migrate logs: {e}")

    # --- Settings + Saved Addresses ---
    if "settings" in existing_files and Setting.query.count() == 0:
        try:
            with open(existing_files["settings"], "r") as fh:
                settings: dict[str, Any] = json.load(fh)

            # Separate saved addresses from scalar settings
            saved_senders: list[str] = settings.pop("saved_senders", [])
            saved_recipients: list[str] = settings.pop("saved_recipients", [])

            for key, value in settings.items():
                db.session.add(Setting(key=key, value=value))

            for email in saved_senders:
                db.session.add(
                    SavedAddress(email=email, address_type="sender")
                )
            for email in saved_recipients:
                db.session.add(
                    SavedAddress(email=email, address_type="recipient")
                )

            db.session.commit()
            _rename_migrated(existing_files["settings"])
            migrated_any = True
            logger.info("Migrated settings from JSON")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to migrate settings: {e}")

    if migrated_any:
        logger.info("JSON-to-SQLite migration completed")


def _rename_migrated(filepath: str | Path) -> None:
    """Rename a successfully migrated JSON file."""
    try:
        p = Path(filepath)
        p.rename(p.with_suffix(".json.migrated"))
    except OSError as e:
        logger.warning(f"Could not rename {filepath}: {e}")


# ========================================================================
# Default template initialization
# ========================================================================


def init_default_templates() -> None:
    """Seed the templates table with built-in examples when it is empty."""
    if Template.query.count() > 0:
        return

    _DEFAULT_TEMPLATES: list[dict[str, str]] = [
        {
            "name": "Plain Text Example",
            "subject": "Test Email - Plain Text",
            "body_type": "plain",
            "body": (
                "Hello,\n"
                "\n"
                "This is a sample plain text email for testing SMTP servers.\n"
                "\n"
                "Features to note:\n"
                "- No formatting\n"
                "- Simple text content\n"
                "- Can be used to test basic email delivery\n"
                "\n"
                "Regards,\n"
                "SMTP Testing Tool"
            ),
        },
        {
            "name": "HTML Example",
            "subject": "Test Email - HTML Format",
            "body_type": "html",
            "body": (
                '<!DOCTYPE html>\n'
                '<html>\n'
                '<head>\n'
                '    <meta charset="UTF-8">\n'
                '    <title>HTML Email Test</title>\n'
                '</head>\n'
                '<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">\n'
                '    <header style="background-color: #4a69bd; color: white; padding: 20px; text-align: center;">\n'
                '        <h1 style="margin: 0;">HTML Email Test</h1>\n'
                '    </header>\n'
                '    \n'
                '    <div style="padding: 20px;">\n'
                '        <p>This is a <strong>sample HTML email</strong> for testing SMTP servers.</p>\n'
                '        \n'
                '        <h2 style="color: #4a69bd; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Features to note:</h2>\n'
                '        \n'
                '        <ul style="list-style-type: circle; padding-left: 20px;">\n'
                '            <li>HTML formatting</li>\n'
                '            <li>CSS styling</li>\n'
                '            <li>Unicode support: こんにちは (Hello)</li>\n'
                '        </ul>\n'
                '        \n'
                '        <div style="background-color: #f8f9fa; border-left: 4px solid #4a69bd; margin: 20px 0; padding: 15px;">\n'
                '            This is an example information box to show more complex HTML.\n'
                '        </div>\n'
                '        \n'
                '        <p>You can test how your email client renders various HTML elements:</p>\n'
                '        \n'
                '        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">\n'
                '            <tr style="background-color: #4a69bd; color: white;">\n'
                '                <th style="padding: 10px; border: 1px solid #ddd;">Element</th>\n'
                '                <th style="padding: 10px; border: 1px solid #ddd;">Support</th>\n'
                '            </tr>\n'
                '            <tr>\n'
                '                <td style="padding: 10px; border: 1px solid #ddd;">Tables</td>\n'
                '                <td style="padding: 10px; border: 1px solid #ddd;">✓</td>\n'
                '            </tr>\n'
                '            <tr style="background-color: #f2f2f2;">\n'
                '                <td style="padding: 10px; border: 1px solid #ddd;">Styled text</td>\n'
                '                <td style="padding: 10px; border: 1px solid #ddd;">✓</td>\n'
                '            </tr>\n'
                '        </table>\n'
                '    </div>\n'
                '    \n'
                '    <footer style="background-color: #f2f2f2; padding: 15px; text-align: center; font-size: 12px;">\n'
                '        <p>This email was sent from the SMTP Testing Tool</p>\n'
                '    </footer>\n'
                '</body>\n'
                '</html>'
            ),
        },
        {
            "name": "EICAR Antivirus Test",
            "subject": "EICAR Antivirus Test File",
            "body_type": "plain",
            "body": (
                "This email contains the EICAR antivirus test file as an attachment.\n"
                "\n"
                "The EICAR test file is a standard test file developed by the European Institute "
                "for Computer Antivirus Research to safely test antivirus software without using actual malware.\n"
                "\n"
                "When this email is delivered, most antivirus systems should detect the attachment "
                "as a threat, even though it's completely harmless.\n"
                "\n"
                "Note: Your email system or antivirus might block this email entirely.\n"
            ),
        },
        {
            "name": "SPF Test",
            "subject": "SPF Authentication Test",
            "body_type": "plain",
            "body": (
                "This is a test email specifically for checking SPF validation.\n"
                "\n"
                "The Sender Policy Framework (SPF) is an email authentication method designed to "
                "detect email spoofing.\n"
                "When this email is received, the receiving server should check whether the sending "
                "server is authorized\n"
                "to send email on behalf of the domain in the From address.\n"
                "\n"
                "If properly implemented, this test message will help verify SPF functionality.\n"
            ),
        },
    ]

    try:
        for tpl in _DEFAULT_TEMPLATES:
            db.session.add(
                Template(
                    name=tpl["name"],
                    subject=tpl["subject"],
                    body_type=tpl["body_type"],
                    body=tpl["body"],
                )
            )
        db.session.commit()
        logger.info("Initialized default email templates")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to initialize default templates: {e}")
