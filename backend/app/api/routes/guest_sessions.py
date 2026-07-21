"""嘉宾登录和嘉宾会议路由。"""

from datetime import timezone

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentGuest, DatabaseSession
from app.schemas.guest import GuestProfileResponse
from app.schemas.guest_session import GuestLoginRequest, GuestMeetingResponse, GuestQrResponse, GuestSessionResponse
from app.services.admin_guests import get_guest_values
from app.services.admin_resources import get_guest_display_fields
from app.services.guest_sessions import get_guest_meeting, list_guest_meetings, login_guest
from app.services.sessions import create_guest_session as issue_guest_session

router = APIRouter(prefix="/guest")


@router.post("/sessions", response_model=GuestSessionResponse)
def create_guest_session(payload: GuestLoginRequest, db: DatabaseSession) -> GuestSessionResponse:
    """按会议、姓名和手机号创建可过期、可撤销的嘉宾会话。

    入参：payload 为登录信息；db 为数据库会话，均必填。
    返回值：GuestSessionResponse：包含 Bearer token、过期时间和嘉宾基本信息。
    异常：匹配不到已启用嘉宾时返回 401。
    """
    guest = login_guest(db, payload.meeting_id, payload.name, payload.phone)
    if guest is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未找到匹配的嘉宾登录信息。")
    token, auth_session = issue_guest_session(db, guest)
    return GuestSessionResponse(
        access_token=token,
        expires_at=auth_session.expires_at,
        guest_id=guest.id,
        meeting_id=guest.meeting_id,
        name=guest.name,
    )


@router.get("/meetings", response_model=list[GuestMeetingResponse])
def get_my_meetings(db: DatabaseSession, guest: CurrentGuest) -> list[GuestMeetingResponse]:
    """获取当前嘉宾可访问的会议列表。

    入参：db 为数据库会话；guest 为已验证嘉宾，均由 FastAPI 注入。
    返回值：list[GuestMeetingResponse]：嘉宾会议列表。
    异常：嘉宾身份无效时返回 401。
    """
    return list_guest_meetings(db, guest)


@router.get("/meetings/{meeting_id}", response_model=GuestMeetingResponse)
def get_my_meeting(meeting_id: int, db: DatabaseSession, guest: CurrentGuest) -> GuestMeetingResponse:
    """获取当前嘉宾所属会议详情。

    入参：meeting_id 为会议 ID；db 与 guest 由 FastAPI 注入。
    返回值：GuestMeetingResponse：会议详情。
    异常：嘉宾身份无效时返回 401；跨会议访问时返回 404。
    """
    meeting = get_guest_meeting(db, guest, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return meeting


@router.get("/meetings/{meeting_id}/check-in-qr", response_model=GuestQrResponse)
def get_my_check_in_qr(meeting_id: int, db: DatabaseSession, guest: CurrentGuest) -> GuestQrResponse:
    """获取当前嘉宾在所属会议中的签到二维码 token。

    入参：meeting_id 为会议 ID；db 与 guest 由 FastAPI 注入。
    返回值：GuestQrResponse：不包含个人信息的二维码 token、过期时间和签到状态。
    异常：嘉宾身份无效时返回 401；跨会议访问时返回 404。
    """
    meeting = get_guest_meeting(db, guest, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    check_in = guest.check_in
    checked_in_at = check_in.checked_in_at if check_in else None
    # SQLite 会丢失 DateTime 的时区信息；应用统一按 utc_now 写入，因此响应前按 UTC 恢复。
    if checked_in_at is not None and checked_in_at.tzinfo is None:
        checked_in_at = checked_in_at.replace(tzinfo=timezone.utc)
    return GuestQrResponse(
        qr_token=guest.qr_token,
        expires_at=meeting.end_time,
        is_checked_in=check_in is not None,
        checked_in_at=checked_in_at,
    )


@router.get("/meetings/{meeting_id}/profile", response_model=GuestProfileResponse)
def get_my_profile(meeting_id: int, db: DatabaseSession, guest: CurrentGuest) -> GuestProfileResponse:
    """获取当前嘉宾在所属会议中的完整个人参会信息。

    入参：meeting_id 为会议 ID；db 与 guest 由 FastAPI 注入。
    返回值：GuestProfileResponse：嘉宾固定信息与动态字段值。
    异常：嘉宾无权访问目标会议时返回 404。
    """
    meeting = get_guest_meeting(db, guest, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return GuestProfileResponse(
        id=guest.id,
        meeting_id=guest.meeting_id,
        name=guest.name,
        phone=guest.phone,
        organization=guest.organization,
        title=guest.title,
        tag=guest.tag,
        seat=guest.seat,
        source=guest.source,
        qr_token=guest.qr_token,
        is_active=guest.is_active,
        created_at=guest.created_at,
        updated_at=guest.updated_at,
        values=get_guest_values(db, guest),
        visible_fields=get_guest_display_fields(meeting),
        field_labels={field.key: field.label for field in meeting.guest_fields},
    )
