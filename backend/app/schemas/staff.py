"""工作人员管理与工作人员会议列表接口结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StaffCreate(BaseModel):
    """管理员创建工作人员请求数据。"""

    username: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$", min_length=3, max_length=100)
    display_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    initial_password: str = Field(min_length=8, max_length=128)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        """拒绝只包含空白字符的工作人员姓名。

        入参：value 为待校验姓名，必填。
        返回值：str：去除首尾空白后的姓名。
        异常：姓名为空白时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("工作人员姓名不能为空白。")
        return normalized_value


class StaffResponse(BaseModel):
    """工作人员响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str | None
    phone: str | None
    is_active: bool
    created_at: datetime


class StaffMeetingResponse(BaseModel):
    """工作人员负责会议响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    location: str | None
    start_time: datetime | None
    end_time: datetime | None
    status: str
