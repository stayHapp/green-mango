"""会议助手管理员配置与嘉宾公开响应结构。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MeetingAssistantFeatureKey = Literal["agenda", "manual", "weather", "route", "contact"]


class ContactPerson(BaseModel):
    """联系会务的单条联系人记录。"""

    name: str = Field(min_length=1, max_length=50)
    role: str = Field(default="", max_length=50)
    phone: str = Field(default="", max_length=50)

    @field_validator("name", "role", "phone")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        """统一去除首尾空白，避免保存后出现空姓名。

        入参：value 为待处理的字符串，必填。
        返回值：str：去除首尾空白后的字符串。
        异常：当前函数不主动抛出异常。
        """
        return value.strip()


class MeetingAssistantFeatureUpdate(BaseModel):
    """管理员保存单项会议助手配置的请求。"""

    content: str = Field(max_length=20_000)
    unpublished_message: str = Field(min_length=1, max_length=500)
    is_published: bool
    contacts: list[ContactPerson] | None = None


class MeetingAssistantFeatureResponse(BaseModel):
    """管理员可读取完整草稿的会议助手配置响应。"""

    model_config = ConfigDict(from_attributes=True)

    meeting_id: int
    feature_key: MeetingAssistantFeatureKey
    content: str
    unpublished_message: str
    is_published: bool
    updated_at: datetime
    contacts: list[ContactPerson] = Field(default_factory=list)


class GuestMeetingAssistantFeatureResponse(BaseModel):
    """确保未发布正文为空的嘉宾会议助手响应。"""

    meeting_id: int
    feature_key: MeetingAssistantFeatureKey
    content: str | None
    unpublished_message: str
    is_published: bool
    contacts: list[ContactPerson] = Field(default_factory=list)
