"""会议助手管理员配置与嘉宾公开响应结构。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MeetingAssistantFeatureKey = Literal["agenda", "manual", "weather", "route", "contact"]


class MeetingAssistantFeatureUpdate(BaseModel):
    """管理员保存单项会议助手配置的请求。"""

    content: str = Field(max_length=20_000)
    unpublished_message: str = Field(min_length=1, max_length=500)
    is_published: bool


class MeetingAssistantFeatureResponse(BaseModel):
    """管理员可读取完整草稿的会议助手配置响应。"""

    model_config = ConfigDict(from_attributes=True)

    meeting_id: int
    feature_key: MeetingAssistantFeatureKey
    content: str
    unpublished_message: str
    is_published: bool
    updated_at: datetime


class GuestMeetingAssistantFeatureResponse(BaseModel):
    """确保未发布正文为空的嘉宾会议助手响应。"""

    meeting_id: int
    feature_key: MeetingAssistantFeatureKey
    content: str | None
    unpublished_message: str
    is_published: bool
