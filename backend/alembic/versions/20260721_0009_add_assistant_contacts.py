"""为会议助手功能增加联系人字段

Revision ID: 20260721_0009
Revises: 20260721_0008_add_active_guest_identity_index
Create Date: 2026-07-21 22:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260721_0009"
down_revision = "20260721_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """为会议助手功能配置表增加联系人 JSON 字段。

    入参：无。
    返回值：None：迁移成功后 `meeting_assistant_features.contacts` 保存联系人列表 JSON 数据。
    异常：数据库连接失败、字段已存在或 DDL 执行失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.add_column(
            sa.Column("contacts", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )


def downgrade() -> None:
    """移除会议助手功能配置表中的联系人 JSON 字段。

    入参：无。
    返回值：None：回滚成功后 `meeting_assistant_features.contacts` 字段被删除。
    异常：数据库连接失败、字段不存在或 DDL 执行失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.drop_column("contacts")
