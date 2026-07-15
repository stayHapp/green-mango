"""导入所有 ORM（对象关系映射）模型，确保 Alembic 能读取完整 metadata（元数据）。"""

from app.models.access import MeetingAdmin, StaffMeeting
from app.models.auth import AuthSession
from app.models.application import GuestApplication
from app.models.guest import CheckIn, Guest, GuestField, GuestValue
from app.models.meeting import Meeting, MeetingSetting
from app.models.registration import Registration, RegistrationField, RegistrationValue
from app.models.user import User

__all__ = [
    "AuthSession",
    "CheckIn",
    "Guest",
    "GuestApplication",
    "GuestField",
    "GuestValue",
    "Meeting",
    "MeetingAdmin",
    "MeetingSetting",
    "Registration",
    "RegistrationField",
    "RegistrationValue",
    "StaffMeeting",
    "User",
]
