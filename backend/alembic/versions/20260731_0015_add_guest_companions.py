"""增加嘉宾同行人员关联字段。

Revision ID: 20260731_0015
Revises: 20260731_0014
Create Date: 2026-07-31 18:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0015"
down_revision: str = "20260731_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为嘉宾表增加同行人员关联字段。

    入参：无。
    返回值：None：迁移完成后嘉宾可绑定所陪同的主嘉宾并保存自由文本备注。
    异常：新增列、外键或索引失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("guests") as batch_op:
        batch_op.add_column(sa.Column("companion_of_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("companion_note", sa.String(length=255), nullable=True))
        batch_op.create_foreign_key(
            "fk_guests_companion_of_id",
            "guests",
            ["companion_of_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_guests_companion_of_id", ["companion_of_id"])


def downgrade() -> None:
    """移除嘉宾同行人员关联字段。

    入参：无。
    返回值：None：迁移回退后嘉宾不再保存同行绑定与备注。
    异常：删除索引、外键或列失败时由 Alembic/SQLAlchemy 抛出。
    """
    with op.batch_alter_table("guests") as batch_op:
        batch_op.drop_index("ix_guests_companion_of_id")
        batch_op.drop_constraint("fk_guests_companion_of_id", type_="foreignkey")
        batch_op.drop_column("companion_note")
        batch_op.drop_column("companion_of_id")
