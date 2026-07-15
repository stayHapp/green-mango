"""工作人员签到与签到记录查询业务服务。"""

from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.access import StaffMeeting
from app.models.guest import CheckIn, Guest
from app.models.meeting import Meeting
from app.models.user import User


class CheckInBusinessError(Exception):
    """可映射为 HTTP 业务响应的签到异常。"""

    def __init__(self, status_code: int, message: str) -> None:
        """初始化签到业务异常。

        入参：status_code 为 HTTP 状态码；message 为面向调用方的中文错误信息，均必填。
        返回值：None：完成异常对象初始化。
        异常：当前构造函数不主动抛出业务异常。
        """
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def get_authorized_staff_meeting(db: Session, staff: User, meeting_id: int) -> Meeting | None:
    """查询工作人员被授权操作的会议。

    入参：db 为数据库会话；staff 为已验证工作人员；meeting_id 为会议 ID，均必填。
    返回值：Meeting | None：已授权会议存在时返回会议，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(Meeting)
        .join(StaffMeeting, StaffMeeting.meeting_id == Meeting.id)
        .where(Meeting.id == meeting_id, StaffMeeting.user_id == staff.id)
    )
    return db.scalar(statement)


def get_guest_by_token(db: Session, qr_token: str) -> Guest | None:
    """按二维码 token 查询嘉宾。

    入参：db 为数据库会话；qr_token 为已校验二维码 token，均必填。
    返回值：Guest | None：匹配嘉宾存在时返回对象，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    return db.scalar(select(Guest).where(Guest.qr_token == qr_token))


def create_check_in(db: Session, meeting: Meeting, staff: User, guest: Guest, method: str) -> CheckIn:
    """为指定嘉宾创建唯一签到记录。

    入参：db 为数据库会话；meeting 为已授权会议；staff 为已验证工作人员；guest 为待签到嘉宾；method 为 scan 或 manual，均必填。
    返回值：CheckIn：已持久化的签到记录。
    异常：会议结束、嘉宾不属于会议、嘉宾停用或已签到时抛出 CheckInBusinessError；数据库写入失败时由 SQLAlchemy 抛出异常。
    """
    end_time = meeting.end_time
    if end_time is not None:
        normalized_end_time = end_time if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc)
        if normalized_end_time <= datetime.now(timezone.utc):
            raise CheckInBusinessError(422, "会议已结束，二维码已失效。")
    if guest.meeting_id != meeting.id:
        raise CheckInBusinessError(422, "嘉宾不属于当前会议。")
    if not guest.is_active:
        raise CheckInBusinessError(422, "嘉宾已停用，无法签到。")
    if db.scalar(select(CheckIn.id).where(CheckIn.meeting_id == meeting.id, CheckIn.guest_id == guest.id)) is not None:
        raise CheckInBusinessError(409, "该嘉宾已签到，不能重复签到。")

    check_in = CheckIn(meeting_id=meeting.id, guest_id=guest.id, staff_id=staff.id, method=method)
    db.add(check_in)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise CheckInBusinessError(409, "该嘉宾已签到，不能重复签到。") from error
    db.refresh(check_in)
    return check_in


def list_check_ins(db: Session, meeting: Meeting) -> list[CheckIn]:
    """查询一个会议的签到记录。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：list[CheckIn]：按签到时间倒序排列的签到记录。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(CheckIn).where(CheckIn.meeting_id == meeting.id).order_by(CheckIn.checked_in_at.desc(), CheckIn.id.desc())
    return list(db.scalars(statement))


def search_guests_with_check_in_status(db: Session, meeting: Meeting, query: str) -> list[tuple[Guest, CheckIn | None]]:
    """按现场关键词搜索会议嘉宾并附带签到状态。

    入参：db 为数据库会话；meeting 为已授权会议；query 为可为空的搜索关键词，均必填。
    返回值：list[tuple[Guest, CheckIn | None]]：嘉宾与其签到记录的组合，未签到时记录为 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(Guest, CheckIn)
        .outerjoin(CheckIn, (CheckIn.meeting_id == Guest.meeting_id) & (CheckIn.guest_id == Guest.id))
        .where(Guest.meeting_id == meeting.id)
        .order_by(Guest.created_at, Guest.id)
    )
    normalized_query = query.strip().lower()
    if normalized_query:
        pattern = f"%{normalized_query}%"
        statement = statement.where(
            or_(
                Guest.name.ilike(pattern),
                Guest.phone.ilike(pattern),
                Guest.organization.ilike(pattern),
                Guest.seat.ilike(pattern),
            )
        )
    return list(db.execute(statement).tuples())
