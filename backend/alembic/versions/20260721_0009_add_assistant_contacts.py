"""为会议助手功能增加联系人字段

Revision ID: 20260721_0009_add_assistant_contacts
Revises: 20260721_0008_add_active_guest_identity_index
Create Date: 2026-07-21 22:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260721_0009_add_assistant_contacts"
down_revision = "20260721_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """为 meeting_assistant_features 增加 contacts JSON 字段。"""
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.add_column(
            sa.Column("contacts", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )


def downgrade() -> None:
    """回滚 contacts 字段。"""
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.drop_column("contacts")
