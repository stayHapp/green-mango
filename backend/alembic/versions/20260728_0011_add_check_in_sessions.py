"""增加会议签到场次

Revision ID: 20260728_0011
Revises: 20260728_0010
Create Date: 2026-07-28 16:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260728_0011"
down_revision = "20260728_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """增加签到场次表并迁移历史签到记录。

    入参：无。
    返回值：None：完成后每条签到记录都归属到某个签到场次。
    异常：数据库连接失败、约束调整失败或历史数据无法回填时由 Alembic/SQLAlchemy 抛出。
    """
    op.create_table(
        "check_in_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "title", name="uq_check_in_sessions_meeting_id_title"),
    )
    op.create_index("ix_check_in_sessions_meeting_id", "check_in_sessions", ["meeting_id"], unique=False)

    # 为每个历史会议创建一个默认场次，保证原有签到数据可以无损挂接。
    op.execute(
        """
        INSERT INTO check_in_sessions (
            meeting_id, title, description, is_default, sort_order, created_at, updated_at
        )
        SELECT id, '默认签到', '系统迁移生成的默认签到场次。', TRUE, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM meetings
        """
    )

    with op.batch_alter_table("check_ins") as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE check_ins
        SET session_id = (
            SELECT check_in_sessions.id
            FROM check_in_sessions
            WHERE check_in_sessions.meeting_id = check_ins.meeting_id
              AND check_in_sessions.is_default = TRUE
            ORDER BY check_in_sessions.id
            LIMIT 1
        )
        """
    )

    with op.batch_alter_table("check_ins") as batch_op:
        batch_op.drop_constraint("uq_check_ins_meeting_id_guest_id", type_="unique")
        batch_op.alter_column("session_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_check_ins_session_id_check_in_sessions",
            "check_in_sessions",
            ["session_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint("uq_check_ins_session_id_guest_id", ["session_id", "guest_id"])
        batch_op.create_index("ix_check_ins_session_id", ["session_id"], unique=False)


def downgrade() -> None:
    """移除签到场次并恢复会议级唯一签到。

    入参：无。
    返回值：None：回滚后恢复到每个会议每位嘉宾只能签到一次的结构。
    异常：如果数据库约束调整失败，由 Alembic/SQLAlchemy 抛出异常。
    """
    # 回滚到旧模型时只能保留默认场次签到记录，避免同一嘉宾多场次签到破坏旧唯一约束。
    op.execute(
        """
        DELETE FROM check_ins
        WHERE session_id NOT IN (
            SELECT id FROM check_in_sessions WHERE is_default = TRUE
        )
        """
    )
    with op.batch_alter_table("check_ins") as batch_op:
        batch_op.drop_index("ix_check_ins_session_id")
        batch_op.drop_constraint("uq_check_ins_session_id_guest_id", type_="unique")
        batch_op.drop_constraint("fk_check_ins_session_id_check_in_sessions", type_="foreignkey")
        batch_op.create_unique_constraint("uq_check_ins_meeting_id_guest_id", ["meeting_id", "guest_id"])
        batch_op.drop_column("session_id")

    op.drop_index("ix_check_in_sessions_meeting_id", table_name="check_in_sessions")
    op.drop_table("check_in_sessions")
