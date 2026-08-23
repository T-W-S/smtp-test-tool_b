"""SMTP Test Tool application factory.

Provides :func:`create_app` which configures Flask, initialises extensions,
registers all blueprints and sets up logging.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify

from smtp_tool.models import db


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application.

    Parameters
    ----------
    test_config:
        Optional mapping of config overrides.  When provided, its values
        take precedence over defaults and environment variables.
    """
    # Resolve paths -------------------------------------------------------
    config_dir = os.environ.get(
        "SMTP_CONFIG_DIR",
        os.path.join(os.path.expanduser("~"), ".smtp_tool"),
    )
    os.makedirs(config_dir, exist_ok=True)

    db_uri = f"sqlite:///{os.path.join(config_dir, 'smtp_tool.db')}"

    # Create Flask app ----------------------------------------------------
    # Use the *project-root* ``templates/`` folder that ships with the
    # original monolithic app.  ``static/`` lives under the package.
    root_dir = Path(__file__).resolve().parent.parent.parent  # repo root
    app = Flask(
        __name__,
        template_folder=str(root_dir / "templates"),
        static_folder=str(Path(__file__).resolve().parent / "static"),
    )

    # Core config ---------------------------------------------------------
    app.config["SECRET_KEY"] = os.environ.get(
        "SESSION_SECRET", "default-secret-key-for-development"
    )
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Allow test_config to override anything, including the DB URI --------
    if test_config is not None:
        app.config.update(test_config)

    # Logging -------------------------------------------------------------
    _configure_logging(app)

    # Database ------------------------------------------------------------
    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Migrate legacy JSON files (idempotent) --------------------------
        from smtp_tool.services import config_service

        config_service.migrate_from_json(config_dir)

        # Seed default templates if the table is empty --------------------
        config_service.init_default_templates()

    # Request cache for duplicate prevention (shared mutable dict) --------
    app.extensions["request_cache"] = {}

    # SMTP service singleton ----------------------------------------------
    from smtp_tool.services.smtp_service import SMTPService

    app.extensions["smtp_service"] = SMTPService()

    # Register blueprints (no URL prefix -- routes stay at current paths) -
    # Blueprint modules may not exist yet during incremental migration;
    # import errors are logged and silently skipped so that the CLI and
    # other non-web entry points can still use the app context.
    _blueprint_imports: list[tuple[str, str]] = [
        ("smtp_tool.blueprints.email", "email_bp"),
        ("smtp_tool.blueprints.profiles", "profiles_bp"),
        ("smtp_tool.blueprints.templates_bp", "templates_bp"),
        ("smtp_tool.blueprints.settings", "settings_bp"),
        ("smtp_tool.blueprints.logs", "logs_bp"),
        ("smtp_tool.blueprints.addresses", "addresses_bp"),
    ]

    import importlib as _importlib

    for _module_path, _attr_name in _blueprint_imports:
        try:
            _mod = _importlib.import_module(_module_path)
            _bp = getattr(_mod, _attr_name)
            app.register_blueprint(_bp)
        except (ImportError, AttributeError) as _exc:
            logging.getLogger(__name__).debug(
                "Skipping blueprint %s.%s: %s", _module_path, _attr_name, _exc
            )

    # Health-check route (registered directly on app) ---------------------
    @app.route("/health_check")
    def health_check() -> tuple:
        """Simple health check endpoint for Docker and monitoring."""
        # Verify DB connectivity
        db_ok = True
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            db_ok = False

        status = "ok" if db_ok else "degraded"
        payload = {
            "status": status,
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
        }
        code = 200 if db_ok else 503
        return jsonify(payload), code

    return app


# -----------------------------------------------------------------------
# Logging helper
# -----------------------------------------------------------------------


def _configure_logging(app: Flask) -> None:
    """Set up rotating file + stream handlers."""
    log_dir = os.environ.get("SMTP_LOG_DIR", ".")
    os.makedirs(log_dir, exist_ok=True)

    log_level_name = os.environ.get("LOG_LEVEL", "DEBUG").upper()
    log_level = getattr(logging, log_level_name, logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "smtp_tool.log"),
        maxBytes=10_485_760,  # 10 MB
        backupCount=5,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    # Configure the root logger so all modules pick it up
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Avoid duplicate handlers when create_app is called more than once
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)
