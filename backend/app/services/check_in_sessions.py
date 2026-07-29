"""签到场次管理与默认场次兜底服务。"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.meeting import CheckInSession, Meeting, MeetingSetting

DEFAULT_CHECK_IN_SESSION_TITLE = "默认签到"
CHECK_IN_MODE_KEY = "check_in_mode"
CHECK_IN_MANUAL_DEFAULT_SESSION_ID_KEY = "check_in_manual_default_session_id"
CHECK_IN_MODE_SINGLE = "single"
CHECK_IN_MODE_DATE = "date"
CHECK_IN_MODE_CUSTOM = "custom"
VALID_CHECK_IN_MODES = {CHECK_IN_MODE_SINGLE, CHECK_IN_MODE_DATE, CHECK_IN_MODE_CUSTOM}
CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")


class CheckInSessionBusinessError(Exception):
    """可转换为 HTTP 响应的签到场次业务异常。"""

    def __init__(self, status_code: int, message: str) -> None:
        """初始化签到场次业务异常。

        入参：status_code 为 HTTP 状态码；message 为面向管理员的中文错误信息，均必填。
        返回值：None：完成异常对象初始化。
        异常：当前构造函数不主动抛出业务异常。
        """
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def normalize_session_title(title: str) -> str:
    """规范化签到场次名称。

    入参：title 为管理员输入的场次名称，必填，长度由接口模型限制。
    返回值：str：去除首尾空白后的名称。
    异常：名称为空白时抛出 CheckInSessionBusinessError。
    """
    normalized_title = title.strip()
    if not normalized_title:
        raise CheckInSessionBusinessError(422, "签到场次名称不能为空。")
    return normalized_title


def list_check_in_sessions(db: Session, meeting: Meeting) -> list[CheckInSession]:
    """查询会议下的所有签到场次。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：list[CheckInSession]：按排序值、开始时间和主键排列的签到场次。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(CheckInSession)
        .where(CheckInSession.meeting_id == meeting.id)
        .order_by(CheckInSession.sort_order, CheckInSession.starts_at, CheckInSession.id)
    )
    return list(db.scalars(statement))


def ensure_meeting_setting(db: Session, meeting: Meeting) -> MeetingSetting:
    """读取或创建会议级设置记录。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：MeetingSetting：当前会议的设置记录，缺失时创建但不立即提交。
    异常：数据库写入失败时由 SQLAlchemy 抛出异常。
    """
    if meeting.setting is not None:
        return meeting.setting
    setting = MeetingSetting(meeting_id=meeting.id, settings_json={})
    db.add(setting)
    meeting.setting = setting
    return setting


def normalize_session_datetime(value: datetime | None) -> datetime | None:
    """将签到场次时间规范为中国时区时间。

    入参：value 为签到场次开始或结束时间，可为空。
    返回值：datetime | None：空值原样返回；无时区值按会议本地中国时间解释；有时区值转换到中国时区。
    异常：当前函数不主动抛出异常。
    """
    if value is None:
        return None
    if value.tzinfo is None:
        # SQLite 会丢失管理员输入时区，签到场次配置按会议本地时间解释。
        return value.replace(tzinfo=CHINA_TIMEZONE)
    return value.astimezone(CHINA_TIMEZONE)


def is_full_day_date_session(session: CheckInSession) -> bool:
    """判断场次是否符合系统日期场次特征。

    入参：session 为待判断签到场次，必填。
    返回值：bool：开始与结束位于中国时区同一天，且覆盖整日核心范围时返回 True。
    异常：当前函数不主动抛出异常。
    """
    starts_at = normalize_session_datetime(session.starts_at)
    ends_at = normalize_session_datetime(session.ends_at)
    if starts_at is None or ends_at is None:
        return False
    return (
        starts_at.date() == ends_at.date()
        and starts_at.hour == 0
        and starts_at.minute == 0
        and ends_at.hour == 23
        and ends_at.minute >= 50
    )


