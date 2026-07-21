"""补充嘉宾来源与字段启用状态。

Revision ID: 20260720_0007
Revises: 20260716_0006
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260720_0007"
down_revision: str | None = "20260716_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为嘉宾增加来源，并让动态字段可独立启用或停用。

    入参：无。
    返回值：None：历史嘉宾默认标记为管理员录入，历史字段默认保持启用。
    异常：数据库连接失败或字段冲突时由 Alembic/SQLAlchemy 抛出。
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    guest_columns = {column["name"] for column in inspector.get_columns("guests")}
    guest_field_columns = {column["name"] for column in inspector.get_columns("guest_fields")}
    if "source" not in guest_columns:
        op.add_column(
            "guests",
            sa.Column("source", sa.String(length=32), nullable=False, server_default="admin_entry"),
        )
    if "is_enabled" not in guest_field_columns:
        op.add_column(
            "guest_fields",
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    # SQLite 不支持 ALTER COLUMN DROP DEFAULT；其默认值保留不影响 ORM 运行。
    if bind.dialect.name != "sqlite":
        op.alter_column("guests", "source", server_default=None)
        op.alter_column("guest_fields", "is_enabled", server_default=None)


def downgrade() -> None:
    """回退嘉宾来源和字段启用状态字段。

    入参：无。
    返回值：None：成功时移除本迁移新增的两个字段。
    异常：数据库连接失败或字段不存在时由 Alembic/SQLAlchemy 抛出。
    """
    op.drop_column("guest_fields", "is_enabled")
    op.drop_column("guests", "source")
