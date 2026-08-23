"""Email sending routes."""

from __future__ import annotations

import hashlib
import json
import logging
import socket
import time
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
)

from smtp_tool.services import config_service
from smtp_tool.services.email_validator import validate_email

logger = logging.getLogger(__name__)

REQUEST_CACHE_WINDOW_SECS: int = 8
REQUEST_CACHE_TTL_SECS: int = 30

email_bp = Blueprint("email", __name__)


# -----------------------------------------------------------------------
# GET /  --  main page
# -----------------------------------------------------------------------


@email_bp.route("/")
def index():
    """Render the main page for sending emails."""
    smtp_profiles = config_service.get_profiles()
    email_templates = config_service.get_templates()
    settings = config_service.get_settings()

    saved_senders = settings.get("saved_senders", [])
    saved_recipients = settings.get("saved_recipients", [])
    default_sender = settings.get("default_sender", "")

    return render_template(
        "index.html",
        smtp_profiles=smtp_profiles,
        email_templates=email_templates,
        saved_senders=saved_senders,
        saved_recipients=saved_recipients,
        default_sender=default_sender,
    )


# -----------------------------------------------------------------------
# POST /send_email
# -----------------------------------------------------------------------


@email_bp.route("/send_email", methods=["POST"])
def send_email():
    """API endpoint to send an email."""
    request_cache: dict = current_app.extensions["request_cache"]
    smtp_service = current_app.extensions["smtp_service"]

    # --- duplicate prevention -------------------------------------------
    current_time = time.time()

    form_items = sorted(
        [(k, v) for k, v in request.form.items() if k != "timestamp"]
    )
    form_string = str(form_items)
    request_id = hashlib.sha256(form_string.encode()).hexdigest()[:12]

    if request_id in request_cache:
        cache_entry = request_cache[request_id]
        if current_time - cache_entry["time"] < REQUEST_CACHE_WINDOW_SECS:
            logger.warning("BLOCKING duplicate request: %s", request_id)
            return jsonify(cache_entry["result"])

    # Clean old entries (keep last 30 seconds)
    stale_keys = [
        k
        for k, v in request_cache.items()
        if current_time - v.get("time", 0) >= REQUEST_CACHE_TTL_SECS
    ]
    for k in stale_keys:
        del request_cache[k]

    # --- process request ------------------------------------------------
    body_type = request.form.get("body_type", "plain")
    if body_type == "html":
        logger.info("Processing HTML email")

    try:
        profile_name = request.form.get("profile")
        sender = request.form.get("sender", "")
        recipients_str = request.form.get("recipients", "")
        recipients = recipients_str.split(",") if recipients_str else []

        cc_str = request.form.get("cc", "")
        cc = cc_str.split(",") if cc_str else []

        bcc_str = request.form.get("bcc", "")
        bcc = bcc_str.split(",") if bcc_str else []

        subject = request.form.get("subject", "")
        body_type = request.form.get("body_type", "plain")
        body = request.form.get("body", "")

        # Validate email addresses
        all_recipients = recipients + cc + bcc
        for email in all_recipients + [sender]:
            if email and email.strip():
                try:
                    validate_email(email.strip())
                except Exception as e:
                    return jsonify(
                        {
                            "success": False,
                            "message": f"Invalid email address: {email} - {e}",
                        }
                    )

        # Get profile configuration
        profile = config_service.get_profile(profile_name)
        if not profile:
            return jsonify(
                {"success": False, "message": f"Profile {profile_name} not found"}
            )

        # File attachments
        attachments: list[str] = []
        if "attachments" in request.files:
            files = request.files.getlist("attachments")
            for file in files:
                if file.filename:
                    temp_path = str(Path("/tmp") / file.filename)
                    file.save(temp_path)
                    attachments.append(temp_path)

        # Special attachment
        special_attachment = request.form.get("special_attachment")
        if special_attachment:
            try:
                attachment_data = json.loads(special_attachment)
                attachment_type = attachment_data.get("type")

                if attachment_type == "pdf":
                    filename, data = smtp_service.create_pdf_attachment(
                        malformed=attachment_data.get("malformed", False),
                        active_content=attachment_data.get("active_content", False),
                    )
                    temp_path = str(Path("/tmp") / filename)
                    with open(temp_path, "wb") as f:
                        f.write(data)
                    attachments.append(temp_path)

                elif attachment_type == "eicar":
                    filename, data = smtp_service.create_eicar_attachment()
                    temp_path = str(Path("/tmp") / filename)
                    with open(temp_path, "wb") as f:
                        f.write(data)
                    attachments.append(temp_path)
            except Exception as e:
                logger.exception("Failed to create special attachment: %s", e)

        # Application settings
        settings = config_service.get_settings()

        # Custom headers
        custom_headers: dict[str, str] = {}
        if request.form.get("custom_headers"):
            try:
                custom_headers_str = request.form.get("custom_headers")
                if custom_headers_str:
                    custom_headers = json.loads(custom_headers_str)
            except Exception as e:
                logger.warning("Failed to parse custom headers: %s", e)

        # Send email
        result = smtp_service.send_email(
            server=profile["server"],
            port=profile["port"],
            use_tls=profile["use_tls"],
            use_ssl=profile["use_ssl"],
            username=profile["username"],
            password=profile["password"],
            sender=sender,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            subject=subject,
            body=body,
            body_type=body_type,
            attachments=attachments,
            hostname=settings.get("send_hostname"),
            custom_headers=custom_headers,
            no_tls_verify=profile.get("no_tls_verify", False),
        )

        # Clean up temporary files
        for attachment in attachments:
            if Path(attachment).exists():
                Path(attachment).unlink(missing_ok=True)

        if result["success"]:
            log_entry: dict = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "profile": profile_name,
                "server": f"{profile['server']}:{profile['port']}",
                "sender": sender,
                "recipients": recipients,
                "cc": cc,
                "bcc": bcc,
                "subject": subject,
                "status": "Success",
                "attachments": (
                    [Path(att).name for att in attachments]
                    if attachments
                    else []
                ),
                "message_id": result.get("message_id", ""),
                "smtp_log": result.get("smtp_log", []),
            }

            if settings.get("log_message_content", False):
                log_entry["body"] = body
                log_entry["body_type"] = body_type

            config_service.add_log_entry(log_entry)

            success_result = {"success": True, "message": "Email sent"}
            request_cache[request_id] = {
                "time": current_time,
                "result": success_result,
            }
            return jsonify(success_result)
        else:
            log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "profile": profile_name,
                "server": f"{profile['server']}:{profile['port']}",
                "sender": sender,
                "recipients": recipients,
                "cc": cc,
                "bcc": bcc,
                "subject": subject,
                "status": "Failed",
                "error": result["error"],
                "attachments": (
                    [Path(att).name for att in attachments]
                    if attachments
                    else []
                ),
                "smtp_log": result.get("smtp_log", []),
            }
            config_service.add_log_entry(log_entry)

            failure_result = {
                "success": False,
                "message": f"Email failed: {result['error']}",
            }
            request_cache[request_id] = {
                "time": current_time,
                "result": failure_result,
            }
            return jsonify(failure_result)

    except Exception as e:
        logger.exception("Error sending email")

        exception_result = {"success": False, "message": f"Email failed: {e}"}
        request_cache[request_id] = {
            "time": current_time,
            "result": exception_result,
        }
        return jsonify(exception_result)


