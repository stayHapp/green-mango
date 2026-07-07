"""数据库 engine（连接引擎）辅助函数测试。"""

import app.models  # noqa: F401  # 注册业务模型，确保本测试模块能读取完整 Base.metadata。
from sqlalchemy import inspect

from app.db import Base, create_db_engine


def test_sqlite_engine_can_create_metadata(tmp_path) -> None:
    """验证临时 SQLite 数据库可以创建项目 metadata（元数据）。

    入参：
        tmp_path：pytest 提供的临时目录，必填；用于隔离测试数据库文件。

    返回值：
        None：断言通过表示数据库基础设施可创建核心表。

    异常：
        engine 创建失败或建表失败时，SQLAlchemy 会抛出异常。
    """
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_db_engine(database_url)

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()
