"""管理员签到统计与明细业务服务。"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.guest import CheckIn, Guest
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.admin_check_in import AdminCheckInItem, AdminCheckInSummary


def normalize_utc_datetime(value: datetime) -> datetime:
    """恢复 SQLite 丢失的 UTC 时区信息。

    入参：value 为数据库读取的签到时间，必填。
    返回值：datetime：已有时区时保持原值，无时区时按系统统一写入规则补为 UTC。
    异常：当前函数不主动抛出异常。
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def get_check_in_summary(db: Session, meeting: Meeting) -> AdminCheckInSummary:
    """计算会议签到统计并读取签到明细。

    入参：db 为数据库会话；meeting 为已完成管理员授权校验的会议，均必填。
    返回值：AdminCheckInSummary：嘉宾总数、已签到数、未签到数及签到明细。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    total_guests = db.scalar(select(func.count()).select_from(Guest).where(Guest.meeting_id == meeting.id)) or 0
    checked_in_count = db.scalar(select(func.count()).select_from(CheckIn).where(CheckIn.meeting_id == meeting.id)) or 0
    statement = (
        select(CheckIn, Guest, User.display_name)
        .join(Guest, Guest.id == CheckIn.guest_id)
        .outerjoin(User, User.id == CheckIn.staff_id)
        .where(CheckIn.meeting_id == meeting.id)
        .order_by(CheckIn.checked_in_at.desc(), CheckIn.id.desc())
    )
    records = [
        AdminCheckInItem(
            guest_id=guest.id,
            guest_name=guest.name,
            phone=guest.phone,
            checked_in_at=normalize_utc_datetime(check_in.checked_in_at),
            method=check_in.method,
            staff_name=staff_name,
        )
        for check_in, guest, staff_name in db.execute(statement).tuples()
    ]
    return AdminCheckInSummary(
        total_guests=total_guests,
        checked_in_count=checked_in_count,
        unchecked_count=max(total_guests - checked_in_count, 0),
        records=records,
    )
