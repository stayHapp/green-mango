"""工作人员管理与工作人员会议列表接口结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StaffCreate(BaseModel):
    """管理员创建工作人员请求数据。"""

    username: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$", min_length=3, max_length=100)
    initial_password: str = Field(min_length=8, max_length=128)


class StaffUpdate(BaseModel):
    """管理员更新工作人员资料请求数据。"""

    is_active: bool | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)


class StaffResponse(BaseModel):
    """工作人员响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
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
