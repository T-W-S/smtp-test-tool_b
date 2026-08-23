"""Settings routes."""

from __future__ import annotations

import logging
import socket

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from smtp_tool.services import config_service

logger = logging.getLogger(__name__)

settings_bp = Blueprint("settings_bp", __name__)


# -----------------------------------------------------------------------
# GET /settings
# -----------------------------------------------------------------------


@settings_bp.route("/settings")
def settings_page():
    """Render the settings page for managing SMTP profiles."""
    smtp_profiles = config_service.get_profiles()
    app_settings = config_service.get_settings()
    return render_template(
        "settings.html", smtp_profiles=smtp_profiles, settings=app_settings
    )


# -----------------------------------------------------------------------
# GET /advanced_settings
# -----------------------------------------------------------------------


@settings_bp.route("/advanced_settings")
def advanced_settings():
    """Render the advanced settings page."""
    app_settings = config_service.get_settings()
    return render_template("advanced_settings.html", settings=app_settings)


# -----------------------------------------------------------------------
# POST /update_settings
# -----------------------------------------------------------------------


@settings_bp.route("/update_settings", methods=["POST"])
def update_settings():
    """API endpoint to update application settings."""
    try:
        settings_data: dict = {
            "send_hostname": request.form.get("send_hostname", ""),
            "default_sender": request.form.get("default_sender", ""),
            "log_level": request.form.get("log_level", "INFO"),
            "log_retention_days": int(
                request.form.get("log_retention_days", 30)
            ),
            "log_smtp_traffic": request.form.get("log_smtp_traffic") == "on",
            "log_message_content": request.form.get("log_message_content")
            == "on",
            "max_attachment_size_mb": int(
                request.form.get("max_attachment_size_mb", 10)
            ),
        }

        if not settings_data["send_hostname"]:
            settings_data["send_hostname"] = socket.gethostname()

        config_service.update_settings(settings_data)
        flash("Settings updated successfully", "success")
        return redirect(url_for("settings_bp.advanced_settings"))

    except Exception as e:
        logger.exception("Error updating settings")
        flash(f"Error updating settings: {e}", "danger")
        return redirect(url_for("settings_bp.advanced_settings"))
