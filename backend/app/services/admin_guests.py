"""管理员嘉宾字段配置与嘉宾管理业务服务。"""

import secrets

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.guest import Guest, GuestField, GuestValue
from app.models.meeting import Meeting
from app.schemas.guest import GuestCreate, GuestFieldInput


def list_guest_fields(db: Session, meeting: Meeting) -> list[GuestField]:
    """获取会议嘉宾字段配置。

    入参：db 为数据库会话；meeting 为已完成管理员授权校验的会议，均必填。
    返回值：list[GuestField]：按 sort_order、ID 升序排列的字段列表。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(GuestField).where(GuestField.meeting_id == meeting.id).order_by(GuestField.sort_order, GuestField.id)
    return list(db.scalars(statement))


def replace_guest_fields(db: Session, meeting: Meeting, fields: list[GuestFieldInput]) -> list[GuestField]:
    """安全地全量替换会议嘉宾字段配置。

    入参：db 为数据库会话；meeting 为已授权会议；fields 为已校验且 key 不重复的字段列表，均必填。
    返回值：list[GuestField]：保存后的字段配置，按排序规则返回。
    异常：会议已有嘉宾字段值时抛出 ValueError；数据库写入失败时由 SQLAlchemy 抛出异常。
    """
    value_statement = (
        select(GuestValue.id)
        .join(Guest, Guest.id == GuestValue.guest_id)
        .where(Guest.meeting_id == meeting.id)
        .limit(1)
    )
    if db.scalar(value_statement) is not None:
        raise ValueError("当前会议已有嘉宾字段值，不能全量替换字段配置。")

    db.execute(delete(GuestField).where(GuestField.meeting_id == meeting.id))
    created_fields = [GuestField(meeting_id=meeting.id, **field.model_dump()) for field in fields]
    db.add_all(created_fields)
    db.commit()
    return list_guest_fields(db, meeting)


def list_guests(db: Session, meeting: Meeting) -> list[Guest]:
    """获取一个会议下的嘉宾列表。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：list[Guest]：按创建时间、ID 升序排列的嘉宾列表。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(Guest).where(Guest.meeting_id == meeting.id).order_by(Guest.created_at, Guest.id)
    return list(db.scalars(statement))


def create_guest(db: Session, meeting: Meeting, payload: GuestCreate) -> Guest:
    """在指定会议录入嘉宾并生成随机二维码 token。

    入参：db 为数据库会话；meeting 为已授权会议；payload 为已校验嘉宾输入，均必填。
    返回值：Guest：已持久化且带唯一二维码 token 的嘉宾对象。
    异常：连续生成的 token 均与现有数据冲突时抛出 RuntimeError；数据库写入失败时由 SQLAlchemy 抛出异常。
    """
    for _ in range(5):
        token = secrets.token_urlsafe(32)
        if db.scalar(select(Guest.id).where(Guest.qr_token == token)) is None:
            fixed_values = payload.model_dump(exclude={"values"})
            guest = Guest(meeting_id=meeting.id, qr_token=token, **fixed_values)
            db.add(guest)
            db.flush()
            save_guest_values(db, meeting, guest, payload.values, require_all=True)
            db.commit()
            db.refresh(guest)
            return guest
    raise RuntimeError("生成嘉宾二维码凭证失败，请重试。")


def save_guest_values(
    db: Session,
    meeting: Meeting,
    guest: Guest,
    values: dict[str, str | None],
    require_all: bool,
) -> None:
    """校验并保存嘉宾动态字段值。

    入参：db 为数据库会话；meeting 为会议；guest 为嘉宾；values 为 key 到值的映射；require_all 控制是否校验全部必填字段。
    返回值：None：校验通过后新增或更新 GuestValue，事务由调用方提交。
    异常：字段不存在、必填值缺失或字段不属于会议时抛出 ValueError。
    """
    fields = list(db.scalars(select(GuestField).where(GuestField.meeting_id == meeting.id)))
    fields_by_key = {field.key: field for field in fields}
    unknown_keys = set(values) - set(fields_by_key)
    if unknown_keys:
        raise ValueError(f"存在未配置的嘉宾字段：{', '.join(sorted(unknown_keys))}。")
    if require_all:
        missing_required = [
            field.label
            for field in fields
            if field.required and (field.key not in values or values[field.key] is None or not str(values[field.key]).strip())
        ]
        if missing_required:
            raise ValueError(f"缺少必填嘉宾字段：{', '.join(missing_required)}。")

    for key, value in values.items():
        field = fields_by_key[key]
        guest_value = db.scalar(
            select(GuestValue).where(GuestValue.guest_id == guest.id, GuestValue.field_id == field.id)
        )
        if guest_value is None:
            db.add(GuestValue(guest_id=guest.id, field_id=field.id, field_key=key, value_text=value))
        else:
            guest_value.value_text = value


def get_guest_values(db: Session, guest: Guest) -> dict[str, str | None]:
    """读取嘉宾动态字段值映射。

    入参：db 为数据库会话；guest 为目标嘉宾，均必填。
    返回值：dict[str, str | None]：字段 key 到文本值的映射。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(GuestValue).where(GuestValue.guest_id == guest.id).order_by(GuestValue.id)
    return {value.field_key: value.value_text for value in db.scalars(statement)}
