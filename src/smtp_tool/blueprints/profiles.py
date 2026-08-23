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

logger = logging.getLogger(__name__)

profiles_bp = Blueprint("profiles", __name__)


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
            "port": int(request.form.get("port", 25)),
            "use_tls": request.form.get("use_tls") in ["on", "true", True],
            "use_ssl": request.form.get("use_ssl") in ["on", "true", True],
            "no_tls_verify": request.form.get("no_tls_verify")
            in ["on", "true", True],
            "username": request.form.get("username", ""),
            "password": request.form.get("password", ""),
        }

        if not profile_data["name"] or not profile_data["server"]:
            message = "Profile name and server are required"
            if is_ajax:
                return jsonify({"success": False, "message": message})
            else:
                flash(message, "danger")
                return redirect(url_for("settings_bp.settings_page"))

        config_service.add_profile(profile_data)

        if is_ajax:
            return jsonify(
                {"success": True, "message": "SMTP profile saved successfully"}
            )
        else:
            flash("SMTP profile added successfully", "success")
            return redirect(url_for("settings_bp.settings_page"))

    except Exception as e:
        logger.exception("Error adding profile")
        message = f"Error adding profile: {e}"
        if is_ajax:
            return jsonify({"success": False, "message": message})
        else:
            flash(message, "danger")
            return redirect(url_for("settings_bp.settings_page"))


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
