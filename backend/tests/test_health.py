"""健康检查接口测试。"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check() -> None:
    """验证健康检查接口返回可用状态。

    入参：
        无。

    返回值：
        None：断言通过表示 `/api/health` 可正常响应。

    异常：
        当前函数不主动抛出业务异常；断言失败表示健康检查接口行为变化。
    """
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
