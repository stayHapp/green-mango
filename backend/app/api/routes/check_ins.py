"""工作人员签到路由。"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentStaff, DatabaseSession
from app.models.guest import Guest
from app.schemas.check_in import (
    AlreadyCheckedInDetail,
    CheckInResponse,
    ManualCheckInRequest,
    ScanCheckInRequest,
    StaffGuestResponse,
)
from app.services.admin_resources import get_guest_registration_settings
from app.services.check_ins import (
    CheckInBusinessError,
    create_check_in,
    get_authorized_staff_meeting,
    get_guest_by_token,
    list_check_ins,
    search_guests_with_check_in_status,
)

router = APIRouter(prefix="/staff/meetings")


def normalize_utc_datetime(value: datetime) -> datetime:
    """恢复 SQLite 丢失的 UTC 时区信息。

    入参：value 为数据库读取的签到时间，必填。
    返回值：datetime：已有时区时保持原值，无时区时补为 UTC。
    异常：当前函数不主动抛出异常。
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def build_check_in_response(check_in) -> CheckInResponse:
    """把签到 ORM 对象转换为时区明确的接口响应。

    入参：check_in 为已持久化签到记录，必填。
    返回值：CheckInResponse：字段完整且签到时间按 UTC 表达的响应。
    异常：签到记录字段缺失时由属性访问抛出异常。
    """
    return CheckInResponse(
        id=check_in.id,
        meeting_id=check_in.meeting_id,
        guest_id=check_in.guest_id,
        staff_id=check_in.staff_id,
        method=check_in.method,
        checked_in_at=normalize_utc_datetime(check_in.checked_in_at),
    )


def build_already_checked_in_detail(error: CheckInBusinessError) -> dict[str, object] | str:
    """构建重复签到时返回给工作人员端的结构化错误明细。

    入参：error 为签到业务异常，必填；重复签到时包含已存在签到记录和嘉宾对象。
    返回值：dict[str, object] | str：上下文完整时返回可 JSON 序列化的结构化明细，否则回退为原始中文消息。
    异常：当前函数不主动抛出异常；缺少上下文时使用字符串保持兼容。
    """
    check_in = error.existing_check_in
    guest = error.guest
    if check_in is None or guest is None:
        return error.message
    staff = check_in.staff
    staff_name = (staff.display_name or staff.username) if staff else None
    detail = AlreadyCheckedInDetail(
        code="already_checked_in",
        message=error.message,
        guest_id=guest.id,
        guest_name=guest.name,
        phone=guest.phone,
        checked_in_at=normalize_utc_datetime(check_in.checked_in_at),
        method=check_in.method,
        staff_id=check_in.staff_id,
        staff_name=staff_name,
    )
    return detail.model_dump(mode="json")


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
        return build_check_in_response(create_check_in(db, meeting, staff, guest, method))
    except CheckInBusinessError as error:
        detail = (
            build_already_checked_in_detail(error)
            if error.status_code == status.HTTP_409_CONFLICT
            else error.message
        )
        raise HTTPException(status_code=error.status_code, detail=detail) from error


@router.post("/{meeting_id}/check-ins/scan", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def scan_check_in(
    meeting_id: int, payload: ScanCheckInRequest, db: DatabaseSession, staff: CurrentStaff
) -> CheckInResponse:
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
def manual_check_in(
    meeting_id: int, payload: ManualCheckInRequest, db: DatabaseSession, staff: CurrentStaff
) -> CheckInResponse:
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
    return [
        build_check_in_response(check_in)
        for check_in in list_check_ins(db, load_staff_meeting_or_404(db, staff, meeting_id))
    ]


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
    _, _, enabled_fixed_fields = get_guest_registration_settings(meeting)
    enabled_field_set = set(enabled_fixed_fields)
    return [
        StaffGuestResponse(
            id=guest.id,
            name=guest.name,
            phone=guest.phone,
            organization=guest.organization if "organization" in enabled_field_set else None,
            title=guest.title if "title" in enabled_field_set else None,
            tag=guest.tag if "tag" in enabled_field_set else None,
            seat=guest.seat if "seat" in enabled_field_set else None,
            is_active=guest.is_active,
            checked_in=check_in is not None,
            checked_in_at=normalize_utc_datetime(check_in.checked_in_at) if check_in else None,
            visible_fields=enabled_fixed_fields,
        )
        for guest, check_in in search_guests_with_check_in_status(db, meeting, query, enabled_fixed_fields)
    ]
