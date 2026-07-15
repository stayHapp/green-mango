"""嘉宾自主报名和管理员审核接口结构。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GuestApplicationCreate(BaseModel):
    """嘉宾公开提交报名申请的请求数据。"""

    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    organization: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=100)
    tag: str | None = Field(default=None, max_length=100)
    values: dict[str, str | None] = Field(default_factory=dict)

    @field_validator("name", "phone")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """清理并校验报名姓名和手机号。

        入参：value 为姓名或手机号文本，必填且不能只含空白。
        返回值：str：去除首尾空白的文本。
        异常：内容为空白时抛出 ValueError，由 Pydantic 转换为 422 响应。
        """
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("姓名和手机号不能为空白。")
        return normalized_value


class GuestApplicationReviewRequest(BaseModel):
    """管理员审核报名申请的请求数据。"""

    status: Literal["approved", "rejected"]


class GuestApplicationResponse(BaseModel):
    """报名申请详情响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    name: str
    phone: str
    organization: str | None
    title: str | None
    tag: str | None
    seat: str | None
    values_json: dict[str, str | None]
    status: str
    guest_id: int | None
    reviewed_by_id: int | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