def infer_check_in_mode(sessions: list[CheckInSession]) -> str:
    """根据现有场次推断会议签到规则。

    入参：sessions 为会议签到场次列表，必填。
    返回值：str：单场、日期或自定义规则标识。
    异常：当前函数不主动抛出异常。
    """
    if len(sessions) <= 1:
        return CHECK_IN_MODE_SINGLE
    if any(is_full_day_date_session(session) for session in sessions):
        return CHECK_IN_MODE_DATE
    return CHECK_IN_MODE_CUSTOM


def get_check_in_mode(db: Session, meeting: Meeting) -> str:
    """读取会议级签到规则。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：str：显式配置存在时返回配置值，否则按现有场次推断。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    settings_json = meeting.setting.settings_json if meeting.setting else {}
    configured_mode = settings_json.get(CHECK_IN_MODE_KEY)
    if isinstance(configured_mode, str) and configured_mode in VALID_CHECK_IN_MODES:
        return configured_mode
    return infer_check_in_mode(list_check_in_sessions(db, meeting))


def get_manual_default_session_id(meeting: Meeting) -> int | None:
    """读取日期规则下的手动默认场次覆盖。

    入参：meeting 为已授权会议，必填。
    返回值：int | None：存在合法数字 ID 时返回，否则返回 None。
    异常：当前函数不主动抛出异常。
    """
    settings_json = meeting.setting.settings_json if meeting.setting else {}
    raw_value = settings_json.get(CHECK_IN_MANUAL_DEFAULT_SESSION_ID_KEY)
    if isinstance(raw_value, int):
        return raw_value
    if isinstance(raw_value, str) and raw_value.isdigit():
        return int(raw_value)
    return None


def sync_default_session(db: Session, sessions: list[CheckInSession], target_session: CheckInSession) -> CheckInSession:
    """同步会议默认场次标记。

    入参：db 为数据库会话；sessions 为同会议场次列表；target_session 为当前有效场次，均必填。
    返回值：CheckInSession：已同步默认标记的目标场次。
    异常：数据库提交失败时由 SQLAlchemy 抛出异常。
    """
    changed = False
    for session in sessions:
        next_is_default = session.id == target_session.id
        if session.is_default != next_is_default:
            # 默认标记仍保留在场次表，便于列表展示和历史兼容接口读取。
            session.is_default = next_is_default
            changed = True
    if changed:
        db.commit()
        for session in sessions:
            db.refresh(session)
    return target_session


def find_date_session_for_now(sessions: list[CheckInSession], now: datetime) -> CheckInSession | None:
    """按当前中国日期匹配日期签到场次。

    入参：sessions 为会议场次列表；now 为服务端当前时间或测试注入时间，均必填。
    返回值：CheckInSession | None：当前日期落入某个日期场次时返回该场次，否则返回 None。
    异常：当前函数不主动抛出异常。
    """
    now_china = now.astimezone(CHINA_TIMEZONE) if now.tzinfo else now.replace(tzinfo=CHINA_TIMEZONE)
    for session in sessions:
        starts_at = normalize_session_datetime(session.starts_at)
        ends_at = normalize_session_datetime(session.ends_at)
        if starts_at is None or ends_at is None:
            continue
        if starts_at <= now_china <= ends_at:
            return session
        if is_full_day_date_session(session) and starts_at.date() == now_china.date():
            return session
    return None


def get_current_check_in_session(
    db: Session,
    meeting: Meeting,
    now: datetime | None = None,
) -> CheckInSession:
    """读取会议当前有效签到场次。

    入参：db 为数据库会话；meeting 为已授权会议；now 为可选测试时间，不传时使用服务端当前时间。
    返回值：CheckInSession：用于工作人员签到、嘉宾签到状态和后台默认统计的统一场次。
    异常：数据库读写失败时由 SQLAlchemy 抛出异常。
    """
    get_default_check_in_session(db, meeting)
    sessions = list_check_in_sessions(db, meeting)
    mode = get_check_in_mode(db, meeting)
    if mode == CHECK_IN_MODE_DATE:
        manual_default_session_id = get_manual_default_session_id(meeting)
        if manual_default_session_id is not None:
            manual_session = next((session for session in sessions if session.id == manual_default_session_id), None)
            if manual_session is not None:
                return sync_default_session(db, sessions, manual_session)
        date_session = find_date_session_for_now(sessions, now or datetime.now(tz=CHINA_TIMEZONE))
        if date_session is not None:
            return sync_default_session(db, sessions, date_session)
    default_session = next((session for session in sessions if session.is_default), sessions[0])
    return sync_default_session(db, sessions, default_session)


def update_check_in_settings(
    db: Session,
    meeting: Meeting,
    mode: str,
    manual_default_session_id: int | None,
) -> CheckInSession:
    """更新会议级签到规则并返回当前有效场次。

    入参：db 为数据库会话；meeting 为已授权会议；mode 为签到规则标识；manual_default_session_id 为可选手动默认场次 ID。
    返回值：CheckInSession：规则保存后解析得到的当前有效场次。
    异常：规则无效或手动默认场次不属于会议时抛出 CheckInSessionBusinessError；数据库失败时由 SQLAlchemy 抛出异常。
    """
    if mode not in VALID_CHECK_IN_MODES:
        raise CheckInSessionBusinessError(422, "签到规则无效。")
    if manual_default_session_id is not None and get_check_in_session(db, meeting, manual_default_session_id) is None:
        raise CheckInSessionBusinessError(404, "手动默认场次不存在。")
    setting = ensure_meeting_setting(db, meeting)
    settings_json = dict(setting.settings_json or {})
    settings_json[CHECK_IN_MODE_KEY] = mode
    if mode == CHECK_IN_MODE_DATE and manual_default_session_id is not None:
        settings_json[CHECK_IN_MANUAL_DEFAULT_SESSION_ID_KEY] = manual_default_session_id
    else:
        settings_json.pop(CHECK_IN_MANUAL_DEFAULT_SESSION_ID_KEY, None)
    setting.settings_json = settings_json
    db.commit()
    db.refresh(setting)
    return get_current_check_in_session(db, meeting)


def get_check_in_session(db: Session, meeting: Meeting, session_id: int) -> CheckInSession | None:
    """读取会议下指定签到场次。

    入参：db 为数据库会话；meeting 为已授权会议；session_id 为签到场次 ID，均必填。
    返回值：CheckInSession | None：匹配当前会议时返回场次，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    return db.scalar(
        select(CheckInSession).where(CheckInSession.id == session_id, CheckInSession.meeting_id == meeting.id)
    )


