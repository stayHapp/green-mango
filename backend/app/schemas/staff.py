"""工作人员管理与工作人员会议列表接口结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StaffCreate(BaseModel):
    """管理员创建工作人员请求数据。"""

    username: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$", min_length=3, max_length=100)
    initial_password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        """将显示名首尾空白去除，空白文本规范化为 None。

        入参：value 为待校验的显示名，可为空。
        返回值：str | None：去除首尾空白后的显示名；空白文本返回 None。
        异常：当前校验器不主动抛出业务异常。
        """
        if value is None:
            return None
        normalized_value = value.strip()
        return normalized_value or None


class StaffUpdate(BaseModel):
    """管理员更新工作人员资料请求数据。"""

    is_active: bool | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        """将显示名首尾空白去除，空白文本规范化为 None。

        入参：value 为待校验的显示名，可为空。
        返回值：str | None：去除首尾空白后的显示名；空白文本返回 None。
        异常：当前校验器不主动抛出业务异常。
        """
        if value is None:
            return None
        normalized_value = value.strip()
        return normalized_value or None


class StaffResponse(BaseModel):
    """工作人员响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str | None
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
