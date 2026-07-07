"""动态报名表字段和报名提交值的 ORM（对象关系映射）模型。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class RegistrationField(Base):
    """用于渲染会议专属报名表的动态字段定义。"""

    __tablename__ = "registration_fields"
    __table_args__ = (
        # 字段标识在同一会议内必须稳定唯一，因为报名值会保存字段标识快照。
        UniqueConstraint("meeting_id", "key", name="uq_registration_fields_meeting_id_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # MVP 阶段主要用于 select（单选）选项，后续字段类型也可复用该 JSON 结构。
    options_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    meeting: Mapped[Meeting] = relationship(back_populates="fields")
    values: Mapped[list[RegistrationValue]] = relationship(back_populates="field")


class Registration(Base):
    """某个会议的一条报名提交主记录。"""

    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    meeting: Mapped[Meeting] = relationship(back_populates="registrations")
    values: Mapped[list[RegistrationValue]] = relationship(back_populates="registration", cascade="all, delete-orphan")


class RegistrationValue(Base):
    """某条报名记录中一个动态字段的提交值。"""

    __tablename__ = "registration_values"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)
    field_id: Mapped[int] = mapped_column(ForeignKey("registration_fields.id", ondelete="RESTRICT"), nullable=False)
    # 保存提交时的字段标识，避免后续字段名称或排序变化影响历史数据可读性。
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    registration: Mapped[Registration] = relationship(back_populates="values")
    field: Mapped[RegistrationField] = relationship(back_populates="values")