def get_default_check_in_session(db: Session, meeting: Meeting) -> CheckInSession:
    """读取或创建会议默认签到场次。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：CheckInSession：会议默认签到场次。
    异常：数据库写入失败时由 SQLAlchemy 抛出异常。
    """
    default_session = db.scalar(
        select(CheckInSession)
        .where(CheckInSession.meeting_id == meeting.id, CheckInSession.is_default.is_(True))
        .order_by(CheckInSession.sort_order, CheckInSession.id)
    )
    if default_session is not None:
        return default_session

    first_session = db.scalar(
        select(CheckInSession)
        .where(CheckInSession.meeting_id == meeting.id)
        .order_by(CheckInSession.sort_order, CheckInSession.id)
    )
    if first_session is not None:
        # 历史异常数据没有默认标记时，将第一条场次提升为默认场次。
        first_session.is_default = True
        db.commit()
        db.refresh(first_session)
        return first_session

    default_session = CheckInSession(
        meeting_id=meeting.id,
        title=DEFAULT_CHECK_IN_SESSION_TITLE,
        description="系统默认签到场次。",
        is_default=True,
        sort_order=0,
    )
    db.add(default_session)
    db.commit()
    db.refresh(default_session)
    return default_session


def clear_other_default_sessions(db: Session, session: CheckInSession) -> None:
    """清除同会议内其他签到场次的默认标记。

    入参：db 为数据库会话；session 为将成为默认场次的对象，均必填。
    返回值：None：直接修改同会议其他场次。
    异常：数据库更新失败时由 SQLAlchemy 抛出异常。
    """
    other_sessions = db.scalars(
        select(CheckInSession).where(
            CheckInSession.meeting_id == session.meeting_id,
            CheckInSession.id != session.id,
            CheckInSession.is_default.is_(True),
        )
    )
    for other_session in other_sessions:
        # 默认场次在同一会议中只允许一个，避免工作人员端兜底签到目标不确定。
        other_session.is_default = False


