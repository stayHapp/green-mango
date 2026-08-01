"""工作人员签到接口的请求与响应结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    session_id: int
    session_title: str
    guest_id: int
    staff_id: int | None
    method: str
    checked_in_at: datetime


class StaffCheckInSessionResponse(BaseModel):
    """工作人员端当前签到场次响应数据。"""

    id: int
    title: str
    starts_at: datetime | None
    ends_at: datetime | None
    is_default: bool


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
    companion_count: int
    is_companion: bool
    companion_of_name: str | None
    visible_fields: list[str]


class CompanionCreate(BaseModel):
    """工作人员登记同行人员的请求数据。"""

    companion_of_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    organization: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=100)
    tag: str | None = Field(default=None, max_length=100)
    seat: str | None = Field(default=None, max_length=100)
    companion_note: str | None = Field(default=None, max_length=255)
    values: dict[str, str | None] = Field(default_factory=dict)

    @field_validator("name", "phone")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """拒绝只包含空白字符的姓名和手机号。

        入参：value 为待校验的姓名或手机号文本，必填。
        返回值：str：去除首尾空白后的文本。
        异常：字段为空白时抛出 ValueError，并由 Pydantic 转换为请求校验错误。
        """
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("姓名和手机号不能为空白。")
        return normalized_value

    @model_validator(mode="after")
    def validate_companion_note(self) -> "CompanionCreate":
        """将空备注规范化为 None，避免保存无意义空白。

        入参：无；函数读取当前请求对象中的 companion_note。
        返回值：CompanionCreate：备注规范后的请求对象。
        异常：当前校验器不主动抛出业务异常。
        """
        if self.companion_note is not None and not self.companion_note.strip():
            self.companion_note = None
        return self


class CompanionResponse(BaseModel):
    """工作人员端同行人员响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    name: str
    phone: str
    organization: str | None
    title: str | None
    tag: str | None
    seat: str | None
    companion_note: str | None
    companion_of_id: int
    companion_of_name: str | None
    is_active: bool
    created_at: datetime


class AlreadyCheckedInDetail(BaseModel):
    """重复签到时返回给工作人员端的结构化提示。"""

    code: str
    message: str
    guest_id: int
    guest_name: str
    phone: str
    checked_in_at: datetime
    method: str
    staff_id: int | None
    staff_name: str | None
