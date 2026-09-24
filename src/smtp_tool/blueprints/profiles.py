"""Profile CRUD routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    request,
    url_for,
)

from smtp_tool.services import config_service
from smtp_tool.services.smtp_service import DEFAULT_SMTP_PORT

logger = logging.getLogger(__name__)

profiles_bp = Blueprint("profiles", __name__)


def _error_response(message: str, is_ajax: bool):
    if is_ajax:
        return jsonify({"success": False, "message": message})
    flash(message, "danger")
    return redirect(url_for("settings_bp.settings_page"))


# -----------------------------------------------------------------------
# POST /add_profile
# -----------------------------------------------------------------------


@profiles_bp.route("/add_profile", methods=["POST"])
def add_profile():
    """API endpoint to add a new SMTP profile."""
    is_ajax = "XMLHttpRequest" in request.headers.get("X-Requested-With", "")

    try:
        profile_data = {
            "name": request.form.get("name"),
            "server": request.form.get("server"),
            "port": int(request.form.get("port", DEFAULT_SMTP_PORT)),
            "use_tls": request.form.get("use_tls") in ["on", "true", True],
            "use_ssl": request.form.get("use_ssl") in ["on", "true", True],
            "no_tls_verify": request.form.get("no_tls_verify")
            in ["on", "true", True],
            "username": request.form.get("username", ""),
            "password": request.form.get("password", ""),
        }

        if not profile_data["name"] or not profile_data["server"]:
            return _error_response("Profile name and server are required", is_ajax)

        result = config_service.add_profile(profile_data)

        if not result:
            return _error_response("Failed to save profile to the database", is_ajax)

        if is_ajax:
            return jsonify(
                {"success": True, "message": "SMTP profile saved successfully"}
            )
        else:
            flash("SMTP profile added successfully", "success")
            return redirect(url_for("settings_bp.settings_page"))

    except Exception as e:
        logger.exception("Error adding profile")
        return _error_response(f"Error adding profile: {e}", is_ajax)


# -----------------------------------------------------------------------
# POST /delete_profile/<name>
# -----------------------------------------------------------------------


@profiles_bp.route("/delete_profile/<name>", methods=["POST"])
def delete_profile(name: str):
    """API endpoint to delete an SMTP profile."""
    try:
        config_service.delete_profile(name)
        flash(f"Profile {name} deleted successfully", "success")
        return redirect(url_for("settings_bp.settings_page"))
    except Exception as e:
        logger.exception("Error deleting profile")
        flash(f"Error deleting profile: {e}", "danger")
        return redirect(url_for("settings_bp.settings_page"))
