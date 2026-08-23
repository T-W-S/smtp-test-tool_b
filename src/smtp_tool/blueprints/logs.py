"""Log viewing routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    url_for,
)

from smtp_tool.services import config_service

logger = logging.getLogger(__name__)

logs_bp = Blueprint("logs", __name__)


# -----------------------------------------------------------------------
# GET /logs
# -----------------------------------------------------------------------


@logs_bp.route("/logs")
def logs_page():
    """Render the logs page for viewing email sending history."""
    log_entries = config_service.get_logs()
    return render_template("logs.html", log_entries=log_entries)


# -----------------------------------------------------------------------
# POST /clear_logs
# -----------------------------------------------------------------------


@logs_bp.route("/clear_logs", methods=["POST"])
def clear_logs():
    """API endpoint to clear all logs."""
    try:
        config_service.clear_logs()
        flash("Logs cleared successfully", "success")
        return redirect(url_for("logs.logs_page"))
    except Exception as e:
        logger.exception("Error clearing logs")
        flash(f"Error clearing logs: {e}", "danger")
        return redirect(url_for("logs.logs_page"))
