"""管理员工作人员管理与工作人员会议列表路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentAdmin, CurrentStaff, DatabaseSession
from app.schemas.staff import StaffCreate, StaffMeetingResponse, StaffResponse
from app.services.admin_meetings import get_authorized_meeting
from app.services.staff import create_or_authorize_staff, list_meeting_staff, list_staff_meetings

admin_router = APIRouter(prefix="/admin/meetings")
staff_router = APIRouter(prefix="/staff")


def load_authorized_meeting_or_404(db: DatabaseSession, admin: CurrentAdmin, meeting_id: int):
    """读取管理员已授权会议，不存在或越权时返回 404。

    入参：db 为数据库会话；admin 为已验证管理员；meeting_id 为会议 ID，均必填。
    返回值：Meeting：已授权会议对象。
    异常：会议不存在或未授权时抛出 404 HTTPException。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return meeting


@admin_router.post("/{meeting_id}/staff", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def post_staff(meeting_id: int, payload: StaffCreate, db: DatabaseSession, admin: CurrentAdmin) -> StaffResponse:
    """创建工作人员并授权其负责当前会议。

    入参：meeting_id 为会议 ID；payload 为工作人员账号信息；db 与 admin 由 FastAPI 注入。
    返回值：StaffResponse：创建或复用的工作人员信息。
    异常：管理员无权限时返回 404；账号冲突时返回 422。
    """
    try:
        return create_or_authorize_staff(db, load_authorized_meeting_or_404(db, admin, meeting_id), payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@admin_router.get("/{meeting_id}/staff", response_model=list[StaffResponse])
def get_meeting_staff(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> list[StaffResponse]:
    """获取当前会议已授权的工作人员列表。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：list[StaffResponse]：会议工作人员列表。
    异常：管理员无权限时返回 404。
    """
    return list_meeting_staff(db, load_authorized_meeting_or_404(db, admin, meeting_id))


@staff_router.get("/meetings", response_model=list[StaffMeetingResponse])
def get_staff_meetings(db: DatabaseSession, staff: CurrentStaff) -> list[StaffMeetingResponse]:
    """获取当前工作人员负责的会议列表。

    入参：db 为数据库会话；staff 为已验证工作人员，均由 FastAPI 注入。
    返回值：list[StaffMeetingResponse]：工作人员负责会议列表。
    异常：工作人员身份无效时返回 401 或 403。
    """
    return list_staff_meetings(db, staff)
