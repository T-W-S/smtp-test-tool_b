"""Saved address routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)

from smtp_tool.services import config_service
from smtp_tool.services.email_validator import validate_email

logger = logging.getLogger(__name__)

addresses_bp = Blueprint("addresses", __name__)


# -----------------------------------------------------------------------
# GET /addresses
# -----------------------------------------------------------------------


@addresses_bp.route("/addresses")
def addresses_page():
    """Render the email addresses management page."""
    settings = config_service.get_settings()
    saved_senders = settings.get("saved_senders", [])
    saved_recipients = settings.get("saved_recipients", [])

    return render_template(
        "addresses.html",
        saved_senders=saved_senders,
        saved_recipients=saved_recipients,
    )


# -----------------------------------------------------------------------
# POST /save_sender
# -----------------------------------------------------------------------


@addresses_bp.route("/save_sender", methods=["POST"])
def save_sender():
    """API endpoint to save a sender email address."""
    try:
        data = request.get_json()
        email = data.get("email")

        try:
            validate_email(email)
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)})

        if config_service.add_saved_sender(email):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to save sender"})
    except Exception as e:
        logger.error("Error saving sender: %s", e)
        return jsonify({"success": False, "message": str(e)})


# -----------------------------------------------------------------------
# POST /save_recipient
# -----------------------------------------------------------------------


@addresses_bp.route("/save_recipient", methods=["POST"])
def save_recipient():
    """API endpoint to save a recipient email address."""
    try:
        data = request.get_json()
        email = data.get("email")

        try:
            validate_email(email)
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)})

        if config_service.add_saved_recipient(email):
            return jsonify({"success": True})
        else:
            return jsonify(
                {"success": False, "message": "Failed to save recipient"}
            )
    except Exception as e:
        logger.error("Error saving recipient: %s", e)
        return jsonify({"success": False, "message": str(e)})


# -----------------------------------------------------------------------
# POST /delete_sender
# -----------------------------------------------------------------------


@addresses_bp.route("/delete_sender", methods=["POST"])
def delete_sender():
    """API endpoint to delete a saved sender email address."""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in delete_sender request")
            return jsonify({"success": False, "message": "No data provided"})

        email = data.get("email")
        if not email:
            logger.error("No email provided in delete_sender request")
            return jsonify({"success": False, "message": "No email provided"})

        logger.info("Attempting to delete sender email: %s", email)

        result = config_service.remove_saved_sender(email)
        logger.info("Delete sender result: %s", result)

        if result:
            return jsonify(
                {"success": True, "message": "Email deleted successfully"}
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to delete sender"}
            )
    except Exception as e:
        logger.error("Error deleting sender: %s", e)
        return jsonify({"success": False, "message": str(e)})


# -----------------------------------------------------------------------
# POST /delete_recipient
# -----------------------------------------------------------------------


@addresses_bp.route("/delete_recipient", methods=["POST"])
def delete_recipient():
    """API endpoint to delete a saved recipient email address."""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in delete_recipient request")
            return jsonify({"success": False, "message": "No data provided"})

        email = data.get("email")
        if not email:
            logger.error("No email provided in delete_recipient request")
            return jsonify({"success": False, "message": "No email provided"})

        logger.info("Attempting to delete recipient email: %s", email)

        result = config_service.remove_saved_recipient(email)
        logger.info("Delete recipient result: %s", result)

        if result:
            return jsonify(
                {"success": True, "message": "Email deleted successfully"}
            )
        else:
            return jsonify(
                {"success": False, "message": "Failed to delete recipient"}
            )
    except Exception as e:
        logger.error("Error deleting recipient: %s", e)
        return jsonify({"success": False, "message": str(e)})
