"""增加联系会务二维码配置。

Revision ID: 20260731_0014
Revises: 20260730_0013
Create Date: 2026-07-31 10:55:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0014"
down_revision: str = "20260730_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为会议服务表增加联系会务二维码标题和图片元数据字段。

    入参：无。
    返回值：None：迁移完成后联系会务可配置二维码图片和图片上方文字。
    异常：新增列失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.add_column(
            sa.Column(
                "contact_qr_title",
                sa.String(length=100),
                server_default="会务二维码",
                nullable=False,
            ),
        )
        batch_op.add_column(sa.Column("contact_qr_original_filename", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("contact_qr_storage_key", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("contact_qr_content_type", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("contact_qr_size_bytes", sa.Integer(), nullable=True))


def downgrade() -> None:
    """移除联系会务二维码配置字段。

    入参：无。
    返回值：None：迁移回退后联系会务不再保存二维码图片配置。
    异常：删除列失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("meeting_assistant_features") as batch_op:
        batch_op.drop_column("contact_qr_size_bytes")
        batch_op.drop_column("contact_qr_content_type")
        batch_op.drop_column("contact_qr_storage_key")
        batch_op.drop_column("contact_qr_original_filename")
        batch_op.drop_column("contact_qr_title")
