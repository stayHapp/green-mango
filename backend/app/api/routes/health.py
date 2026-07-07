"""健康检查路由。"""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """返回后端服务健康状态。

    入参：
        无。

    返回值：
        HealthResponse：包含 `status` 字段；`ok` 表示服务进程可正常响应。

    异常：
        当前函数不主动抛出业务异常。
    """
    return HealthResponse(status="ok")
