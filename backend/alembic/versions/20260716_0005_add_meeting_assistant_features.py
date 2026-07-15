"""新增会议助手功能配置表。

Revision ID: 20260716_0005
Revises: 20260715_0004
Create Date: 2026-07-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260716_0005"
down_revision: str | None = "20260715_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建会议助手配置表、固定标识检查和会议功能唯一约束。

    入参：无。
    返回值：None：成功时完成数据库结构升级。
    异常：数据库连接失败或结构冲突时由 Alembic/SQLAlchemy 抛出异常。
    """
    op.create_table(
        "meeting_assistant_features",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("feature_key", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        sa.Column("unpublished_message", sa.String(length=500), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "feature_key IN ('agenda', 'manual', 'weather', 'route', 'contact')",
            name="ck_meeting_assistant_features_feature_key",
        ),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "meeting_id", "feature_key", name="uq_meeting_assistant_features_meeting_id_feature_key"
        ),
    )


def downgrade() -> None:
    """删除会议助手配置表。

    入参：无。
    返回值：None：成功时回滚会议助手数据库结构。
    异常：表不存在或数据库连接失败时由 Alembic/SQLAlchemy 抛出异常。
    """
    op.drop_table("meeting_assistant_features")
