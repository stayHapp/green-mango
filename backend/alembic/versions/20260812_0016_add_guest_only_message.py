"""会议助手新增仅嘉宾可见提示字段。

Revision ID: 20260812_0016
Revises: 20260731_0015
Create Date: 2026-08-12 10:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260812_0016"
down_revision: str = "20260731_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFAULT_GUEST_ONLY_MESSAGE = "此项服务仅对已登录参会人员开放"


def upgrade() -> None:
    """为会议助手配置增加仅嘉宾可见提示字段并回填默认文案。

    入参：无。
    返回值：None：迁移完成后每项会议服务都有可编辑的未登录提示。
    异常：新增列或默认值失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.add_column(
            sa.Column(
                "guest_only_message",
                sa.String(length=500),
                server_default=_DEFAULT_GUEST_ONLY_MESSAGE,
                nullable=False,
            )
        )


def downgrade() -> None:
    """移除会议助手的仅嘉宾可见提示字段。

    入参：无。
    返回值：None：迁移回退后不再保存未登录提示，嘉宾端使用前端默认文案。
    异常：删除列失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.drop_column("guest_only_message")
