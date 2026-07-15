"""嘉宾自主报名申请 ORM（对象关系映射）模型。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.guest import Guest
    from app.models.meeting import Meeting
    from app.models.user import User


class GuestApplication(Base):
    """公开入口提交、由会议管理员审核的嘉宾报名申请。"""

    __tablename__ = "guest_applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(100))
    tag: Mapped[str | None] = mapped_column(String(100))
    seat: Mapped[str | None] = mapped_column(String(100))
    values_json: Mapped[dict[str, str | None]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)
    guest_id: Mapped[int | None] = mapped_column(ForeignKey("guests.id", ondelete="SET NULL"))
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="guest_applications")
    guest: Mapped[Guest | None] = relationship()
    reviewed_by: Mapped[User | None] = relationship()
