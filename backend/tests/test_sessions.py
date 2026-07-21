"""会话管理 API 测试。

覆盖场景：管理员/工作人员登录登出闭环、缺少 token、错误 token、
已撤销会话、停用用户无法登录等。
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


def test_admin_login_and_logout_revokes_session(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证管理员登录后登出，会话被撤销。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示管理员登录登出闭环可用。
    异常：当前函数不主动抛出业务异常；断言失败表示会话撤销逻辑异常。
    """
    client, db = client_and_session
    create_user(db, "session-admin", password="admin-pass-123")

    login_response = client.post("/api/admin/sessions", json={
        "username": "session-admin",
        "password": "admin-pass-123",
    })
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    # 登录后可访问
    assert client.get("/api/admin/meetings", headers=headers).status_code == 200

    # 登出
    assert client.post("/api/sessions/logout", headers=headers).status_code == 200

    # 登出后 token 失效
    assert client.get("/api/admin/meetings", headers=headers).status_code == 401


def test_staff_login_and_logout_revokes_session(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证工作人员登录后登出，会话被撤销。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示工作人员登录登出闭环可用。
    异常：当前函数不主动抛出业务异常；断言失败表示会话撤销逻辑异常。
    """
    client, db = client_and_session
    create_user(db, "session-staff", role="staff", password="staff-pass-123")

    login_response = client.post("/api/staff/sessions", json={
        "username": "session-staff",
        "password": "staff-pass-123",
    })
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    # 登出
    assert client.post("/api/sessions/logout", headers=headers).status_code == 200

    # 登出后 token 失效
    assert client.get("/api/staff/meetings", headers=headers).status_code == 401


def test_missing_bearer_token_returns_401(client_and_session: tuple[TestClient, Session]) -> None:
    """验证缺少 Bearer token 时返回 401。

    入参：client_and_session 为测试客户端和数据库会话夹具。
    返回值：None：断言通过表示身份校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示未认证请求未被拒绝。
    """
    client, db = client_and_session

    response = client.get("/api/admin/meetings")
    assert response.status_code == 401


def test_invalid_token_returns_401(client_and_session: tuple[TestClient, Session]) -> None:
    """验证无效 token 返回 401。

    入参：client_and_session 为测试客户端和数据库会话夹具。
    返回值：None：断言通过表示 token 校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示无效 token 可通过认证。
    """
    client, db = client_and_session

    headers = {"Authorization": "Bearer invalid-random-token-string"}
    response = client.get("/api/admin/meetings", headers=headers)
    assert response.status_code == 401


def test_wrong_scheme_returns_401(client_and_session: tuple[TestClient, Session]) -> None:
    """验证非 Bearer 认证方案返回 401。

    入参：client_and_session 为测试客户端和数据库会话夹具。
    返回值：None：断言通过表示认证方案校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示非 Bearer 方案可通过认证。
    """
    client, db = client_and_session

    headers = {"Authorization": "Basic dXNlcjpwYXNz"}
    response = client.get("/api/admin/meetings", headers=headers)
    assert response.status_code == 401


def test_disabled_admin_cannot_login(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证已停用管理员无法登录。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示停用用户登录过滤生效。
    异常：当前函数不主动抛出业务异常；断言失败表示停用用户可越权登录。
    """
    client, db = client_and_session
    create_user(db, "disabled-admin", is_active=False, password="disabled-pass")

    response = client.post("/api/admin/sessions", json={
        "username": "disabled-admin",
        "password": "disabled-pass",
    })
    assert response.status_code == 401


def test_wrong_password_returns_401(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证错误密码登录返回 401。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示密码校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示错误密码可通过认证。
    """
    client, db = client_and_session
    create_user(db, "wrong-pass-admin", password="correct-pass")

    response = client.post("/api/admin/sessions", json={
        "username": "wrong-pass-admin",
        "password": "wrong-pass",
    })
    assert response.status_code == 401


def test_admin_cannot_login_as_staff(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证管理员账号不能通过工作人员登录入口登录。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示角色隔离生效。
    异常：当前函数不主动抛出业务异常；断言失败表示角色隔离存在缺口。
    """
    client, db = client_and_session
    create_user(db, "role-admin", password="admin-pass")

    response = client.post("/api/staff/sessions", json={
        "username": "role-admin",
        "password": "admin-pass",
    })
    assert response.status_code == 401
