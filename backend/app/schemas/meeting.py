"""管理员会议管理接口的请求与响应结构。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MeetingCreate(BaseModel):
    """创建会议请求数据。"""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)
    navigation_name: str | None = Field(default=None, max_length=200)
    navigation_address: str | None = Field(default=None, max_length=255)
    navigation_longitude: float | None = Field(default=None, ge=-180, le=180)
    navigation_latitude: float | None = Field(default=None, ge=-90, le=90)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: Literal["draft", "published", "ended"] = "draft"

    @model_validator(mode="after")
    def validate_time_range(self) -> "MeetingCreate":
        """校验创建会议时的起止时间范围。

        入参：无；函数读取当前请求对象中的 start_time 与 end_time。
        返回值：MeetingCreate：时间范围合法时返回当前对象。
        异常：结束时间早于或等于开始时间时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("会议结束时间必须晚于开始时间。")
        return self


class MeetingUpdate(BaseModel):
    """修改会议请求数据；所有字段均为可选。"""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)
    navigation_name: str | None = Field(default=None, max_length=200)
    navigation_address: str | None = Field(default=None, max_length=255)
    navigation_longitude: float | None = Field(default=None, ge=-180, le=180)
    navigation_latitude: float | None = Field(default=None, ge=-90, le=90)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: Literal["draft", "published", "ended"] | None = None


class MeetingResponse(BaseModel):
    """管理员端会议详情响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    location: str | None
    navigation_name: str | None
    navigation_address: str | None
    navigation_longitude: float | None
    navigation_latitude: float | None
    start_time: datetime | None
    end_time: datetime | None
    status: str
    created_by_id: int
    created_at: datetime
    updated_at: datetime


class MeetingLocationOptionResponse(BaseModel):
    """管理员地点搜索候选项。"""

    poi_id: str
    name: str
    address: str
    district: str
    longitude: float
    latitude: float
