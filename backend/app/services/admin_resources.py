"""嘉宾、工作人员和会议管理员的补充维护业务服务。"""

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.access import MeetingAdmin, StaffMeeting
from app.models.guest import Guest
from app.models.meeting import Meeting, MeetingSetting
from app.models.user import User
from app.schemas.admin_resources import StaffUpdate
from app.schemas.guest import GuestUpdate
from app.services.admin_guests import ensure_guest_identity_available, save_guest_values

FIXED_GUEST_DISPLAY_FIELDS = ("name", "phone", "organization", "title", "tag", "seat")
DEFAULT_GUEST_REGISTRATION_FIELDS = ("name", "phone", "organization", "title")
DEFAULT_GUEST_REQUIRED_FIELDS = ("name", "phone")


def get_guest_registration_settings(meeting: Meeting) -> tuple[list[str], list[str], list[str]]:
    """读取固定嘉宾字段在公开报名页中的启用、呈现和必填配置。

    入参：meeting 为已加载的会议对象，必填。
    返回值：tuple[list[str], list[str], list[str]]：依次为报名字段、必填字段和启用字段的有序 key 列表。
    异常：当前函数不主动抛出异常；历史配置非法时自动回退为兼容默认值。
    """
    settings_json = meeting.setting.settings_json if meeting.setting else {}
    configured_fields = settings_json.get("guest_registration_fields", list(DEFAULT_GUEST_REGISTRATION_FIELDS))
    configured_required = settings_json.get("guest_registration_required_fields", list(DEFAULT_GUEST_REQUIRED_FIELDS))
    configured_enabled = settings_json.get("guest_enabled_fixed_fields", list(FIXED_GUEST_DISPLAY_FIELDS))
    enabled_fields = [key for key in configured_enabled if isinstance(key, str) and key in FIXED_GUEST_DISPLAY_FIELDS]
    registration_fields = [
        key
        for key in configured_fields
        if isinstance(key, str) and key in enabled_fields
    ]
    required_fields = [
        key
        for key in configured_required
        if isinstance(key, str) and key in registration_fields
    ]
    # 姓名和手机号是嘉宾登录凭证，始终启用、呈现并必填。
    for key in reversed(DEFAULT_GUEST_REQUIRED_FIELDS):
        if key not in enabled_fields:
            enabled_fields.insert(0, key)
        if key not in registration_fields:
            registration_fields.insert(0, key)
        if key not in required_fields:
            required_fields.insert(0, key)
    return registration_fields, required_fields, enabled_fields


def save_guest_registration_settings(
    db: Session,
    meeting: Meeting,
    fields: list[str],
    required_fields: list[str],
    enabled_fields: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """保存固定嘉宾字段在公开报名页中的配置。

    入参：db 为数据库会话；meeting 为目标会议；fields、required_fields、enabled_fields 分别为报名、必填与启用字段 key 列表。
    返回值：tuple[list[str], list[str], list[str]]：保存后规范化的报名、必填与启用字段列表。
    异常：包含未知字段、关闭登录凭证字段或必填字段未同时报名和启用时抛出 ValueError。
    """
    sequences = (fields, required_fields, enabled_fields)
    invalid_fields = [
        key
        for sequence in sequences
        for key in sequence
        if key not in FIXED_GUEST_DISPLAY_FIELDS
    ]
    if invalid_fields:
        raise ValueError(f"存在不可用的固定嘉宾字段：{', '.join(sorted(set(invalid_fields)))}。")
    normalized_enabled = list(dict.fromkeys(enabled_fields))
    normalized_fields = [key for key in dict.fromkeys(fields) if key in normalized_enabled]
    normalized_required = [key for key in dict.fromkeys(required_fields) if key in normalized_fields]
    for key in reversed(DEFAULT_GUEST_REQUIRED_FIELDS):
        if key not in normalized_enabled:
            normalized_enabled.insert(0, key)
        if key not in normalized_fields:
            normalized_fields.insert(0, key)
        if key not in normalized_required:
            normalized_required.insert(0, key)
    if meeting.setting is None:
        meeting.setting = MeetingSetting(settings_json={})
    settings_json = dict(meeting.setting.settings_json)
    settings_json["guest_registration_fields"] = normalized_fields
    settings_json["guest_registration_required_fields"] = normalized_required
    settings_json["guest_enabled_fixed_fields"] = normalized_enabled
    meeting.setting.settings_json = settings_json
    db.commit()
    return normalized_fields, normalized_required, normalized_enabled


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
    target_name = values.get("name", guest.name)
    target_phone = values.get("phone", guest.phone)
    target_active = values.get("is_active", guest.is_active)
    # 只有目标记录保持启用时才占用登录身份；停用记录允许后续重新录入同一嘉宾。
    if target_active:
        ensure_guest_identity_available(db, meeting, target_name, target_phone, exclude_guest_id=guest.id)
    for field_name, value in values.items():
        setattr(guest, field_name, value)
    if dynamic_values is not None:
        save_guest_values(db, meeting, guest, dynamic_values, require_all=False)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ValueError("当前会议已存在姓名和手机号相同的启用嘉宾。") from error
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
    _, _, enabled_fixed_fields = get_guest_registration_settings(meeting)
    dynamic_fields = [field.key for field in meeting.guest_fields if field.is_enabled]
    default_fields = [
        *enabled_fixed_fields,
        *(field.key for field in meeting.guest_fields if field.is_enabled and field.visible_to_guest),
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
    _, _, enabled_fixed_fields = get_guest_registration_settings(meeting)
    allowed_fields = set(enabled_fixed_fields) | {field.key for field in meeting.guest_fields if field.is_enabled}
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
