"""会议管理员与工作人员授权关系的 ORM（对象关系映射）模型。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.meeting import Meeting
    from app.models.user import User


class MeetingAdmin(Base):
    """会议与管理员之间的多对多授权关系。"""

    __tablename__ = "meeting_admins"
    __table_args__ = (UniqueConstraint("meeting_id", "user_id", name="uq_meeting_admins_meeting_id_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="admin_assignments")
    user: Mapped[User] = relationship(back_populates="admin_assignments")


class StaffMeeting(Base):
    """会议与工作人员之间的多对多授权关系。"""

    __tablename__ = "staff_meetings"
    __table_args__ = (UniqueConstraint("meeting_id", "user_id", name="uq_staff_meetings_meeting_id_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="staff_assignments")
    user: Mapped[User] = relationship(back_populates="staff_assignments")
