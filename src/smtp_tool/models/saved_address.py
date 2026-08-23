from datetime import UTC, datetime

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from smtp_tool.models import db


class SavedAddress(db.Model):
    __tablename__ = "saved_addresses"
    __table_args__ = (UniqueConstraint("email", "address_type", name="uq_email_address_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    address_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
