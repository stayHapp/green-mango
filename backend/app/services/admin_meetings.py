"""管理员会议管理业务服务。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access import MeetingAdmin
from app.models.meeting import Meeting, MeetingSetting
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingUpdate


def list_authorized_meetings(db: Session, admin: User) -> list[Meeting]:
    """查询指定管理员被授权管理的全部会议。

    入参：
        db：数据库会话，必填。
        admin：已完成管理员身份校验的用户对象，必填。

    返回值：
        list[Meeting]：按创建时间倒序排列的会议列表。

    异常：
        数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(Meeting)
        .join(MeetingAdmin, MeetingAdmin.meeting_id == Meeting.id)
        .where(MeetingAdmin.user_id == admin.id)
        .order_by(Meeting.created_at.desc())
    )
    return list(db.scalars(statement))


def get_authorized_meeting(db: Session, admin: User, meeting_id: int) -> Meeting | None:
    """查询管理员有权限访问的单个会议。

    入参：
        db：数据库会话，必填。
        admin：已完成管理员身份校验的用户对象，必填。
        meeting_id：会议 ID，必填，必须为正整数。

    返回值：
        Meeting | None：存在且已授权时返回会议，否则返回 None。

    异常：
        数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(Meeting)
        .join(MeetingAdmin, MeetingAdmin.meeting_id == Meeting.id)
        .where(Meeting.id == meeting_id, MeetingAdmin.user_id == admin.id)
    )
    return db.scalar(statement)


def create_meeting(db: Session, admin: User, payload: MeetingCreate) -> Meeting:
    """创建会议、默认会议设置和创建人的管理员授权。

    入参：
        db：数据库会话，必填。
        admin：创建会议的已授权管理员，必填。
        payload：已通过请求校验的会议创建数据，必填。

    返回值：
        Meeting：已持久化且已加载主键的会议对象。

    异常：
        数据库写入或提交失败时由 SQLAlchemy 抛出异常。
    """
    meeting = Meeting(created_by_id=admin.id, **payload.model_dump())
    db.add(meeting)
    db.flush()
    # 新会议默认允许保留的嘉宾报名补充入口，具体开关由后续设置 API 管理。
    db.add(MeetingSetting(meeting_id=meeting.id))
    db.add(MeetingAdmin(meeting_id=meeting.id, user_id=admin.id))
    db.commit()
    db.refresh(meeting)
    return meeting


def update_meeting(db: Session, meeting: Meeting, payload: MeetingUpdate) -> Meeting:
    """更新已有会议的允许修改字段并校验最终时间范围。

    入参：
        db：数据库会话，必填。
        meeting：已完成管理员授权校验的会议对象，必填。
        payload：会议修改数据，必填；未传字段保持原值。

    返回值：
        Meeting：已持久化后的会议对象。

    异常：
        修改后的结束时间早于或等于开始时间时抛出 ValueError；数据库提交失败时由 SQLAlchemy 抛出异常。
    """
    values = payload.model_dump(exclude_unset=True)
    start_time = values.get("start_time", meeting.start_time)
    end_time = values.get("end_time", meeting.end_time)
    if start_time and end_time and end_time <= start_time:
        raise ValueError("会议结束时间必须晚于开始时间。")

    for field_name, value in values.items():
        setattr(meeting, field_name, value)
    db.commit()
    db.refresh(meeting)
    return meeting
