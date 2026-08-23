from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from smtp_tool.models import db


class Setting(db.Model):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[list | dict | str | int | float | bool | None] = mapped_column(JSON, nullable=True)
