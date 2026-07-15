"""管理员嘉宾字段配置和嘉宾管理接口的请求与响应结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GuestFieldInput(BaseModel):
    """单个嘉宾字段配置输入。"""

    label: str = Field(min_length=1, max_length=100)
    key: str = Field(pattern=r"^[a-z][a-z0-9_]*$", max_length=100)
    field_type: str = Field(min_length=1, max_length=50)
    required: bool = False
    visible_to_guest: bool = True
    sort_order: int = Field(default=0, ge=0)
    options_json: list[dict[str, object]] = Field(default_factory=list)


class GuestFieldReplaceRequest(BaseModel):
    """全量替换一个会议嘉宾字段配置的请求数据。"""

    fields: list[GuestFieldInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_field_keys(self) -> "GuestFieldReplaceRequest":
        """校验同一会议提交的嘉宾字段 key 不重复。

        入参：无；函数读取当前请求对象中的 fields。
        返回值：GuestFieldReplaceRequest：字段 key 无重复时返回当前对象。
        异常：发现重复 key 时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        keys = [field.key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("同一会议的嘉宾字段 key 不能重复。")
        return self


class GuestFieldResponse(GuestFieldInput):
    """嘉宾字段配置响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    created_at: datetime
    updated_at: datetime


class GuestCreate(BaseModel):
    """管理员录入单个嘉宾的请求数据。"""

    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    organization: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=100)
    tag: str | None = Field(default=None, max_length=100)
    seat: str | None = Field(default=None, max_length=100)

    @field_validator("name", "phone")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """拒绝只包含空白字符的姓名和手机号。

        入参：value 为待校验的字段文本，必填。
        返回值：str：去除首尾空白后的文本。
        异常：字段为空白时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("姓名和手机号不能为空白。")
        return normalized_value


class GuestResponse(BaseModel):
    """管理员端嘉宾响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    name: str
    phone: str
    organization: str | None
    title: str | None
    tag: str | None
    seat: str | None
    qr_token: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
