"""增加会议首页时间显示方式。

Revision ID: 20260730_0013
Revises: 20260729_0012
Create Date: 2026-07-30 18:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0013"
down_revision: str = "20260729_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为会议表增加首页时间显示方式字段。

    入参：无。
    返回值：None：完成后每场会议可以独立选择首页时间展示精度。
    异常：新增列或约束失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meetings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "time_display_mode",
                sa.String(length=32),
                server_default="day_period",
                nullable=False,
            ),
        )
        batch_op.create_check_constraint(
            "ck_meetings_time_display_mode",
            "time_display_mode IN ('day_period', 'time')",
        )


def downgrade() -> None:
    """移除会议首页时间显示方式字段。

    入参：无。
    返回值：None：完成后会议首页恢复为前端固定展示逻辑。
    异常：删除约束或列失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meetings") as batch_op:
        batch_op.drop_constraint("ck_meetings_time_display_mode", type_="check")
        batch_op.drop_column("time_display_mode")
