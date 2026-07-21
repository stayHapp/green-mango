"""增加启用嘉宾会议内身份唯一索引。

Revision ID: 20260721_0008
Revises: 20260720_0007
Create Date: 2026-07-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260721_0008"
down_revision: str | None = "20260720_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """限制同一会议内姓名和手机号相同的启用嘉宾只能存在一条。

    入参：无。
    返回值：None：创建兼容 SQLite 和 PostgreSQL 的部分唯一索引。
    异常：历史数据存在重复启用身份时抛出 RuntimeError；数据库操作失败时由 Alembic/SQLAlchemy 抛出。
    """
    bind = op.get_bind()
    duplicate = bind.execute(
        sa.text(
            """
            SELECT meeting_id, name, phone, COUNT(*) AS duplicate_count
            FROM guests
            WHERE is_active = :active_value
            GROUP BY meeting_id, name, phone
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        ),
        {"active_value": True},
    ).first()
    if duplicate is not None:
        raise RuntimeError("存在姓名和手机号相同的启用嘉宾，请先合并或停用重复记录后再执行迁移。")

    dialect_name = bind.dialect.name
    index_kwargs: dict[str, object] = {}
    if dialect_name == "sqlite":
        index_kwargs["sqlite_where"] = sa.text("is_active = 1")
    elif dialect_name == "postgresql":
        index_kwargs["postgresql_where"] = sa.text("is_active")
    op.create_index(
        "uq_guests_active_meeting_name_phone",
        "guests",
        ["meeting_id", "name", "phone"],
        unique=True,
        **index_kwargs,
    )


def downgrade() -> None:
    """移除启用嘉宾身份部分唯一索引。

    入参：无。
    返回值：None：成功时恢复迁移前的嘉宾身份约束。
    异常：索引不存在或数据库操作失败时由 Alembic/SQLAlchemy 抛出。
    """
    op.drop_index("uq_guests_active_meeting_name_phone", table_name="guests")
