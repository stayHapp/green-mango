"""新增嘉宾自主报名申请表。

Revision ID: 20260715_0004
Revises: 20260715_0003
Create Date: 2026-07-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260715_0004"
down_revision: str | None = "20260715_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建嘉宾报名申请表及查询索引。

    入参：无。
    返回值：None：通过 Alembic 创建表和索引。
    异常：数据库连接失败或结构冲突时由 Alembic/SQLAlchemy 抛出异常。
    """
    op.create_table(
        "guest_applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("tag", sa.String(length=100), nullable=True),
        sa.Column("seat", sa.String(length=100), nullable=True),
        sa.Column("values_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guest_applications_meeting_id", "guest_applications", ["meeting_id"], unique=False)
    op.create_index("ix_guest_applications_status", "guest_applications", ["status"], unique=False)


def downgrade() -> None:
    """删除嘉宾报名申请表及索引。

    入参：无。
    返回值：None：通过 Alembic 回滚本次结构变更。
    异常：表或索引不存在、数据库连接失败时由 Alembic/SQLAlchemy 抛出异常。
    """
    op.drop_index("ix_guest_applications_status", table_name="guest_applications")
    op.drop_index("ix_guest_applications_meeting_id", table_name="guest_applications")
    op.drop_table("guest_applications")
