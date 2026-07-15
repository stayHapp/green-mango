"""工作人员创建、授权和会议查询业务服务。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.access import StaffMeeting
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.staff import StaffCreate


def create_or_authorize_staff(db: Session, meeting: Meeting, payload: StaffCreate) -> User:
    """创建工作人员账号或复用已有工作人员，并授权其负责会议。

    入参：db 为数据库会话；meeting 为已授权会议；payload 为工作人员创建数据，均必填。
    返回值：User：已创建或已存在的工作人员账号。
    异常：同名账号属于非工作人员时抛出 ValueError；数据库写入失败时由 SQLAlchemy 抛出异常。
    """
    staff = db.scalar(select(User).where(User.username == payload.username))
    if staff is not None and staff.role != "staff":
        raise ValueError("该账号已被非工作人员用户使用。")
    if staff is None:
        # 初始密码只在请求中出现，持久化前立即转换为带盐 scrypt 哈希。
        staff = User(
            username=payload.username,
            password_hash=hash_password(payload.initial_password),
            display_name=payload.display_name,
            phone=payload.phone,
            role="staff",
            is_active=True,
        )
        db.add(staff)
        db.flush()

    assignment = db.scalar(
        select(StaffMeeting).where(StaffMeeting.meeting_id == meeting.id, StaffMeeting.user_id == staff.id)
    )
    if assignment is None:
        db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    db.commit()
    db.refresh(staff)
    return staff


def list_meeting_staff(db: Session, meeting: Meeting) -> list[User]:
    """查询一个会议已授权的工作人员。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：list[User]：按账号 ID 升序排列的工作人员。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(User).join(StaffMeeting, StaffMeeting.user_id == User.id).where(StaffMeeting.meeting_id == meeting.id)
    return list(db.scalars(statement))


def list_staff_meetings(db: Session, staff: User) -> list[Meeting]:
    """查询工作人员被授权负责的会议列表。

    入参：db 为数据库会话；staff 为已验证工作人员账号，均必填。
    返回值：list[Meeting]：按创建时间倒序排列的负责会议。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(Meeting)
        .join(StaffMeeting, StaffMeeting.meeting_id == Meeting.id)
        .where(StaffMeeting.user_id == staff.id)
        .order_by(Meeting.created_at.desc())
    )
    return list(db.scalars(statement))
