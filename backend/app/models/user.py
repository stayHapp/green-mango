"""平台用户 ORM（对象关系映射）模型。

MVP 只需要最小用户表，用于记录会议创建人。认证、密码哈希生成和密码校验不在本次模型任务范围内。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.access import MeetingAdmin, StaffMeeting
    from app.models.meeting import Meeting


def utc_now() -> datetime:
    """返回带时区的 UTC 当前时间。

    入参：
        无。

    返回值：
        datetime：带 UTC 时区信息的当前时间，用作 SQLAlchemy 默认时间值。

    异常：
        当前函数不主动抛出业务异常。
    """
    return datetime.now(timezone.utc)


class User(Base):
    """管理员或工作人员账号。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    # 这里只保存密码哈希值；密码校验由后续认证模块负责。
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    # role 当前只允许由业务层写入 admin 或 staff，细粒度权限留待后续认证任务实现。
    role: Mapped[str] = mapped_column(String(20), default="admin", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    meetings: Mapped[list[Meeting]] = relationship(back_populates="created_by")
    admin_assignments: Mapped[list[MeetingAdmin]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    staff_assignments: Mapped[list[StaffMeeting]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
