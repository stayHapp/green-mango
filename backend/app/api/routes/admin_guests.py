"""管理员嘉宾字段配置与嘉宾管理路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentAdmin, DatabaseSession
from app.models.meeting import Meeting
from app.schemas.guest import GuestCreate, GuestFieldReplaceRequest, GuestFieldResponse, GuestResponse
from app.services.admin_guests import create_guest, list_guest_fields, list_guests, replace_guest_fields
from app.services.admin_meetings import get_authorized_meeting

router = APIRouter(prefix="/admin/meetings")


def load_authorized_meeting_or_404(db: DatabaseSession, admin: CurrentAdmin, meeting_id: int) -> Meeting:
    """读取管理员已授权会议，不存在或越权时统一返回 404。

    入参：db 为数据库会话；admin 为已验证管理员；meeting_id 为会议 ID，均必填。
    返回值：Meeting：已授权的会议对象。
    异常：会议不存在或当前管理员未获授权时抛出 404 HTTPException。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return meeting


@router.get("/{meeting_id}/guest-fields", response_model=list[GuestFieldResponse])
def get_guest_fields(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> list[GuestFieldResponse]:
    """获取已授权会议的嘉宾字段配置。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：list[GuestFieldResponse]：按排序规则返回的嘉宾字段配置。
    异常：管理员身份无效时返回 401 或 403；会议不存在或未授权时返回 404。
    """
    return list_guest_fields(db, load_authorized_meeting_or_404(db, admin, meeting_id))


@router.put("/{meeting_id}/guest-fields", response_model=list[GuestFieldResponse])
def put_guest_fields(
    meeting_id: int, payload: GuestFieldReplaceRequest, db: DatabaseSession, admin: CurrentAdmin
) -> list[GuestFieldResponse]:
    """按稳定 key 增量保存已授权会议的嘉宾字段配置。

    入参：meeting_id 为会议 ID；payload 为字段配置；db 与 admin 由 FastAPI 注入。
    返回值：list[GuestFieldResponse]：保存后的完整字段配置。
    异常：管理员身份无效时返回 401 或 403；会议未授权时返回 404；删除含值字段或修改其类型时返回 422。
    """
    meeting = load_authorized_meeting_or_404(db, admin, meeting_id)
    try:
        return replace_guest_fields(db, meeting, payload.fields)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@router.get("/{meeting_id}/guests", response_model=list[GuestResponse])
def get_guests(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> list[GuestResponse]:
    """获取已授权会议的嘉宾列表。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：list[GuestResponse]：会议嘉宾列表。
    异常：管理员身份无效时返回 401 或 403；会议不存在或未授权时返回 404。
    """
    return list_guests(db, load_authorized_meeting_or_404(db, admin, meeting_id))


@router.post("/{meeting_id}/guests", response_model=GuestResponse, status_code=status.HTTP_201_CREATED)
def post_guest(meeting_id: int, payload: GuestCreate, db: DatabaseSession, admin: CurrentAdmin) -> GuestResponse:
    """在已授权会议中录入单个嘉宾。

    入参：meeting_id 为会议 ID；payload 为嘉宾固定字段；db 与 admin 由 FastAPI 注入。
    返回值：GuestResponse：新建嘉宾及其随机二维码 token。
    异常：管理员身份无效时返回 401 或 403；会议未授权时返回 404；输入无效时返回 422。
    """
    try:
        return create_guest(db, load_authorized_meeting_or_404(db, admin, meeting_id), payload)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
