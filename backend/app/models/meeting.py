"""会议与会议级配置的 ORM（对象关系映射）模型。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.access import MeetingAdmin, StaffMeeting
    from app.models.application import GuestApplication
    from app.models.guest import CheckIn, Guest, GuestField
    from app.models.registration import Registration, RegistrationField
    from app.models.user import User


class Meeting(Base):
    """教育会议、研讨、培训、论坛或专家讲座。"""

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    navigation_name: Mapped[str | None] = mapped_column(String(200))
    navigation_address: Mapped[str | None] = mapped_column(String(255))
    navigation_longitude: Mapped[float | None] = mapped_column(Float)
    navigation_latitude: Mapped[float | None] = mapped_column(Float)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    # 数据库列名沿用文档中的 created_by，Python 属性名保留更明确的 created_by_id。
    created_by_id: Mapped[int] = mapped_column("created_by", ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    created_by: Mapped[User] = relationship(back_populates="meetings")
    setting: Mapped[MeetingSetting | None] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", uselist=False
    )
    fields: Mapped[list[RegistrationField]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="RegistrationField.sort_order"
    )
    registrations: Mapped[list[Registration]] = relationship(back_populates="meeting", cascade="all, delete-orphan")
    admin_assignments: Mapped[list[MeetingAdmin]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    staff_assignments: Mapped[list[StaffMeeting]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    guest_fields: Mapped[list[GuestField]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="GuestField.sort_order"
    )
    guests: Mapped[list[Guest]] = relationship(back_populates="meeting", cascade="all, delete-orphan")
    check_ins: Mapped[list[CheckIn]] = relationship(back_populates="meeting", cascade="all, delete-orphan")
    guest_applications: Mapped[list[GuestApplication]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )
    assistant_features: Mapped[list[MeetingAssistantFeature]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )


class MeetingSetting(Base):
    """会议级配置，独立存放以便后续扩展页面配置和报名规则。"""

    __tablename__ = "meeting_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 每个会议只允许一条设置记录，保证会议规则读取路径确定。
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, nullable=False)
    registration_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    settings_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    meeting: Mapped[Meeting] = relationship(back_populates="setting")


class MeetingAssistantFeature(Base):
    """会议下固定会议助手功能的正文、提醒和发布状态。"""

    __tablename__ = "meeting_assistant_features"
    __table_args__ = (
        UniqueConstraint(
            "meeting_id", "feature_key", name="uq_meeting_assistant_features_meeting_id_feature_key"
        ),
        CheckConstraint(
            "feature_key IN ('agenda', 'manual', 'weather', 'route', 'contact')",
            name="ck_meeting_assistant_features_feature_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    feature_key: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    unpublished_message: Mapped[str] = mapped_column(String(500), nullable=False)
    is_published: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    meeting: Mapped[Meeting] = relationship(back_populates="assistant_features")
