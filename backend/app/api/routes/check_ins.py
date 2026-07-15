"""工作人员签到路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentStaff, DatabaseSession
from app.schemas.check_in import CheckInResponse, ManualCheckInRequest, ScanCheckInRequest, StaffGuestResponse
from app.services.check_ins import CheckInBusinessError, create_check_in, get_authorized_staff_meeting, get_guest_by_token, list_check_ins, search_guests_with_check_in_status
from app.models.guest import Guest

router = APIRouter(prefix="/staff/meetings")


def load_staff_meeting_or_404(db: DatabaseSession, staff: CurrentStaff, meeting_id: int):
    """读取工作人员已授权会议，不存在或越权时返回 404。

    入参：db 为数据库会话；staff 为已验证工作人员；meeting_id 为会议 ID，均必填。
    返回值：Meeting：已授权会议对象。
    异常：会议不存在或工作人员未获授权时抛出 404 HTTPException。
    """
    meeting = get_authorized_staff_meeting(db, staff, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无签到权限。")
    return meeting


def execute_check_in(db: DatabaseSession, meeting, staff: CurrentStaff, guest: Guest, method: str) -> CheckInResponse:
    """执行签到服务并转换签到业务错误为 HTTP 响应。

    入参：db 为数据库会话；meeting 为已授权会议；staff 为工作人员；guest 为嘉宾；method 为签到方式，均必填。
    返回值：CheckInResponse：新建签到记录。
    异常：签到业务规则不满足时抛出对应状态码的 HTTPException。
    """
    try:
        return create_check_in(db, meeting, staff, guest, method)
    except CheckInBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error


@router.post("/{meeting_id}/check-ins/scan", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def scan_check_in(meeting_id: int, payload: ScanCheckInRequest, db: DatabaseSession, staff: CurrentStaff) -> CheckInResponse:
    """使用嘉宾二维码 token 完成签到。

    入参：meeting_id 为会议 ID；payload 包含二维码 token；db 与 staff 由 FastAPI 注入。
    返回值：CheckInResponse：签到成功记录。
    异常：无会议权限返回 404；二维码无效返回 422；重复签到返回 409。
    """
    meeting = load_staff_meeting_or_404(db, staff, meeting_id)
    guest = get_guest_by_token(db, payload.qr_token)
    if guest is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="二维码无效或嘉宾不存在。")
    return execute_check_in(db, meeting, staff, guest, "scan")


@router.post("/{meeting_id}/check-ins/manual", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def manual_check_in(meeting_id: int, payload: ManualCheckInRequest, db: DatabaseSession, staff: CurrentStaff) -> CheckInResponse:
    """按嘉宾 ID 完成人工核验签到。

    入参：meeting_id 为会议 ID；payload 包含嘉宾 ID；db 与 staff 由 FastAPI 注入。
    返回值：CheckInResponse：签到成功记录。
    异常：无会议权限或嘉宾不存在时返回 404；重复或失效签到返回对应业务错误。
    """
    meeting = load_staff_meeting_or_404(db, staff, meeting_id)
    guest = db.get(Guest, payload.guest_id)
    if guest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="嘉宾不存在。")
    return execute_check_in(db, meeting, staff, guest, "manual")


@router.get("/{meeting_id}/check-ins", response_model=list[CheckInResponse])
def get_check_ins(meeting_id: int, db: DatabaseSession, staff: CurrentStaff) -> list[CheckInResponse]:
    """获取工作人员有权限查看的会议签到记录。

    入参：meeting_id 为会议 ID；db 与 staff 由 FastAPI 注入。
    返回值：list[CheckInResponse]：签到记录列表。
    异常：无会议权限时返回 404。
    """
    return list_check_ins(db, load_staff_meeting_or_404(db, staff, meeting_id))


@router.get("/{meeting_id}/guests", response_model=list[StaffGuestResponse])
def search_meeting_guests(
    meeting_id: int, db: DatabaseSession, staff: CurrentStaff, query: str = ""
) -> list[StaffGuestResponse]:
    """按姓名、手机号、单位或座位号搜索工作人员可核验的嘉宾。

    入参：meeting_id 为会议 ID；query 为可选关键词；db 与 staff 由 FastAPI 注入。
    返回值：list[StaffGuestResponse]：嘉宾基础信息与签到状态列表。
    异常：无会议权限时返回 404。
    """
    meeting = load_staff_meeting_or_404(db, staff, meeting_id)
    return [
        StaffGuestResponse(
            id=guest.id,
            name=guest.name,
            phone=guest.phone,
            organization=guest.organization,
            title=guest.title,
            tag=guest.tag,
            seat=guest.seat,
            is_active=guest.is_active,
            checked_in=check_in is not None,
            checked_in_at=check_in.checked_in_at if check_in else None,
        )
        for guest, check_in in search_guests_with_check_in_status(db, meeting, query)
    ]
