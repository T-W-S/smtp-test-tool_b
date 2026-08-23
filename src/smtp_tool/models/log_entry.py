from datetime import datetime

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from smtp_tool.models import db


class LogEntry(db.Model):
    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_name: Mapped[str] = mapped_column(String(255), nullable=False)
    server: Mapped[str] = mapped_column(String(255), nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    recipients: Mapped[list | dict | None] = mapped_column(JSON, nullable=False)
    cc: Mapped[list | dict | None] = mapped_column(JSON, nullable=False)
    bcc: Mapped[list | dict | None] = mapped_column(JSON, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_log: Mapped[list | dict | None] = mapped_column(JSON, nullable=False)
    attachments: Mapped[list | dict | None] = mapped_column(JSON, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
