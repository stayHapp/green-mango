"""管理员、工作人员统一账号登录与退出接口结构。"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserLoginRequest(BaseModel):
    """管理员或工作人员账号密码登录请求。"""

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class SessionResponse(BaseModel):
    """三端登录成功的访问会话响应。"""

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    subject_id: int
    subject_type: str


class LogoutResponse(BaseModel):
    """退出登录响应。"""

    success: bool
