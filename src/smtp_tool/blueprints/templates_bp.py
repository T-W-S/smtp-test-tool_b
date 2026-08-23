"""Template CRUD routes."""

from __future__ import annotations

import logging
import os

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

from smtp_tool.services import config_service

logger = logging.getLogger(__name__)

templates_bp = Blueprint("templates_bp", __name__)


# -----------------------------------------------------------------------
# GET /templates
# -----------------------------------------------------------------------


@templates_bp.route("/templates")
def templates_page():
    """Render the templates page for managing email templates."""
    all_templates = config_service.get_templates()

    # Filter out internal templates (marked with underscore prefix)
    email_templates = {
        k: v for k, v in all_templates.items() if not k.startswith("_")
    }

    template_names = list(all_templates.keys())
    filtered_names = list(email_templates.keys())
    logger.info("All templates: %s", template_names)
    logger.info("Filtered templates: %s", filtered_names)

    return render_template("templates.html", email_templates=email_templates)


# -----------------------------------------------------------------------
# POST /add_template
# -----------------------------------------------------------------------


@templates_bp.route("/add_template", methods=["POST"])
def add_template():
    """API endpoint to add a new email template."""
    try:
        template_data: dict = {
            "name": request.form.get("name"),
            "subject": request.form.get("subject"),
            "body_type": request.form.get("body_type", "plain"),
            "body": request.form.get("body"),
        }

        if not template_data["name"] or not template_data["body"]:
            return jsonify(
                {
                    "success": False,
                    "message": "Template name and body are required",
                }
            )

        # Handle file attachment if provided
        attachment_file = request.files.get("attachment")
        if attachment_file and attachment_file.filename:
            try:
                config_dir = os.environ.get(
                    "SMTP_CONFIG_DIR",
                    os.path.join(os.path.expanduser("~"), ".smtp_tool"),
                )
                attachment_dir = os.path.join(config_dir, "attachments")
                os.makedirs(attachment_dir, exist_ok=True)

                attachment_path = os.path.join(
                    attachment_dir, secure_filename(attachment_file.filename)
                )
                attachment_file.save(attachment_path)

                template_data["attachment"] = {
                    "filename": secure_filename(attachment_file.filename),
                    "path": attachment_path,
                }

                logger.info(
                    "Saved attachment %s for template %s",
                    attachment_file.filename,
                    template_data["name"],
                )
            except Exception as att_error:
                logger.error("Error saving attachment: %s", att_error)
                # Continue without attachment if there's an error

        config_service.add_template(template_data)
        flash("Email template added successfully", "success")
        return redirect(url_for("templates_bp.templates_page"))

    except Exception as e:
        logger.exception("Error adding template")
        flash(f"Error adding template: {e}", "danger")
        return redirect(url_for("templates_bp.templates_page"))


# -----------------------------------------------------------------------
# POST /delete_template/<name>
# -----------------------------------------------------------------------


@templates_bp.route("/delete_template/<name>", methods=["POST"])
def delete_template(name: str):
    """API endpoint to delete an email template."""
    try:
        config_service.delete_template(name)
        flash(f"Template {name} deleted successfully", "success")
        return redirect(url_for("templates_bp.templates_page"))
    except Exception as e:
        logger.exception("Error deleting template")
        flash(f"Error deleting template: {e}", "danger")
        return redirect(url_for("templates_bp.templates_page"))


# -----------------------------------------------------------------------
# GET /get_template/<name>
# -----------------------------------------------------------------------


@templates_bp.route("/get_template/<name>")
def get_template(name: str):
    """API endpoint to get a specific email template."""
    try:
        template = config_service.get_template(name)
        if template:
            return jsonify({"success": True, "template": template})
        else:
            return jsonify(
                {"success": False, "message": f"Template {name} not found"}
            )
    except Exception as e:
        logger.exception("Error getting template")
        return jsonify(
            {"success": False, "message": f"Error getting template: {e}"}
        )
