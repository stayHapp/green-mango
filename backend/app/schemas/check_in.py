"""工作人员签到接口的请求与响应结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanCheckInRequest(BaseModel):
    """扫码签到请求数据。"""

    qr_token: str = Field(min_length=1, max_length=255)

    @field_validator("qr_token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        """拒绝只包含空白字符的二维码 token。

        入参：value 为待校验二维码 token，必填。
        返回值：str：去除首尾空白后的 token。
        异常：token 为空白时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("二维码 token 不能为空白。")
        return normalized_value


class ManualCheckInRequest(BaseModel):
    """人工签到请求数据。"""

    guest_id: int = Field(gt=0)


class CheckInResponse(BaseModel):
    """签到记录响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    guest_id: int
    staff_id: int | None
    method: str
    checked_in_at: datetime


class StaffGuestResponse(BaseModel):
    """工作人员核验嘉宾的搜索结果。"""

    id: int
    name: str
    phone: str
    organization: str | None
    title: str | None
    tag: str | None
    seat: str | None
    is_active: bool
    checked_in: bool
    checked_in_at: datetime | None
