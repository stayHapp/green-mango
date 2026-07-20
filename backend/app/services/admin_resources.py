"""嘉宾、工作人员和会议管理员的补充维护业务服务。"""

import secrets

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.access import MeetingAdmin, StaffMeeting
from app.models.guest import Guest
from app.models.meeting import Meeting, MeetingSetting
from app.models.user import User
from app.schemas.admin_resources import StaffUpdate
from app.schemas.guest import GuestUpdate
from app.services.admin_guests import save_guest_values

FIXED_GUEST_DISPLAY_FIELDS = ("name", "phone", "organization", "title", "tag", "seat")


def update_guest(db: Session, meeting: Meeting, guest: Guest, payload: GuestUpdate) -> Guest:
    """修改会议嘉宾固定信息、动态字段值和启用状态。

    入参：db 为数据库会话；meeting 为已授权会议；guest 为目标嘉宾；payload 为修改数据。
    返回值：Guest：更新后的嘉宾对象。
    异常：嘉宾不属于会议或动态字段无效时抛出 ValueError。
    """
    if guest.meeting_id != meeting.id:
        raise ValueError("嘉宾不属于当前会议。")
    values = payload.model_dump(exclude_unset=True)
    dynamic_values = values.pop("values", None)
    for field_name, value in values.items():
        setattr(guest, field_name, value)
    if dynamic_values is not None:
        save_guest_values(db, meeting, guest, dynamic_values, require_all=False)
    db.commit()
    db.refresh(guest)
    return guest


def deactivate_guest(db: Session, meeting: Meeting, guest: Guest) -> None:
    """软停用会议嘉宾并保留历史签到数据。

    入参：db 为数据库会话；meeting 为已授权会议；guest 为目标嘉宾。
    返回值：None：提交后嘉宾不能登录或签到。
    异常：嘉宾不属于会议时抛出 ValueError。
    """
    if guest.meeting_id != meeting.id:
        raise ValueError("嘉宾不属于当前会议。")
    guest.is_active = False
    db.commit()


def get_login_fields(meeting: Meeting) -> list[str]:
    """读取会议嘉宾登录字段配置。

    入参：meeting 为已加载会议，必填。
    返回值：list[str]：当前 MVP 固定或已保存的 name、phone 字段。
    异常：当前函数不主动抛出业务异常。
    """
    settings_json = meeting.setting.settings_json if meeting.setting else {}
    fields = settings_json.get("guest_login_fields", ["name", "phone"])
    return list(fields) if isinstance(fields, list) else ["name", "phone"]


def save_login_fields(db: Session, meeting: Meeting, fields: list[str]) -> list[str]:
    """保存会议嘉宾登录字段配置。

    入参：db 为数据库会话；meeting 为目标会议；fields 为已校验字段列表。
    返回值：list[str]：保存后的字段列表。
    异常：数据库提交失败时由 SQLAlchemy 抛出异常。
    """
    if meeting.setting is None:
        meeting.setting = MeetingSetting(settings_json={})
    settings_json = dict(meeting.setting.settings_json)
    settings_json["guest_login_fields"] = fields
    meeting.setting.settings_json = settings_json
    db.commit()
    return fields


def get_guest_display_fields(meeting: Meeting) -> list[str]:
    """读取会议嘉宾端个人信息呈现字段。

    入参：meeting 为已加载会议，必填。
    返回值：list[str]：固定字段与动态字段组成的有序字段 key 列表。
    异常：当前函数不主动抛出业务异常；历史配置无效时回退为默认呈现字段。
    """
    dynamic_fields = [field.key for field in meeting.guest_fields]
    default_fields = [
        *FIXED_GUEST_DISPLAY_FIELDS,
        *(field.key for field in meeting.guest_fields if field.visible_to_guest),
    ]
    settings_json = meeting.setting.settings_json if meeting.setting else {}
    configured_fields = settings_json.get("guest_visible_fields")
    if not isinstance(configured_fields, list):
        return default_fields

    allowed_fields = set(FIXED_GUEST_DISPLAY_FIELDS) | set(dynamic_fields)
    # 配置读取时过滤已删除或非法 key，避免历史设置让嘉宾端出现无效字段。
    return [
        field
        for field in configured_fields
        if isinstance(field, str) and field in allowed_fields
    ]