# -----------------------------------------------------------------------
# POST /test_connection
# -----------------------------------------------------------------------


@email_bp.route("/test_connection", methods=["POST"])
def test_connection():
    """API endpoint to test an SMTP connection."""
    smtp_service = current_app.extensions["smtp_service"]

    try:
        profile_name = request.form.get("profile")
        profile = config_service.get_profile(profile_name)

        if not profile:
            return jsonify(
                {"success": False, "message": f"Profile {profile_name} not found"}
            )

        settings = config_service.get_settings()

        result = smtp_service.test_connection(
            server=profile["server"],
            port=profile["port"],
            use_tls=profile["use_tls"],
            use_ssl=profile["use_ssl"],
            username=profile["username"],
            password=profile["password"],
            hostname=settings.get("send_hostname"),
            no_tls_verify=profile.get("no_tls_verify", False),
        )

        return jsonify(result)

    except Exception as e:
        logger.exception("Error testing connection")
        return jsonify({"success": False, "message": f"An error occurred: {e}"})


# -----------------------------------------------------------------------
# GET /get_test_data
# -----------------------------------------------------------------------


@email_bp.route("/get_test_data")
def get_test_data():
    """API endpoint to get test email data for special test emails."""
    smtp_service = current_app.extensions["smtp_service"]

    try:
        test_type = request.args.get("test_type")
        settings = config_service.get_settings()
        default_sender = settings.get(
            "default_sender", f"smtp@{socket.getfqdn()}"
        )

        recipient = request.args.get("recipient", default_sender)

        # Base test data
        test_data: dict = {
            "sender": default_sender,
            "recipients": [recipient],
            "cc": [],
            "bcc": [],
            "body_type": "plain",
        }

        if test_type == "pdf":
            test_data.update(
                {
                    "subject": "PDF Attachment Test",
                    "body": "This email contains a standard PDF attachment generated for testing purposes.",
                    "special_attachment": {
                        "type": "pdf",
                        "malformed": False,
                        "active_content": False,
                    },
                }
            )

        elif test_type == "pdf-malformed":
            test_data.update(
                {
                    "subject": "Malformed PDF Test",
                    "body": "This email contains a malformed PDF attachment intended for testing how systems handle invalid PDFs.",
                    "special_attachment": {
                        "type": "pdf",
                        "malformed": True,
                        "active_content": False,
                    },
                }
            )

        elif test_type == "pdf-active":
            test_data.update(
                {
                    "subject": "PDF with Active Content Test",
                    "body": "This email contains a PDF with simulated active content (JavaScript) for testing security policies.",
                    "special_attachment": {
                        "type": "pdf",
                        "malformed": False,
                        "active_content": True,
                    },
                }
            )

        elif test_type == "eicar":
            test_data.update(
                {
                    "subject": "EICAR Antivirus Test File",
                    "body": (
                        "This email contains the EICAR antivirus test file as an attachment.\n"
                        "\n"
                        "The EICAR test file is a standard test file developed by the European "
                        "Institute for Computer Antivirus Research to safely test antivirus "
                        "software without using actual malware.\n"
                        "\n"
                        "When this email is delivered, most antivirus systems should detect the "
                        "attachment as a threat, even though it's completely harmless.\n"
                        "\n"
                        "Note: Your email system or antivirus might block this email entirely."
                    ),
                    "special_attachment": {"type": "eicar"},
                }
            )

        elif test_type == "spf":
            spf_test = smtp_service.create_spf_test_email(recipient)
            test_data.update(spf_test)

        else:
            return jsonify(
                {"success": False, "message": f"Unknown test type: {test_type}"}
            )

        return jsonify({"success": True, "test_data": test_data})

    except Exception as e:
        logger.exception("Error getting test data")
        return jsonify({"success": False, "message": f"An error occurred: {e}"})
