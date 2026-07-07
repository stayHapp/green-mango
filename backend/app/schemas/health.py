"""健康检查接口的响应结构。"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """健康检查响应数据。

    属性：
        status：服务状态字符串，当前成功状态固定为 `ok`。
    """

    status: str
