"""嘉宾登录和嘉宾会议路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentGuest, DatabaseSession
from app.schemas.guest_session import GuestLoginRequest, GuestMeetingResponse, GuestQrResponse, GuestSessionResponse
from app.services.guest_sessions import get_guest_meeting, list_guest_meetings, login_guest

router = APIRouter(prefix="/guest")


@router.post("/sessions", response_model=GuestSessionResponse)
def create_guest_session(payload: GuestLoginRequest, db: DatabaseSession) -> GuestSessionResponse:
    """按会议、姓名和手机号创建开发期嘉宾会话结果。

    入参：payload 为登录信息；db 为数据库会话，均必填。
    返回值：GuestSessionResponse：包含后续开发期请求使用的 guest_id。
    异常：匹配不到已启用嘉宾时返回 401。
    """
    guest = login_guest(db, payload.meeting_id, payload.name, payload.phone)
    if guest is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未找到匹配的嘉宾登录信息。")
    return GuestSessionResponse(guest_id=guest.id, meeting_id=guest.meeting_id, name=guest.name)


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
    返回值：GuestQrResponse：不包含个人信息的二维码 token 与过期时间。
    异常：嘉宾身份无效时返回 401；跨会议访问时返回 404。
    """
    meeting = get_guest_meeting(db, guest, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return GuestQrResponse(qr_token=guest.qr_token, expires_at=meeting.end_time)
