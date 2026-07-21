"""会议管理员、工作人员维护和通用操作响应结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AdminAssignmentRequest(BaseModel):
    """按账号添加会议管理员的请求。"""

    username: str = Field(min_length=1, max_length=100)


class AdminResponse(BaseModel):
    """会议管理员响应数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str | None
    phone: str | None
    is_active: bool


class StaffUpdate(BaseModel):
    """管理员修改工作人员资料和启用状态的请求。"""

    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)


class OperationResponse(BaseModel):
    """通用资源操作结果。"""

    success: bool
    message: str


class GuestLoginFieldsResponse(BaseModel):
    """会议嘉宾登录字段配置响应。"""

    fields: list[str]


class GuestDisplayFieldsRequest(BaseModel):
    """保存嘉宾端个人信息呈现字段的请求。"""

    fields: list[str]


class GuestDisplayFieldsResponse(BaseModel):
    """会议嘉宾端个人信息呈现字段响应。"""

    fields: list[str]


class GuestRegistrationFieldsRequest(BaseModel):
    """保存固定嘉宾字段在公开报名页中的配置。"""

    fields: list[str]
    required_fields: list[str]
    enabled_fields: list[str]


class GuestRegistrationFieldsResponse(GuestRegistrationFieldsRequest):
    """固定嘉宾字段的公开报名配置响应。"""


class ImportRowError(BaseModel):
    """Excel 嘉宾导入单行错误。"""

    row_number: int
    message: str


class GuestImportResponse(BaseModel):
    """Excel 嘉宾导入结果摘要。"""

    imported_count: int
    errors: list[ImportRowError]
