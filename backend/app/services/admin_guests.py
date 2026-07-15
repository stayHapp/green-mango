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
            guest = Guest(meeting_id=meeting.id, qr_token=token, **payload.model_dump())
            db.add(guest)
            db.commit()
            db.refresh(guest)
            return guest
    raise RuntimeError("生成嘉宾二维码凭证失败，请重试。")
