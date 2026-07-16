"""新增会议导航点位字段。

Revision ID: 20260716_0006
Revises: 20260716_0005
Create Date: 2026-07-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260716_0006"
down_revision: str | None = "20260716_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """为会议表增加导航名称、地址和高德坐标。

    入参：无。
    返回值：None：成功时增加四个可空字段，历史会议保持兼容。
    异常：数据库连接失败或字段冲突时由 Alembic/SQLAlchemy 抛出。
    """
    op.add_column("meetings", sa.Column("navigation_name", sa.String(length=200), nullable=True))
    op.add_column("meetings", sa.Column("navigation_address", sa.String(length=255), nullable=True))
    op.add_column("meetings", sa.Column("navigation_longitude", sa.Float(), nullable=True))
    op.add_column("meetings", sa.Column("navigation_latitude", sa.Float(), nullable=True))


def downgrade() -> None:
    """从会议表删除导航点位字段。

    入参：无。
    返回值：None：成功时恢复到上一版会议结构。
    异常：数据库连接失败或字段不存在时由 Alembic/SQLAlchemy 抛出。
    """
    op.drop_column("meetings", "navigation_latitude")
    op.drop_column("meetings", "navigation_longitude")
    op.drop_column("meetings", "navigation_address")
    op.drop_column("meetings", "navigation_name")
