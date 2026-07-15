"""嘉宾登录和嘉宾会议查询业务服务。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.meeting import Meeting


def login_guest(db: Session, meeting_id: int, name: str, phone: str) -> Guest | None:
    """在已发布或已结束会议内按姓名和手机号匹配已启用嘉宾。

    入参：db 为数据库会话；meeting_id 为会议 ID；name 与 phone 为已标准化登录信息，均必填。
    返回值：Guest | None：匹配的启用嘉宾存在时返回对象，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(Guest)
        .join(Meeting, Meeting.id == Guest.meeting_id)
        .where(
            Guest.meeting_id == meeting_id,
            Guest.name == name,
            Guest.phone == phone,
            Guest.is_active.is_(True),
            Meeting.status.in_(["published", "ended"]),
        )
    )
    return db.scalar(statement)


def get_guest_meeting(db: Session, guest: Guest, meeting_id: int) -> Meeting | None:
    """读取嘉宾所属的指定会议，阻止跨会议访问。

    入参：db 为数据库会话；guest 为已验证嘉宾；meeting_id 为目标会议 ID，均必填。
    返回值：Meeting | None：目标会议属于嘉宾时返回会议，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    if guest.meeting_id != meeting_id:
        return None
    return db.get(Meeting, meeting_id)


def list_guest_meetings(db: Session, guest: Guest) -> list[Meeting]:
    """查询当前嘉宾可访问的会议列表。

    入参：db 为数据库会话；guest 为已验证嘉宾，均必填。
    返回值：list[Meeting]：当前模型中包含嘉宾所属的一场会议，保留列表结构以兼容后续扩展。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(Meeting).where(Meeting.id == guest.meeting_id)
    return list(db.scalars(statement))
