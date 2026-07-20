"""管理员维护嘉宾、工作人员、登录规则和会议管理员的补充路由。"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import CurrentAdmin, DatabaseSession
from app.models.access import StaffMeeting
from app.models.guest import Guest
from app.models.user import User
from app.schemas.admin_resources import (
    AdminAssignmentRequest,
    AdminResponse,
    GuestDisplayFieldsRequest,
    GuestDisplayFieldsResponse,
    GuestLoginFieldsResponse,
    OperationResponse,
    StaffUpdate,
)
from app.schemas.guest import (
    GuestLoginFieldsRequest,
    GuestProfileResponse,
    GuestQrGenerationResponse,
    GuestResponse,
    GuestUpdate,
)
from app.schemas.staff import StaffResponse
from app.services.admin_guests import get_guest_values
from app.services.admin_meetings import get_authorized_meeting
from app.services.admin_resources import (
    add_meeting_admin,
    deactivate_guest,
    get_guest_display_fields,
    get_login_fields,
    list_meeting_admins,
    regenerate_missing_guest_tokens,
    remove_meeting_admin,
    remove_staff_assignment,
    save_login_fields,
    save_guest_display_fields,
    update_guest,
    update_staff,
)

router = APIRouter(prefix="/admin/meetings")


def load_meeting(db: DatabaseSession, admin: CurrentAdmin, meeting_id: int):
    """读取管理员已授权会议。

    入参：db 为数据库会话；admin 为管理员；meeting_id 为会议 ID。
    返回值：Meeting：已授权会议对象。
    异常：会议不存在或未授权时抛出 404。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return meeting


def load_guest(db: DatabaseSession, meeting_id: int, guest_id: int) -> Guest:
    """读取属于指定会议的嘉宾。

    入参：db 为数据库会话；meeting_id 和 guest_id 分别为会议与嘉宾 ID。
    返回值：Guest：匹配嘉宾。
    异常：嘉宾不存在或不属于会议时抛出 404。
    """
    guest = db.get(Guest, guest_id)
    if guest is None or guest.meeting_id != meeting_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="嘉宾不存在。")
    return guest


