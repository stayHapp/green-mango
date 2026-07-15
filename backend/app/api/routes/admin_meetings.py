"""管理员会议管理路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentAdmin, DatabaseSession
from app.schemas.meeting import MeetingCreate, MeetingResponse, MeetingUpdate
from app.services.admin_meetings import create_meeting, get_authorized_meeting, list_authorized_meetings, update_meeting

router = APIRouter(prefix="/admin/meetings")


@router.get("", response_model=list[MeetingResponse])
def list_meetings(db: DatabaseSession, admin: CurrentAdmin) -> list[MeetingResponse]:
    """获取当前管理员有权限管理的会议列表。

    入参：db 为当前请求数据库会话；admin 为已验证的管理员，均由 FastAPI 注入。
    返回值：list[MeetingResponse]：管理员被授权会议的响应列表。
    异常：管理员身份无效时返回 401 或 403；数据库查询失败时由框架返回服务器错误。
    """
    return list_authorized_meetings(db, admin)


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_admin_meeting(
    payload: MeetingCreate, db: DatabaseSession, admin: CurrentAdmin
) -> MeetingResponse:
    """以当前管理员身份创建一个会议。

    入参：payload 为经 Pydantic 校验的会议创建数据；db 与 admin 由 FastAPI 注入。
    返回值：MeetingResponse：创建成功的会议详情。
    异常：管理员身份无效时返回 401 或 403；请求字段不合法时返回 422；数据库写入失败时由框架返回服务器错误。
    """
    return create_meeting(db, admin, payload)


@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> MeetingResponse:
    """获取当前管理员有权限访问的会议详情。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：MeetingResponse：会议详情。
    异常：管理员身份无效时返回 401 或 403；会议不存在或未授权时返回 404。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingResponse)
def patch_meeting(
    meeting_id: int, payload: MeetingUpdate, db: DatabaseSession, admin: CurrentAdmin
) -> MeetingResponse:
    """修改当前管理员有权限管理的会议。

    入参：meeting_id 为会议 ID；payload 为待修改字段；db 与 admin 由 FastAPI 注入。
    返回值：MeetingResponse：修改后的会议详情。
    异常：管理员身份无效时返回 401 或 403；会议不存在或未授权时返回 404；时间范围无效时返回 422。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    try:
        return update_meeting(db, meeting, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
