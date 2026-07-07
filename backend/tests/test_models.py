"""MVP 核心 SQLAlchemy 模型测试。"""

import app.models  # noqa: F401  # 导入模型的副作用是把全部业务表注册到 Base.metadata。
from sqlalchemy import inspect

from app.db import Base, create_db_engine

CORE_TABLES = {
    "users",
    "meetings",
    "meeting_settings",
    "registration_fields",
    "registrations",
    "registration_values",
}


def test_core_models_are_registered_in_metadata() -> None:
    """验证核心业务表已注册到 SQLAlchemy metadata（元数据）。

    入参：
        无。

    返回值：
        None：断言通过表示 Alembic 和测试都能发现全部核心表。

    异常：
        当前函数不主动抛出业务异常；断言失败表示模型导入或 metadata 注册存在问题。
    """
    assert CORE_TABLES.issubset(Base.metadata.tables.keys())


def test_core_models_create_expected_tables_and_constraints(tmp_path) -> None:
    """验证核心模型能创建预期表和关键唯一约束。

    入参：
        tmp_path：pytest 提供的临时目录，必填；用于隔离测试数据库文件。

    返回值：
        None：断言通过表示核心表和关键唯一约束符合当前设计。

    异常：
        engine 创建失败、建表失败或数据库反射失败时，SQLAlchemy 会抛出异常。
    """
    engine = create_db_engine(f"sqlite:///{tmp_path / 'models.db'}")

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert CORE_TABLES == set(inspector.get_table_names())

    meeting_setting_constraints = {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("meeting_settings")
    }
    assert ("meeting_id",) in meeting_setting_constraints

    field_constraints = {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("registration_fields")
    }
    assert ("meeting_id", "key") in field_constraints