def save_guest_display_fields(db: Session, meeting: Meeting, fields: list[str]) -> list[str]:
    """保存会议嘉宾端个人信息呈现字段。

    入参：db 为数据库会话；meeting 为目标会议；fields 为管理员选择的字段 key 列表，均必填。
    返回值：list[str]：去重后按请求顺序保存的字段 key 列表。
    异常：包含当前会议不存在的固定或动态字段 key 时抛出 ValueError；数据库提交失败时向上抛出异常。
    使用示例：保存 `["name", "organization", "seat"]` 后嘉宾端只呈现对应非空资料。
    """
    allowed_fields = set(FIXED_GUEST_DISPLAY_FIELDS) | {field.key for field in meeting.guest_fields}
    invalid_fields = [field for field in fields if field not in allowed_fields]
    if invalid_fields:
        raise ValueError(f"存在不可用的嘉宾呈现字段：{', '.join(invalid_fields)}。")

    normalized_fields = list(dict.fromkeys(fields))
    if meeting.setting is None:
        meeting.setting = MeetingSetting(settings_json={})
    settings_json = dict(meeting.setting.settings_json)
    settings_json["guest_visible_fields"] = normalized_fields
    meeting.setting.settings_json = settings_json
    db.commit()
    return normalized_fields


def regenerate_missing_guest_tokens(db: Session, meeting: Meeting) -> tuple[int, int]:
    """为会议中缺少 token 的嘉宾补生成随机凭证。

    入参：db 为数据库会话；meeting 为目标会议。
    返回值：tuple[int, int]：生成数量与已有数量。
    异常：数据库提交失败时由 SQLAlchemy 抛出异常。
    """
    guests = list(db.scalars(select(Guest).where(Guest.meeting_id == meeting.id)))
    generated_count = 0
    existing_count = 0
    for guest in guests:
        if guest.qr_token:
            existing_count += 1
        else:
            guest.qr_token = secrets.token_urlsafe(32)
            generated_count += 1
    db.commit()
    return generated_count, existing_count


def update_staff(db: Session, staff: User, payload: StaffUpdate) -> User:
    """修改工作人员资料、启用状态或密码。

    入参：db 为数据库会话；staff 为工作人员；payload 为修改数据。
    返回值：User：更新后的工作人员。
    异常：目标不是工作人员时抛出 ValueError。
    """
    if staff.role != "staff":
        raise ValueError("目标账号不是工作人员。")
    values = payload.model_dump(exclude_unset=True)
    new_password = values.pop("new_password", None)
    for field_name, value in values.items():
        setattr(staff, field_name, value)
    if new_password:
        staff.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(staff)
    return staff


def remove_staff_assignment(db: Session, meeting: Meeting, staff_id: int) -> bool:
    """解除工作人员与会议的授权关系。

    入参：db 为数据库会话；meeting 为会议；staff_id 为工作人员 ID。
    返回值：bool：删除了授权时返回 True，否则返回 False。
    异常：数据库提交失败时由 SQLAlchemy 抛出异常。
    """
    result = db.execute(
        delete(StaffMeeting).where(StaffMeeting.meeting_id == meeting.id, StaffMeeting.user_id == staff_id)
    )
    db.commit()
    return bool(result.rowcount)


def list_meeting_admins(db: Session, meeting: Meeting) -> list[User]:
    """查询会议管理员列表。

    入参：db 为数据库会话；meeting 为目标会议。
    返回值：list[User]：已授权管理员列表。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(User).join(MeetingAdmin, MeetingAdmin.user_id == User.id).where(MeetingAdmin.meeting_id == meeting.id)
    return list(db.scalars(statement))


def add_meeting_admin(db: Session, meeting: Meeting, username: str) -> User:
    """按账号为会议添加管理员授权。

    入参：db 为数据库会话；meeting 为会议；username 为已存在管理员账号。
    返回值：User：被授权管理员。
    异常：账号不存在、非管理员或停用时抛出 ValueError。
    """
    user = db.scalar(select(User).where(User.username == username))
    if user is None or user.role != "admin" or not user.is_active:
        raise ValueError("未找到可用的管理员账号。")
    assignment = db.scalar(
        select(MeetingAdmin).where(MeetingAdmin.meeting_id == meeting.id, MeetingAdmin.user_id == user.id)
    )
    if assignment is None:
        db.add(MeetingAdmin(meeting_id=meeting.id, user_id=user.id))
        db.commit()
    return user


def remove_meeting_admin(db: Session, meeting: Meeting, user_id: int) -> None:
    """移除会议管理员授权并保护会议创建人。

    入参：db 为数据库会话；meeting 为会议；user_id 为待移除管理员 ID。
    返回值：None：提交后授权被移除。
    异常：试图移除创建人或不存在授权时抛出 ValueError。
    """
    if meeting.created_by_id == user_id:
        raise ValueError("不能移除会议创建人。")
    assignment = db.scalar(
        select(MeetingAdmin).where(MeetingAdmin.meeting_id == meeting.id, MeetingAdmin.user_id == user_id)
    )
    if assignment is None:
        raise ValueError("会议管理员授权不存在。")
    db.delete(assignment)
    db.commit()
