"""嘉宾、嘉宾字段、嘉宾字段值和签到记录的 ORM（对象关系映射）模型。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.meeting import Meeting
    from app.models.user import User


class GuestField(Base):
    """会议级嘉宾信息字段定义。"""

    __tablename__ = "guest_fields"
    __table_args__ = (UniqueConstraint("meeting_id", "key", name="uq_guest_fields_meeting_id_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visible_to_guest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    options_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="guest_fields")
    values: Mapped[list[GuestValue]] = relationship(back_populates="field", cascade="all, delete-orphan")


class Guest(Base):
    """一个会议中由管理员录入或导入的嘉宾。"""

    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(100))
    tag: Mapped[str | None] = mapped_column(String(100))
    seat: Mapped[str | None] = mapped_column(String(100))
    # 二维码只承载随机凭证；不得将姓名、手机号等敏感信息编码到该字段。
    qr_token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="guests")
    values: Mapped[list[GuestValue]] = relationship(back_populates="guest", cascade="all, delete-orphan")
    check_in: Mapped[CheckIn | None] = relationship(back_populates="guest", cascade="all, delete-orphan", uselist=False)


class GuestValue(Base):
    """嘉宾在动态嘉宾字段中的单项值。"""

    __tablename__ = "guest_values"
    __table_args__ = (UniqueConstraint("guest_id", "field_id", name="uq_guest_values_guest_id_field_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guest_id: Mapped[int] = mapped_column(ForeignKey("guests.id", ondelete="CASCADE"), nullable=False)
    field_id: Mapped[int] = mapped_column(ForeignKey("guest_fields.id", ondelete="RESTRICT"), nullable=False)
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    guest: Mapped[Guest] = relationship(back_populates="values")
    field: Mapped[GuestField] = relationship(back_populates="values")


class CheckIn(Base):
    """嘉宾在会议中的唯一签到记录。"""

    __tablename__ = "check_ins"
    __table_args__ = (UniqueConstraint("meeting_id", "guest_id", name="uq_check_ins_meeting_id_guest_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False)
    guest_id: Mapped[int] = mapped_column(ForeignKey("guests.id", ondelete="CASCADE"), nullable=False)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="check_ins")
    guest: Mapped[Guest] = relationship(back_populates="check_in")
    staff: Mapped[User | None] = relationship()
