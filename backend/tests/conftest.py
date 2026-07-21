"""后端 API 测试共享夹具与辅助函数。

提供所有测试文件复用的基础设施：
- client_and_session：隔离数据库 + TestClient + 依赖覆盖
- create_user：创建测试用户的辅助函数（通过 _helpers fixture 暴露）
- auth_headers：生成真实 Bearer token 请求头（通过 _helpers fixture 暴露）
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  # 导入模型以注册完整 metadata（元数据）。
from app.api.dependencies import get_db
from app.core.security import hash_password
from app.db import Base
from app.main import create_app
from app.models.guest import Guest
from app.models.user import User
from app.services.sessions import create_guest_session, create_user_session


@pytest.fixture
def client_and_session(tmp_path) -> Generator[tuple[TestClient, Session], None, None]:
    """创建隔离数据库、测试客户端和请求依赖覆盖。

    入参：tmp_path 为 pytest 临时目录，用于创建隔离 SQLite 数据库。
    返回值：Generator[tuple[TestClient, Session], None, None]：测试客户端与可用于准备数据的数据库会话。
    异常：数据库建表或测试客户端初始化失败时，由 SQLAlchemy 或 FastAPI 抛出异常。
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'tests.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        """为每个测试请求提供独立数据库会话。

        入参：无。
        返回值：Generator[Session, None, None]：测试专用数据库会话。
        异常：会话创建失败时由 SQLAlchemy 抛出异常。
        """
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = session_factory()
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        db.close()
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def create_user():
    """返回创建测试用户的辅助函数。

    入参：无（返回函数）。
    返回值：callable：create_user(db, username, role, is_active, password) 辅助函数。
    异常：当前 fixture 不主动抛出异常。
    """
    def _create_user(
        db: Session,
        username: str,
        role: str = "admin",
        is_active: bool = True,
        password: str | None = None,
    ) -> User:
        """创建用于测试的用户。

        入参：db 为数据库会话；username 为唯一账号；role 为角色；is_active 表示账号是否启用。
        返回值：User：已持久化并具有主键的用户对象。
        异常：账号重复或数据库写入失败时由 SQLAlchemy 抛出异常。
        """
        user = User(
            username=username,
            password_hash=hash_password(password) if password else "test-hash",
            display_name=username,
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _create_user


@pytest.fixture
def auth_headers():
    """返回生成真实 Bearer token 请求头的辅助函数。

    入参：无（返回函数）。
    返回值：callable：auth_headers(db, subject) 辅助函数。
    异常：当前 fixture 不主动抛出异常。
    """
    def _auth_headers(db: Session, subject: User | Guest) -> dict[str, str]:
        """为测试用户或嘉宾创建真实 Bearer 会话请求头。

        入参：db 为数据库会话；subject 为管理员、工作人员或嘉宾对象，均必填。
        返回值：dict[str, str]：包含 Authorization Bearer token 的请求头。
        异常：会话写入失败时由 SQLAlchemy 抛出异常。
        """
        if isinstance(subject, Guest):
            token, _ = create_guest_session(db, subject)
        else:
            token, _ = create_user_session(db, subject)
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers
