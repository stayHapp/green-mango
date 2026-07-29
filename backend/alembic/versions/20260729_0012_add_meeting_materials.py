"""增加多条会议资料与附件元数据

Revision ID: 20260729_0012
Revises: 20260728_0011
Create Date: 2026-07-29 10:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260729_0012"
down_revision = "20260728_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建会议资料表并回填历史会议资料正文。

    入参：无。
    返回值：None：完成后会议可以拥有多条带正文或附件的资料。
    异常：建表、创建索引或历史数据回填失败时由 Alembic/SQLAlchemy 抛出。
    """
    op.create_table(
        "meeting_materials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=150), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "length(trim(content)) > 0 OR storage_key IS NOT NULL",
            name="ck_meeting_materials_content_or_attachment",
        ),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # 外键列建立索引，避免按会议加载资料和级联删除时扫描整张资料表。
    op.create_index(
        "ix_meeting_materials_meeting_id",
        "meeting_materials",
        ["meeting_id"],
        unique=False,
    )

    # 将旧版单段会议资料正文复制为首条资料，原字段继续保留以支持安全回滚。
    op.execute(
        """
        INSERT INTO meeting_materials (
            meeting_id, title, content, sort_order, created_at, updated_at
        )
        SELECT
            meeting_id, '会议资料', content, 0, created_at, updated_at
        FROM meeting_assistant_features
        WHERE feature_key = 'manual'
          AND length(trim(content)) > 0
        """
    )


def downgrade() -> None:
    """移除会议资料表并回到单段正文结构。

    入参：无。
    返回值：None：删除会议资料记录和附件元数据表。
    异常：索引或表删除失败时由 Alembic/SQLAlchemy 抛出。
    """
    op.drop_index("ix_meeting_materials_meeting_id", table_name="meeting_materials")
    op.drop_table("meeting_materials")
