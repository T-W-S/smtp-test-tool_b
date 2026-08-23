#!/usr/bin/env python3
"""Command-line interface for the SMTP Test Tool.

Provides subcommands for sending emails, testing SMTP connections, and
managing profiles, templates, and logs.  All persistent state is stored
via :mod:`smtp_tool.services.config_service` (SQLAlchemy-backed) inside
a Flask application context created by :func:`smtp_tool.create_app`.

Entry point registered in ``pyproject.toml``::

    [project.scripts]
    smtp-tool = "smtp_tool.cli:main"
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from smtp_tool import create_app
from smtp_tool.services import config_service
from smtp_tool.services.email_validator import validate_email
from smtp_tool.services.smtp_service import DEFAULT_SMTP_PORT

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("smtp_tool_cli.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Argument parser construction
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser with all subcommands."""

    parser = argparse.ArgumentParser(
        description="SMTP Testing and Email Sending Tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # -- send ---------------------------------------------------------------
    send_parser = subparsers.add_parser("send", help="Send an email")
    send_parser.add_argument(
        "--profile", "-p", required=False, help="Profile name to use for sending"
    )
    send_parser.add_argument(
        "--server", "-s", required=False, help="SMTP server address"
    )
    send_parser.add_argument(
        "--port", "-P", type=int, default=DEFAULT_SMTP_PORT, help="SMTP server port (default: 25)"
    )
    send_parser.add_argument(
        "--tls", "-t", action="store_true", help="Use STARTTLS"
    )
    send_parser.add_argument(
        "--ssl", "-S", action="store_true", help="Use SSL/TLS"
    )
    send_parser.add_argument("--username", "-u", help="SMTP username")
    send_parser.add_argument("--password", "-w", help="SMTP password")
    send_parser.add_argument(
        "--from", "-f", dest="sender", required=True, help="Sender email address"
    )
    send_parser.add_argument(
        "--to",
        "-r",
        dest="recipients",
        required=True,
        help="Recipient email addresses (comma-separated)",
    )
    send_parser.add_argument(
        "--cc", "-c", help="CC email addresses (comma-separated)"
    )
    send_parser.add_argument(
        "--bcc", "-b", help="BCC email addresses (comma-separated)"
    )
    send_parser.add_argument("--subject", "-j", default="", help="Email subject")
    send_parser.add_argument("--body", "-m", help="Email body text")
    send_parser.add_argument(
        "--body-file", "-B", help="File containing email body"
    )
    send_parser.add_argument(
        "--html", "-H", action="store_true", help="Send as HTML email"
    )
    send_parser.add_argument(
        "--attachment",
        "-a",
        action="append",
        help="Email attachment file path (can be used multiple times)",
    )
    send_parser.add_argument(
        "--template", "-T", help="Use a saved email template"
    )

    # -- test ---------------------------------------------------------------
    test_parser = subparsers.add_parser("test", help="Test SMTP server connection")
    test_parser.add_argument(
        "--profile", "-p", required=False, help="Profile name to test"
    )
    test_parser.add_argument(
        "--server", "-s", required=False, help="SMTP server address"
    )
    test_parser.add_argument(
        "--port", "-P", type=int, default=DEFAULT_SMTP_PORT, help="SMTP server port (default: 25)"
    )
    test_parser.add_argument(
        "--tls", "-t", action="store_true", help="Use STARTTLS"
    )
    test_parser.add_argument(
        "--ssl", "-S", action="store_true", help="Use SSL/TLS"
    )
    test_parser.add_argument("--username", "-u", help="SMTP username")
    test_parser.add_argument("--password", "-w", help="SMTP password")

    # -- profile ------------------------------------------------------------
    profile_parser = subparsers.add_parser("profile", help="Manage SMTP profiles")
    profile_subparsers = profile_parser.add_subparsers(
        dest="profile_command", help="Profile command"
    )

    # profile list
    profile_subparsers.add_parser("list", help="List saved profiles")

    # profile add
    add_parser = profile_subparsers.add_parser("add", help="Add a new profile")
    add_parser.add_argument("--name", "-n", required=True, help="Profile name")
    add_parser.add_argument(
        "--server", "-s", required=True, help="SMTP server address"
    )
    add_parser.add_argument(
        "--port", "-P", type=int, default=DEFAULT_SMTP_PORT, help="SMTP server port (default: 25)"
    )
    add_parser.add_argument(
        "--tls", "-t", action="store_true", help="Use STARTTLS"
    )
    add_parser.add_argument(
        "--ssl", "-S", action="store_true", help="Use SSL/TLS"
    )
    add_parser.add_argument("--username", "-u", help="SMTP username")
    add_parser.add_argument("--password", "-w", help="SMTP password")

    # profile delete
    delete_parser = profile_subparsers.add_parser("delete", help="Delete a profile")
    delete_parser.add_argument("name", help="Profile name to delete")

    # -- template -----------------------------------------------------------
    template_parser = subparsers.add_parser(
        "template", help="Manage email templates"
    )
    template_subparsers = template_parser.add_subparsers(
        dest="template_command", help="Template command"
    )

    # template list
    template_subparsers.add_parser("list", help="List saved templates")

    # template add
    add_template_parser = template_subparsers.add_parser(
        "add", help="Add a new template"
    )
    add_template_parser.add_argument(
        "--name", "-n", required=True, help="Template name"
    )
    add_template_parser.add_argument("--subject", "-s", help="Email subject")
    add_template_parser.add_argument("--body", "-b", help="Email body text")
    add_template_parser.add_argument(
        "--body-file", "-f", help="File containing email body"
    )
    add_template_parser.add_argument(
        "--html", "-H", action="store_true", help="Mark as HTML template"
    )

    # template delete
    delete_template_parser = template_subparsers.add_parser(
        "delete", help="Delete a template"
    )
    delete_template_parser.add_argument("name", help="Template name to delete")

    # template show
    show_template_parser = template_subparsers.add_parser(
        "show", help="Show a template"
    )
    show_template_parser.add_argument("name", help="Template name to show")

    # -- logs ---------------------------------------------------------------
    logs_parser = subparsers.add_parser("logs", help="Display email sending logs")
    logs_parser.add_argument(
        "--clear", "-c", action="store_true", help="Clear logs"
    )
    logs_parser.add_argument(
        "--limit", "-l", type=int, default=20, help="Limit number of logs displayed"
    )

    return parser


# ---------------------------------------------------------------------------
# Subcommand helpers — called from within a Flask app context
# ---------------------------------------------------------------------------


def _resolve_server_args(
    args: argparse.Namespace,
) -> dict[str, Any] | None:
    """Extract SMTP server details from a profile or CLI flags.

    Returns a dict with keys ``server``, ``port``, ``use_tls``,
    ``use_ssl``, ``username``, ``password`` or ``None`` on error.
    """
    if args.profile:
        profile = config_service.get_profile(args.profile)
        if not profile:
            logger.error("Profile '%s' not found", args.profile)
            return None
        return {
            "server": profile["server"],
            "port": profile["port"],
            "use_tls": profile["use_tls"],
            "use_ssl": profile["use_ssl"],
            "username": profile["username"],
            "password": profile["password"],
        }

    if not args.server:
        logger.error("Server address is required when not using a profile")
        return None

    return {
        "server": args.server,
        "port": args.port,
        "use_tls": args.tls,
        "use_ssl": args.ssl,
        "username": args.username,
        "password": args.password,
    }


def _handle_send(args: argparse.Namespace, smtp_service: SMTPService) -> int:
    """Handle the ``send`` subcommand."""

    conn = _resolve_server_args(args)
    if conn is None:
        return 1

    # Resolve email body
    body = ""
    body_type: str = "html" if args.html else "plain"

    if args.template:
        template = config_service.get_template(args.template)
        if not template:
            logger.error("Template '%s' not found", args.template)
            return 1
        if not args.subject:
            args.subject = template.get("subject", "")
        body = template.get("body", "")
        body_type = template.get("body_type", "plain")

    if args.body:
        body = args.body

    if args.body_file:
        try:
            with open(args.body_file, "r") as fh:
                body = fh.read()
        except Exception as exc:
            logger.error("Failed to read body file: %s", exc)
            return 1

    # Parse recipients
    recipients: list[str] = args.recipients.split(",")
    cc: list[str] = args.cc.split(",") if args.cc else []
    bcc: list[str] = args.bcc.split(",") if args.bcc else []

    # Validate email addresses
    all_addresses: list[str] = recipients + cc + bcc + [args.sender]
    for email in all_addresses:
        if email.strip():
            try:
                validate_email(email.strip())
            except Exception as exc:
                logger.error("Invalid email address '%s': %s", email, exc)
                return 1

    # Send the email
    result: dict[str, Any] = smtp_service.send_email(
        server=conn["server"],
        port=conn["port"],
        use_tls=conn["use_tls"],
        use_ssl=conn["use_ssl"],
        username=conn["username"],
        password=conn["password"],
        sender=args.sender,
        recipients=recipients,
        cc=cc,
        bcc=bcc,
        subject=args.subject,
        body=body,
        body_type=body_type,
        attachments=args.attachment,
    )

    log_entry: dict[str, Any] = {
        "timestamp": None,  # filled by config_service
        "profile": args.profile if args.profile else "CLI",
        "server": conn["server"],
        "sender": args.sender,
        "recipients": recipients,
        "cc": cc,
        "bcc": bcc,
        "subject": args.subject,
    }

    if result["success"]:
        logger.info("Email sent successfully")
        log_entry["status"] = "Success"
        config_service.add_log_entry(log_entry)
        return 0

    error_msg: str = str(result.get("error", "Unknown error"))
    logger.error("Failed to send email: %s", error_msg)
    log_entry["status"] = "Failed"
    log_entry["error"] = error_msg
    config_service.add_log_entry(log_entry)
    return 1


def _handle_test(args: argparse.Namespace, smtp_service: SMTPService) -> int:
    """Handle the ``test`` subcommand."""

    conn = _resolve_server_args(args)
    if conn is None:
        return 1

    result: dict[str, Any] = smtp_service.test_connection(
        server=conn["server"],
        port=conn["port"],
        use_tls=conn["use_tls"],
        use_ssl=conn["use_ssl"],
        username=conn["username"],
        password=conn["password"],
    )

    if result["success"]:
        logger.info(
            "Successfully connected to SMTP server %s:%s",
            conn["server"],
            conn["port"],
        )
        if "capabilities" in result:
            logger.info("Server capabilities:")
            for capability in result["capabilities"]:
                logger.info("- %s", capability)
        return 0

    logger.error(
        "Failed to connect to SMTP server: %s",
        result.get("error", "Unknown error"),
    )
    return 1


def _handle_profile(
    args: argparse.Namespace,
    profile_parser: argparse.ArgumentParser,
) -> int:
    """Handle the ``profile`` subcommand (list / add / delete)."""

    if not args.profile_command:
        profile_parser.print_help()
        return 1

    if args.profile_command == "list":
        profiles: dict[str, dict[str, Any]] = config_service.get_profiles()
        if not profiles:
            logger.info("No profiles found")
        else:
            logger.info("Saved profiles:")
            for name, profile in profiles.items():
                logger.info("- %s:", name)
                logger.info("  Server: %s:%s", profile["server"], profile["port"])
                if profile["use_ssl"]:
                    security = "SSL/TLS"
                elif profile["use_tls"]:
                    security = "STARTTLS"
                else:
                    security = "None"
                logger.info("  Security: %s", security)
                logger.info(
                    "  Authentication: %s",
                    "Yes" if profile["username"] else "No",
                )
        return 0

    if args.profile_command == "add":
        profile_data: dict[str, Any] = {
            "name": args.name,
            "server": args.server,
            "port": args.port,
            "use_tls": args.tls,
            "use_ssl": args.ssl,
            "username": args.username,
            "password": args.password,
        }
        config_service.add_profile(profile_data)
        logger.info("Profile '%s' added successfully", args.name)
        return 0

    if args.profile_command == "delete":
        if config_service.delete_profile(args.name):
            logger.info("Profile '%s' deleted successfully", args.name)
            return 0
        logger.error("Profile '%s' not found", args.name)
        return 1

    return 0


def _handle_template(
    args: argparse.Namespace,
    template_parser: argparse.ArgumentParser,
) -> int:
    """Handle the ``template`` subcommand (list / add / delete / show)."""

    if not args.template_command:
        template_parser.print_help()
        return 1

    if args.template_command == "list":
        templates: dict[str, dict[str, Any]] = config_service.get_templates()
        if not templates:
            logger.info("No templates found")
        else:
            logger.info("Saved templates:")
            for name, template in templates.items():
                logger.info("- %s:", name)
                logger.info("  Subject: %s", template.get("subject", "N/A"))
                tpl_type = (
                    "HTML"
                    if template.get("body_type") == "html"
                    else "Plain Text"
                )
                logger.info("  Type: %s", tpl_type)
        return 0

    if args.template_command == "add":
        body = ""
        if args.body:
            body = args.body

        if args.body_file:
            try:
                with open(args.body_file, "r") as fh:
                    body = fh.read()
            except Exception as exc:
                logger.error("Failed to read body file: %s", exc)
                return 1

        template_data: dict[str, Any] = {
            "name": args.name,
            "subject": args.subject or "",
            "body_type": "html" if args.html else "plain",
            "body": body,
        }
        config_service.add_template(template_data)
        logger.info("Template '%s' added successfully", args.name)
        return 0

    if args.template_command == "delete":
        if config_service.delete_template(args.name):
            logger.info("Template '%s' deleted successfully", args.name)
            return 0
        logger.error("Template '%s' not found", args.name)
        return 1

    if args.template_command == "show":
        template = config_service.get_template(args.name)
        if template:
            logger.info("Template: %s", args.name)
            logger.info("Subject: %s", template.get("subject", "N/A"))
            tpl_type = (
                "HTML"
                if template.get("body_type") == "html"
                else "Plain Text"
            )
            logger.info("Type: %s", tpl_type)
            logger.info("Body:")
            logger.info(template.get("body", ""))
            return 0
        logger.error("Template '%s' not found", args.name)
        return 1

    return 0


def _handle_logs(args: argparse.Namespace) -> int:
    """Handle the ``logs`` subcommand (display / clear)."""

    if args.clear:
        config_service.clear_logs()
        logger.info("Logs cleared successfully")
        return 0

    logs: list[dict[str, Any]] = config_service.get_logs()
    if not logs:
        logger.info("No logs found")
    else:
        logs = logs[-args.limit:] if len(logs) > args.limit else logs
        logger.info("Recent %d log entries:", len(logs))
        for log in logs:
            status_str: str = log.get("status", "Unknown")
            if status_str == "Success":
                status_display = "SUCCESS"
            else:
                status_display = f"FAILED: {log.get('error', 'Unknown error')}"

            logger.info(
                "[%s] %s - %s - %s",
                log.get("timestamp", "Unknown"),
                log.get("profile", "N/A"),
                log.get("subject", "N/A"),
                status_display,
            )
    return 0


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point.  Returns an exit code (0 = success)."""

    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create the Flask application for its app context (needed by
    # config_service which relies on SQLAlchemy / Flask-SQLAlchemy).
    app = create_app()

    with app.app_context():
        smtp_service = app.extensions["smtp_service"]
        if args.command == "send":
            return _handle_send(args, smtp_service)

        if args.command == "test":
            return _handle_test(args, smtp_service)

        if args.command == "profile":
            # Retrieve the profile sub-parser so we can print its help
            # when no profile_command is given.
            profile_parser = parser._subparsers._group_actions[0].choices["profile"]  # type: ignore[union-attr]
            return _handle_profile(args, profile_parser)

        if args.command == "template":
            template_parser = parser._subparsers._group_actions[0].choices["template"]  # type: ignore[union-attr]
            return _handle_template(args, template_parser)

        if args.command == "logs":
            return _handle_logs(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
