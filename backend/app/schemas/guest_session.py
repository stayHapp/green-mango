"""嘉宾登录、会议和二维码接口结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GuestLoginRequest(BaseModel):
    """嘉宾按会议登录请求。"""

    meeting_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)

    @field_validator("name", "phone")
    @classmethod
    def normalize_login_text(cls, value: str) -> str:
        """标准化嘉宾登录姓名和手机号。

        入参：value 为待校验文本，必填。
        返回值：str：去除首尾空白后的文本。
        异常：文本为空白时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("姓名和手机号不能为空白。")
        return normalized_value


class GuestSessionResponse(BaseModel):
    """开发期嘉宾登录成功响应。"""

    model_config = ConfigDict(from_attributes=True)

    guest_id: int
    meeting_id: int
    name: str


class GuestMeetingResponse(BaseModel):
    """嘉宾可查看的会议响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    location: str | None
    start_time: datetime | None
    end_time: datetime | None
    status: str


class GuestQrResponse(BaseModel):
    """嘉宾个人签到二维码凭证响应。"""

    qr_token: str
    expires_at: datetime | None
