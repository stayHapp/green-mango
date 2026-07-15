"""新增会议授权、嘉宾与签到数据结构。

Revision ID: 20260715_0002
Revises: 20260707_0001
Create Date: 2026-07-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260715_0002"
down_revision: str | None = "20260707_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """以向前兼容方式新增三端 MVP 所需的数据表和账号属性。

    入参：
        无。

    返回值：
        None：该函数通过 Alembic 操作数据库结构。

    异常：
        数据库连接失败、表结构与预期不一致或底层数据库不支持相关约束时，Alembic/SQLAlchemy 会抛出异常。
    """
    # 为已有用户补充三端角色、管理员手机号登录与账号启用状态，保留原始账号字段以兼容历史表。
    op.add_column("users", sa.Column("role", sa.String(length=20), server_default="admin", nullable=False))
    op.add_column("users", sa.Column("phone", sa.String(length=30), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.create_index("ix_users_phone", "users", ["phone"], unique=False)

    op.create_table(
        "meeting_admins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "user_id", name="uq_meeting_admins_meeting_id_user_id"),
    )
    op.create_table(
        "staff_meetings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "user_id", name="uq_staff_meetings_meeting_id_user_id"),
    )
    op.create_table(
        "guest_fields",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("field_type", sa.String(length=50), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("visible_to_guest", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "key", name="uq_guest_fields_meeting_id_key"),
    )
    op.create_table(
        "guests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("tag", sa.String(length=100), nullable=True),
        sa.Column("seat", sa.String(length=100), nullable=True),
        sa.Column("qr_token", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guests_meeting_id", "guests", ["meeting_id"], unique=False)
    op.create_index("ix_guests_qr_token", "guests", ["qr_token"], unique=True)
    op.create_table(
        "guest_values",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(length=100), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["guest_fields.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guest_id", "field_id", name="uq_guest_values_guest_id_field_id"),
    )
    op.create_table(
        "check_ins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("staff_id", sa.Integer(), nullable=True),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["staff_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "guest_id", name="uq_check_ins_meeting_id_guest_id"),
    )
    op.create_index("ix_check_ins_meeting_id", "check_ins", ["meeting_id"], unique=False)


def downgrade() -> None:
    """按依赖逆序删除本次新增的三端 MVP 数据结构。

    入参：
        无。

    返回值：
        None：该函数通过 Alembic 回滚本次迁移产生的数据库结构。

    异常：
        表、列或索引不存在，或者数据库连接失败时，Alembic/SQLAlchemy 会抛出异常。
    """
    op.drop_index("ix_check_ins_meeting_id", table_name="check_ins")
    op.drop_table("check_ins")
    op.drop_table("guest_values")
    op.drop_index("ix_guests_qr_token", table_name="guests")
    op.drop_index("ix_guests_meeting_id", table_name="guests")
    op.drop_table("guests")
    op.drop_table("guest_fields")
    op.drop_table("staff_meetings")
    op.drop_table("meeting_admins")
    op.drop_index("ix_users_phone", table_name="users")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_active")
        batch_op.drop_column("phone")
        batch_op.drop_column("role")