def create_check_in_session(
    db: Session,
    meeting: Meeting,
    title: str,
    description: str | None,
    starts_at: datetime | None,
    ends_at: datetime | None,
    is_default: bool,
) -> CheckInSession:
    """创建会议签到场次。

    入参：db 为数据库会话；meeting 为已授权会议；title 为场次名称；description 为可选说明；starts_at 与 ends_at 为可选时间；is_default 表示是否设为默认场次。
    返回值：CheckInSession：已持久化的新场次。
    异常：名称为空、结束时间早于开始时间、名称重复时抛出 CheckInSessionBusinessError；数据库失败时由 SQLAlchemy 抛出异常。
    """
    if starts_at and ends_at and ends_at <= starts_at:
        raise CheckInSessionBusinessError(422, "签到场次结束时间必须晚于开始时间。")
    max_sort_order = max((item.sort_order for item in list_check_in_sessions(db, meeting)), default=-1)
    session = CheckInSession(
        meeting_id=meeting.id,
        title=normalize_session_title(title),
        description=description.strip() if description else None,
        starts_at=starts_at,
        ends_at=ends_at,
        is_default=is_default,
        sort_order=max_sort_order + 1,
    )
    db.add(session)
    if is_default:
        clear_other_default_sessions(db, session)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise CheckInSessionBusinessError(409, "同一会议下签到场次名称不能重复。") from error
    db.refresh(session)
    return session


def update_check_in_session(
    db: Session,
    session: CheckInSession,
    updates: dict[str, object],
) -> CheckInSession:
    """更新会议签到场次。

    入参：db 为数据库会话；session 为待更新场次；updates 为仅包含请求显式传入字段的更新字典。
    返回值：CheckInSession：更新后的场次。
    异常：名称为空、结束时间早于开始时间、名称重复时抛出 CheckInSessionBusinessError；数据库失败时由 SQLAlchemy 抛出异常。
    """
    next_starts_at = updates.get("starts_at", session.starts_at)
    next_ends_at = updates.get("ends_at", session.ends_at)
    if next_starts_at and next_ends_at and next_ends_at <= next_starts_at:
        raise CheckInSessionBusinessError(422, "签到场次结束时间必须晚于开始时间。")
    if "title" in updates:
        session.title = normalize_session_title(str(updates["title"]))
    if "description" in updates:
        description = updates["description"]
        session.description = str(description).strip() if description else None
    if "starts_at" in updates:
        session.starts_at = updates["starts_at"]
    if "ends_at" in updates:
        session.ends_at = updates["ends_at"]
    if "is_default" in updates:
        session.is_default = bool(updates["is_default"])
        if session.is_default:
            clear_other_default_sessions(db, session)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise CheckInSessionBusinessError(409, "同一会议下签到场次名称不能重复。") from error
    db.refresh(session)
    return session


def delete_check_in_session(db: Session, meeting: Meeting, session: CheckInSession) -> None:
    """删除会议签到场次并维护默认场次兜底。

    入参：db 为数据库会话；meeting 为已授权会议；session 为待删除场次，均必填。
    返回值：None：删除成功后提交事务。
    异常：数据库删除失败时由 SQLAlchemy 抛出异常。
    """
    remaining_sessions = [item for item in list_check_in_sessions(db, meeting) if item.id != session.id]
    if remaining_sessions and (session.is_default or not any(item.is_default for item in remaining_sessions)):
        # 删除默认场次或历史异常数据缺少默认场次时，将剩余第一条场次设为默认。
        remaining_sessions[0].is_default = True
        clear_other_default_sessions(db, remaining_sessions[0])
    db.delete(session)
    db.commit()
