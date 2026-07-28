"""为会议服务增加访问级别字段

Revision ID: 20260728_0010
Revises: 20260721_0009
Create Date: 2026-07-28 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260728_0010"
down_revision = "20260721_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """增加会议服务访问级别并安全回填历史配置。

    入参：无。
    返回值：None：迁移完成后每项会议服务都具有 public 或 guest 访问级别。
    异常：数据库连接失败、字段或约束已存在、DDL 执行失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        # 历史内容默认保持登录可见，避免升级后意外公开。
        batch_op.add_column(
            sa.Column(
                "access_level",
                sa.String(length=32),
                nullable=False,
                server_default=sa.text("'guest'"),
            )
        )
        batch_op.create_check_constraint(
            "ck_meeting_assistant_features_access_level",
            "access_level IN ('public', 'guest')",
        )


def downgrade() -> None:
    """移除会议服务访问级别字段与检查约束。

    入参：无。
    返回值：None：回滚后恢复迁移前的数据结构。
    异常：数据库连接失败、字段或约束不存在、DDL 执行失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.drop_constraint(
            "ck_meeting_assistant_features_access_level",
            type_="check",
        )
        batch_op.drop_column("access_level")
