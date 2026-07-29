"""管理员签到统计与明细路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentAdmin, DatabaseSession
from app.schemas.admin_check_in import (
    AdminCheckInSettingsResponse,
    AdminCheckInSettingsUpdate,
    AdminCheckInSessionCreate,
    AdminCheckInSessionResponse,
    AdminCheckInSessionUpdate,
    AdminCheckInSummary,
)
from app.schemas.admin_resources import OperationResponse
from app.services.check_in_sessions import (
    CheckInSessionBusinessError,
    create_check_in_session,
    delete_check_in_session,
    get_check_in_session,
    get_check_in_mode,
    get_current_check_in_session,
    get_default_check_in_session,
    get_manual_default_session_id,
    list_check_in_sessions,
    update_check_in_settings,
    update_check_in_session,
)
from app.services.admin_check_ins import get_check_in_summary
from app.services.admin_meetings import get_authorized_meeting

router = APIRouter(prefix="/admin/meetings")


def load_admin_meeting_or_404(db: DatabaseSession, admin: CurrentAdmin, meeting_id: int):
    """读取管理员有权限访问的会议，不存在或越权时返回 404。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：Meeting：已授权会议对象。
    异常：会议不存在或未授权时抛出 404 HTTPException。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return meeting


def raise_session_business_error(error: CheckInSessionBusinessError) -> None:
    """将签到场次业务异常转换为 HTTP 异常。

    入参：error 为签到场次服务抛出的业务异常，必填。
    返回值：None：当前函数始终抛出 HTTPException。
    异常：按业务异常中的状态码抛出 HTTPException。
    """
    raise HTTPException(status_code=error.status_code, detail=error.message) from error


def build_check_in_settings_response(db: DatabaseSession, meeting) -> AdminCheckInSettingsResponse:
    """构建会议级签到规则响应。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：AdminCheckInSettingsResponse：包含规则、手动覆盖和当前有效场次。
    异常：数据库读写失败时由 SQLAlchemy 抛出异常。
    """
    current_session = get_current_check_in_session(db, meeting)
    return AdminCheckInSettingsResponse(
        mode=get_check_in_mode(db, meeting),
        manual_default_session_id=get_manual_default_session_id(meeting),
        effective_session_id=current_session.id,
        effective_session_title=current_session.title,
    )


