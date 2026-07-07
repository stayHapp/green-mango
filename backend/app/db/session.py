"""数据库连接、会话工厂和 FastAPI 依赖。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _connect_args(database_url: str) -> dict[str, object]:
    """根据数据库连接地址生成 SQLAlchemy 连接参数。

    入参：
        database_url：数据库连接地址，必填；当前用于判断是否为 SQLite。

    返回值：
        dict[str, object]：传给 SQLAlchemy engine 的连接参数。

    异常：
        当前函数不主动抛出业务异常。
    """
    if database_url.startswith("sqlite"):
        # SQLite 在 FastAPI 测试和本地开发中可能跨线程访问，需要关闭同线程限制。
        return {"check_same_thread": False}
    return {}


def create_db_engine(database_url: str | None = None) -> Engine:
    """创建 SQLAlchemy engine（数据库连接引擎）。

    入参：
        database_url：可选数据库连接地址；为空时使用全局配置中的 `settings.database_url`。

    返回值：
        Engine：SQLAlchemy 数据库连接引擎。

    异常：
        数据库地址格式非法或底层驱动不可用时，SQLAlchemy 会在创建或使用连接时抛出异常。
    """
    url = database_url or settings.database_url
    return create_engine(url, connect_args=_connect_args(url), pool_pre_ping=True)


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """为 FastAPI 请求提供数据库会话。

    入参：
        无。

    返回值：
        Generator[Session, None, None]：生成一个 SQLAlchemy Session，并在请求结束后关闭。

    异常：
        会话创建或数据库操作失败时，异常由 SQLAlchemy 或调用方继续处理。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