def build_guest_profile(db: DatabaseSession, guest: Guest) -> GuestProfileResponse:
    """组装包含动态字段值的嘉宾响应。

    入参：db 为数据库会话；guest 为目标嘉宾。
    返回值：GuestProfileResponse：固定字段和动态值响应。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    return GuestProfileResponse(
        id=guest.id,
        meeting_id=guest.meeting_id,
        name=guest.name,
        phone=guest.phone,
        organization=guest.organization,
        title=guest.title,
        tag=guest.tag,
        seat=guest.seat,
        qr_token=guest.qr_token,
        is_active=guest.is_active,
        created_at=guest.created_at,
        updated_at=guest.updated_at,
        values=get_guest_values(db, guest),
    )


@router.get("/{meeting_id}/guests/{guest_id}", response_model=GuestProfileResponse)
def get_admin_guest(meeting_id: int, guest_id: int, db: DatabaseSession, admin: CurrentAdmin) -> GuestProfileResponse:
    """获取管理员有权限查看的嘉宾完整资料。

    入参：meeting_id、guest_id 为资源 ID；db 与 admin 由 FastAPI 注入。
    返回值：GuestProfileResponse：嘉宾固定信息与动态字段值。
    异常：会议或嘉宾不存在、无权限时返回 404。
    """
    load_meeting(db, admin, meeting_id)
    return build_guest_profile(db, load_guest(db, meeting_id, guest_id))


@router.patch("/{meeting_id}/guests/{guest_id}", response_model=GuestProfileResponse)
def patch_admin_guest(
    meeting_id: int, guest_id: int, payload: GuestUpdate, db: DatabaseSession, admin: CurrentAdmin
) -> GuestProfileResponse:
    """修改嘉宾固定资料、动态字段值或启用状态。

    入参：meeting_id、guest_id 为资源 ID；payload 为修改数据；db 与 admin 由 FastAPI 注入。
    返回值：GuestProfileResponse：修改后的完整嘉宾资料。
    异常：资源不存在返回 404；动态字段无效返回 422。
    """
    meeting = load_meeting(db, admin, meeting_id)
    guest = load_guest(db, meeting_id, guest_id)
    try:
        return build_guest_profile(db, update_guest(db, meeting, guest, payload))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@router.delete("/{meeting_id}/guests/{guest_id}", response_model=OperationResponse)
def delete_admin_guest(meeting_id: int, guest_id: int, db: DatabaseSession, admin: CurrentAdmin) -> OperationResponse:
    """软停用嘉宾并保留历史数据。

    入参：meeting_id、guest_id 为资源 ID；db 与 admin 由 FastAPI 注入。
    返回值：OperationResponse：停用成功信息。
    异常：资源不存在或无权限时返回 404。
    """
    meeting = load_meeting(db, admin, meeting_id)
    deactivate_guest(db, meeting, load_guest(db, meeting_id, guest_id))
    return OperationResponse(success=True, message="嘉宾已停用。")


@router.get("/{meeting_id}/guest-login-fields", response_model=GuestLoginFieldsResponse)
def get_guest_login_fields(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> GuestLoginFieldsResponse:
    """获取会议嘉宾登录字段配置。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：GuestLoginFieldsResponse：当前登录字段。
    异常：会议不存在或无权限时返回 404。
    """
    return GuestLoginFieldsResponse(fields=get_login_fields(load_meeting(db, admin, meeting_id)))


@router.put("/{meeting_id}/guest-login-fields", response_model=GuestLoginFieldsResponse)
def put_guest_login_fields(
    meeting_id: int, payload: GuestLoginFieldsRequest, db: DatabaseSession, admin: CurrentAdmin
) -> GuestLoginFieldsResponse:
    """保存 MVP 固定嘉宾登录字段配置。

    入参：meeting_id 为会议 ID；payload 为字段组合；db 与 admin 由 FastAPI 注入。
    返回值：GuestLoginFieldsResponse：保存后的字段组合。
    异常：字段组合无效返回 422；会议无权限返回 404。
    """
    fields = save_login_fields(db, load_meeting(db, admin, meeting_id), payload.fields)
    return GuestLoginFieldsResponse(fields=fields)


@router.get("/{meeting_id}/guest-display-fields", response_model=GuestDisplayFieldsResponse)
def get_guest_display_field_settings(
    meeting_id: int, db: DatabaseSession, admin: CurrentAdmin
) -> GuestDisplayFieldsResponse:
    """获取管理员已授权会议的嘉宾端呈现字段。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：GuestDisplayFieldsResponse：当前固定和动态呈现字段 key。
    异常：会议不存在或无权限时返回 404。
    """
    return GuestDisplayFieldsResponse(fields=get_guest_display_fields(load_meeting(db, admin, meeting_id)))


@router.put("/{meeting_id}/guest-display-fields", response_model=GuestDisplayFieldsResponse)
def put_guest_display_field_settings(
    meeting_id: int,
    payload: GuestDisplayFieldsRequest,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> GuestDisplayFieldsResponse:
    """保存管理员已授权会议的嘉宾端呈现字段。

    入参：meeting_id 为会议 ID；payload 为字段 key 列表；db 与 admin 由 FastAPI 注入。
    返回值：GuestDisplayFieldsResponse：规范化并保存后的呈现字段 key。
    异常：会议不存在或无权限时返回 404；字段 key 不属于当前会议时返回 422。
    """
    try:
        fields = save_guest_display_fields(db, load_meeting(db, admin, meeting_id), payload.fields)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    return GuestDisplayFieldsResponse(fields=fields)


@router.post("/{meeting_id}/guest-qrcodes/generate", response_model=GuestQrGenerationResponse)
def generate_guest_qrcodes(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> GuestQrGenerationResponse:
    """为会议嘉宾补齐二维码 token。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：GuestQrGenerationResponse：生成数量和已有数量。
    异常：会议不存在或无权限时返回 404。
    """
    generated_count, existing_count = regenerate_missing_guest_tokens(db, load_meeting(db, admin, meeting_id))
    return GuestQrGenerationResponse(generated_count=generated_count, existing_count=existing_count)


@router.patch("/{meeting_id}/staff/{staff_id}", response_model=StaffResponse)
def patch_meeting_staff(
    meeting_id: int, staff_id: int, payload: StaffUpdate, db: DatabaseSession, admin: CurrentAdmin
) -> StaffResponse:
    """修改当前会议工作人员资料、状态或密码。

    入参：meeting_id、staff_id 为资源 ID；payload 为修改数据；db 与 admin 由 FastAPI 注入。
    返回值：StaffResponse：修改后的工作人员。
    异常：会议无权限、工作人员未获授权返回 404；目标角色错误返回 422。
    """
    meeting = load_meeting(db, admin, meeting_id)
    assignment = db.scalar(
        select(StaffMeeting).where(StaffMeeting.meeting_id == meeting.id, StaffMeeting.user_id == staff_id)
    )
    staff = db.get(User, staff_id)
    if assignment is None or staff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工作人员授权不存在。")
    try:
        return update_staff(db, staff, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@router.delete("/{meeting_id}/staff/{staff_id}", response_model=OperationResponse)
def delete_meeting_staff(meeting_id: int, staff_id: int, db: DatabaseSession, admin: CurrentAdmin) -> OperationResponse:
    """解除工作人员当前会议授权。

    入参：meeting_id、staff_id 为资源 ID；db 与 admin 由 FastAPI 注入。
    返回值：OperationResponse：解除成功结果。
    异常：会议不存在或无权限时返回 404。
    """
    removed = remove_staff_assignment(db, load_meeting(db, admin, meeting_id), staff_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工作人员授权不存在。")
    return OperationResponse(success=True, message="工作人员会议授权已解除。")


@router.get("/{meeting_id}/admins", response_model=list[AdminResponse])
def get_meeting_admins(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> list[AdminResponse]:
    """获取会议管理员列表。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：list[AdminResponse]：已授权管理员列表。
    异常：会议不存在或无权限时返回 404。
    """
    return list_meeting_admins(db, load_meeting(db, admin, meeting_id))


@router.post("/{meeting_id}/admins", response_model=AdminResponse)
def post_meeting_admin(
    meeting_id: int, payload: AdminAssignmentRequest, db: DatabaseSession, admin: CurrentAdmin
) -> AdminResponse:
    """为会议添加已有管理员账号。

    入参：meeting_id 为会议 ID；payload 包含管理员账号；db 与 admin 由 FastAPI 注入。
    返回值：AdminResponse：被授权管理员。
    异常：账号不可用返回 422；会议无权限返回 404。
    """
    try:
        return add_meeting_admin(db, load_meeting(db, admin, meeting_id), payload.username)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@router.delete("/{meeting_id}/admins/{user_id}", response_model=OperationResponse)
def delete_meeting_admin(
    meeting_id: int, user_id: int, db: DatabaseSession, admin: CurrentAdmin
) -> OperationResponse:
    """移除非创建人的会议管理员授权。

    入参：meeting_id、user_id 为资源 ID；db 与 admin 由 FastAPI 注入。
    返回值：OperationResponse：移除成功结果。
    异常：创建人保护或授权不存在返回 422。
    """
    try:
        remove_meeting_admin(db, load_meeting(db, admin, meeting_id), user_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    return OperationResponse(success=True, message="会议管理员授权已移除。")