@router.get("/{meeting_id}/check-in-settings", response_model=AdminCheckInSettingsResponse)
def get_admin_check_in_settings(
    meeting_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> AdminCheckInSettingsResponse:
    """获取管理员有权限查看的会议级签到规则。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：AdminCheckInSettingsResponse：当前签到规则和有效场次。
    异常：管理员身份无效时返回 401 或 403；会议不存在或未授权时返回 404。
    """
    meeting = load_admin_meeting_or_404(db, admin, meeting_id)
    return build_check_in_settings_response(db, meeting)


@router.patch("/{meeting_id}/check-in-settings", response_model=AdminCheckInSettingsResponse)
def update_admin_check_in_settings(
    meeting_id: int,
    payload: AdminCheckInSettingsUpdate,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> AdminCheckInSettingsResponse:
    """更新管理员有权限维护的会议级签到规则。

    入参：meeting_id 为会议 ID；payload 为签到规则更新数据；db 与 admin 由 FastAPI 注入。
    返回值：AdminCheckInSettingsResponse：保存后的签到规则和当前有效场次。
    异常：会议不存在返回 404；规则无效或手动默认场次不存在时返回业务错误。
    """
    meeting = load_admin_meeting_or_404(db, admin, meeting_id)
    try:
        update_check_in_settings(db, meeting, payload.mode, payload.manual_default_session_id)
    except CheckInSessionBusinessError as error:
        raise_session_business_error(error)
    return build_check_in_settings_response(db, meeting)


@router.get("/{meeting_id}/check-in-sessions", response_model=list[AdminCheckInSessionResponse])
def get_admin_check_in_sessions(
    meeting_id: int, db: DatabaseSession, admin: CurrentAdmin
) -> list[AdminCheckInSessionResponse]:
    """获取管理员有权限查看的会议签到场次。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：list[AdminCheckInSessionResponse]：会议下所有签到场次。
    异常：管理员身份无效时返回 401 或 403；会议不存在或未授权时返回 404。
    """
    meeting = load_admin_meeting_or_404(db, admin, meeting_id)
    get_current_check_in_session(db, meeting)
    return list_check_in_sessions(db, meeting)


@router.post(
    "/{meeting_id}/check-in-sessions",
    response_model=AdminCheckInSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_check_in_session(
    meeting_id: int,
    payload: AdminCheckInSessionCreate,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> AdminCheckInSessionResponse:
    """创建管理员有权限维护的会议签到场次。

    入参：meeting_id 为会议 ID；payload 为场次创建数据；db 与 admin 由 FastAPI 注入。
    返回值：AdminCheckInSessionResponse：创建后的签到场次。
    异常：会议不存在返回 404；名称重复或时间无效返回业务错误。
    """
    meeting = load_admin_meeting_or_404(db, admin, meeting_id)
    get_default_check_in_session(db, meeting)
    try:
        return create_check_in_session(
            db,
            meeting,
            payload.title,
            payload.description,
            payload.starts_at,
            payload.ends_at,
            payload.is_default,
        )
    except CheckInSessionBusinessError as error:
        raise_session_business_error(error)


@router.patch("/{meeting_id}/check-in-sessions/{session_id}", response_model=AdminCheckInSessionResponse)
def update_admin_check_in_session(
    meeting_id: int,
    session_id: int,
    payload: AdminCheckInSessionUpdate,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> AdminCheckInSessionResponse:
    """更新管理员有权限维护的会议签到场次。

    入参：meeting_id 为会议 ID；session_id 为签到场次 ID；payload 为可选更新字段；db 与 admin 由 FastAPI 注入。
    返回值：AdminCheckInSessionResponse：更新后的签到场次。
    异常：会议或场次不存在返回 404；名称重复或时间无效返回业务错误。
    """
    meeting = load_admin_meeting_or_404(db, admin, meeting_id)
    session = get_check_in_session(db, meeting, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签到场次不存在。")
    try:
        updated_session = update_check_in_session(
            db,
            session,
            payload.model_dump(exclude_unset=True),
        )
        if payload.is_default is True and get_check_in_mode(db, meeting) == "date":
            # 日期规则下管理员点击默认圆点表示手动覆盖当天自动选择。
            update_check_in_settings(db, meeting, "date", updated_session.id)
        return updated_session
    except CheckInSessionBusinessError as error:
        raise_session_business_error(error)


@router.delete("/{meeting_id}/check-in-sessions/{session_id}", response_model=OperationResponse)
def delete_admin_check_in_session(
    meeting_id: int,
    session_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> OperationResponse:
    """删除管理员有权限维护的会议签到场次。

    入参：meeting_id 为会议 ID；session_id 为签到场次 ID；db 与 admin 由 FastAPI 注入。
    返回值：OperationResponse：删除成功结果。
    异常：会议或场次不存在返回 404；管理员身份无效时返回 401 或 403。
    """
    meeting = load_admin_meeting_or_404(db, admin, meeting_id)
    session = get_check_in_session(db, meeting, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签到场次不存在。")
    deleted_manual_default = get_manual_default_session_id(meeting) == session.id
    delete_check_in_session(db, meeting, session)
    if deleted_manual_default and get_check_in_mode(db, meeting) == "date":
        # 删除手动覆盖场次后恢复日期自动选择，避免保留无效配置。
        update_check_in_settings(db, meeting, "date", None)
    return OperationResponse(success=True, message="签到场次已删除。")


@router.get("/{meeting_id}/check-ins", response_model=AdminCheckInSummary)
def get_admin_check_ins(
    meeting_id: int, db: DatabaseSession, admin: CurrentAdmin, session_id: int | None = None
) -> AdminCheckInSummary:
    """获取管理员有权限查看的会议签到统计、明细与相邻场次差异。

    入参：meeting_id 为会议 ID；session_id 为可选签到场次 ID；db 与 admin 由 FastAPI 注入。
    返回值：AdminCheckInSummary：指定场次的统计、记录和对比结果。
    异常：管理员身份无效时返回 401 或 403；会议或场次不存在时返回 404。
    """
    meeting = load_admin_meeting_or_404(db, admin, meeting_id)
    summary = get_check_in_summary(db, meeting, session_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="签到场次不存在。")
    return summary
