from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from smtp_tool.models.profile import Profile  # noqa: E402
from smtp_tool.models.template import Template  # noqa: E402
from smtp_tool.models.log_entry import LogEntry  # noqa: E402
from smtp_tool.models.setting import Setting  # noqa: E402
from smtp_tool.models.saved_address import SavedAddress  # noqa: E402

__all__ = ["db", "Profile", "Template", "LogEntry", "Setting", "SavedAddress"]
