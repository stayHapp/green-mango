"""管理员签到统计、明细与场次对比业务服务。"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.guest import CheckIn, Guest
from app.models.meeting import CheckInSession, Meeting
from app.models.user import User
from app.schemas.admin_check_in import (
    AdminCheckInComparison,
    AdminCheckInComparisonItem,
    AdminCheckInItem,
    AdminCheckInSummary,
)
from app.services.check_in_sessions import get_check_in_session, get_current_check_in_session, list_check_in_sessions


def normalize_utc_datetime(value: datetime) -> datetime:
    """恢复 SQLite 丢失的 UTC 时区信息。

    入参：value 为数据库读取的签到时间，必填。
    返回值：datetime：已有时区时保持原值，无时区时按系统统一写入规则补为 UTC。
    异常：当前函数不主动抛出异常。
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def build_comparison_item(check_in: CheckIn, guest: Guest, staff_name: str | None) -> AdminCheckInComparisonItem:
    """把签到记录转换为场次差异展示项。

    入参：check_in 为签到记录；guest 为该记录对应嘉宾；staff_name 为执行工作人员显示名，可为空。
    返回值：AdminCheckInComparisonItem：包含嘉宾和签到上下文的差异项。
    异常：签到记录字段缺失时由属性访问抛出异常。
    """
    return AdminCheckInComparisonItem(
        guest_id=guest.id,
        guest_name=guest.name,
        phone=guest.phone,
        checked_in_at=normalize_utc_datetime(check_in.checked_in_at),
        method=check_in.method,
        staff_name=staff_name,
    )


def get_previous_check_in_session(
    db: Session, meeting: Meeting, current_session: CheckInSession
) -> CheckInSession | None:
    """按后台展示顺序读取当前场次前一个签到场次。

    入参：db 为数据库会话；meeting 为已授权会议；current_session 为当前选中的签到场次，均必填。
    返回值：CheckInSession | None：存在前一场次时返回，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    sessions = list_check_in_sessions(db, meeting)
    current_index = next((index for index, session in enumerate(sessions) if session.id == current_session.id), -1)
    if current_index <= 0:
        return None
    return sessions[current_index - 1]


def load_session_check_in_map(db: Session, session: CheckInSession) -> dict[int, tuple[CheckIn, Guest, str | None]]:
    """读取一个签到场次中所有已签到嘉宾。

    入参：db 为数据库会话；session 为签到场次，必填。
    返回值：dict[int, tuple[CheckIn, Guest, str | None]]：以嘉宾 ID 为 key 的签到记录、嘉宾和工作人员名称。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(CheckIn, Guest, func.coalesce(User.display_name, User.username))
        .join(Guest, Guest.id == CheckIn.guest_id)
        .outerjoin(User, User.id == CheckIn.staff_id)
        .where(CheckIn.session_id == session.id, Guest.is_active.is_(True))
        .order_by(CheckIn.checked_in_at.desc(), CheckIn.id.desc())
    )
    return {
        guest.id: (check_in, guest, staff_name)
        for check_in, guest, staff_name in db.execute(statement).tuples()
    }


def build_check_in_comparison(
    db: Session,
    meeting: Meeting,
    current_session: CheckInSession,
    current_records: dict[int, tuple[CheckIn, Guest, str | None]],
) -> AdminCheckInComparison | None:
    """构建当前场次相对前一场次的签到差异。

    入参：db 为数据库会话；meeting 为已授权会议；current_session 为当前场次；current_records 为当前场次签到映射，均必填。
    返回值：AdminCheckInComparison | None：没有前一场次时返回 None，否则返回新增和减少名单。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    previous_session = get_previous_check_in_session(db, meeting, current_session)
    if previous_session is None:
        return None
    previous_records = load_session_check_in_map(db, previous_session)
    current_guest_ids = set(current_records)
    previous_guest_ids = set(previous_records)
    added_guests = [
        build_comparison_item(*current_records[guest_id])
        for guest_id in sorted(current_guest_ids - previous_guest_ids)
    ]
    removed_guests = [
        build_comparison_item(*previous_records[guest_id])
        for guest_id in sorted(previous_guest_ids - current_guest_ids)
    ]
    return AdminCheckInComparison(
        previous_session_id=previous_session.id,
        previous_session_title=previous_session.title,
        added_guests=added_guests,
        removed_guests=removed_guests,
    )


def resolve_summary_session(db: Session, meeting: Meeting, session_id: int | None) -> CheckInSession | None:
    """解析管理员统计所使用的签到场次。

    入参：db 为数据库会话；meeting 为已授权会议；session_id 为可选签到场次 ID。
    返回值：CheckInSession | None：指定场次存在时返回；未指定时返回默认场次；指定但不存在时返回 None。
    异常：数据库查询或默认场次创建失败时由 SQLAlchemy 抛出异常。
    """
    if session_id is not None:
        return get_check_in_session(db, meeting, session_id)
    return get_current_check_in_session(db, meeting)


def get_check_in_summary(db: Session, meeting: Meeting, session_id: int | None = None) -> AdminCheckInSummary | None:
    """计算会议指定签到场次的统计、明细和相邻场次差异。

    入参：db 为数据库会话；meeting 为已完成管理员授权校验的会议；session_id 为可选签到场次 ID。
    返回值：AdminCheckInSummary | None：场次存在时返回统计；指定场次不属于当前会议时返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    session = resolve_summary_session(db, meeting, session_id)
    if session is None:
        return None
    total_guests = db.scalar(
        select(func.count()).select_from(Guest).where(Guest.meeting_id == meeting.id, Guest.is_active.is_(True))
    ) or 0
    record_map = load_session_check_in_map(db, session)
    records = [
        AdminCheckInItem(
            session_id=session.id,
            session_title=session.title,
            guest_id=guest.id,
            guest_name=guest.name,
            phone=guest.phone,
            checked_in_at=normalize_utc_datetime(check_in.checked_in_at),
            method=check_in.method,
            staff_name=staff_name,
        )
        for check_in, guest, staff_name in record_map.values()
    ]
    return AdminCheckInSummary(
        session_id=session.id,
        session_title=session.title,
        total_guests=total_guests,
        checked_in_count=len(record_map),
        unchecked_count=max(total_guests - len(record_map), 0),
        records=records,
        comparison=build_check_in_comparison(db, meeting, session, record_map),
    )
