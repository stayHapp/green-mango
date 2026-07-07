"""Alembic 迁移环境配置。

本文件把 Alembic 连接到应用的数据库配置和 SQLAlchemy metadata（元数据）。
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401  # 导入模型，确保 Base.metadata 包含业务表。

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """以离线模式运行 Alembic 迁移。

    入参：
        无。

    返回值：
        None：该函数只配置迁移上下文并执行迁移。

    异常：
        数据库 URL 缺失或迁移脚本错误时，Alembic 会抛出异常。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """以在线模式运行 Alembic 迁移。

    入参：
        无。

    返回值：
        None：该函数创建数据库连接并执行迁移。

    异常：
        数据库连接失败、迁移版本冲突或迁移脚本错误时，Alembic/SQLAlchemy 会抛出异常。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
