"""管理员签到统计与明细接口结构。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CheckInMode = Literal["single", "date", "custom"]


class AdminCheckInSessionBase(BaseModel):
    """管理员维护签到场次的基础字段。"""

    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_default: bool = False

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        """拒绝空白签到场次名称。

        入参：value 为待校验的场次名称，必填。
        返回值：str：去除首尾空白后的场次名称。
        异常：名称为空白时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("签到场次名称不能为空。")
        return normalized_value


class AdminCheckInSessionCreate(AdminCheckInSessionBase):
    """管理员创建签到场次的请求结构。"""


class AdminCheckInSessionUpdate(BaseModel):
    """管理员更新签到场次的请求结构。"""

    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_default: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_optional_title(cls, value: str | None) -> str | None:
        """拒绝空白的可选签到场次名称。

        入参：value 为待校验的可选场次名称。
        返回值：str | None：空值原样返回，非空值去除首尾空白。
        异常：名称为空白时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        if value is None:
            return None
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("签到场次名称不能为空。")
        return normalized_value


class AdminCheckInSessionResponse(BaseModel):
    """管理员查看的签到场次响应结构。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    title: str
    description: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    is_default: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AdminCheckInSettingsUpdate(BaseModel):
    """管理员更新签到规则的请求结构。"""

    mode: CheckInMode
    manual_default_session_id: int | None = None


class AdminCheckInSettingsResponse(BaseModel):
    """管理员查看的会议级签到规则响应结构。"""

    mode: CheckInMode
    manual_default_session_id: int | None
    effective_session_id: int | None
    effective_session_title: str | None


class AdminCheckInComparisonItem(BaseModel):
    """签到场次差异中的单个嘉宾。"""

    guest_id: int
    guest_name: str
    phone: str
    checked_in_at: datetime
    method: str
    staff_name: str | None


class AdminCheckInComparison(BaseModel):
    """当前签到场次相对前一场次的签到差异。"""

    previous_session_id: int | None
    previous_session_title: str | None
    added_guests: list[AdminCheckInComparisonItem]
    removed_guests: list[AdminCheckInComparisonItem]


class AdminCheckInItem(BaseModel):
    """管理员查看的单条签到明细。"""

    session_id: int
    session_title: str
    guest_id: int
    guest_name: str
    phone: str
    checked_in_at: datetime
    method: str
    staff_name: str | None


class AdminCheckInSummary(BaseModel):
    """会议签到统计与明细响应。"""

    session_id: int
    session_title: str
    total_guests: int
    checked_in_count: int
    unchecked_count: int
    records: list[AdminCheckInItem]
    comparison: AdminCheckInComparison | None
