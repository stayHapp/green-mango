"""公开嘉宾报名与管理员审核路由。"""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentAdmin, DatabaseSession
from app.models.application import GuestApplication
from app.models.meeting import Meeting
from app.schemas.guest_application import (
    GuestApplicationCreate,
    GuestApplicationResponse,
    GuestApplicationReviewRequest,
)
from app.schemas.guest_session import PublicMeetingResponse
from app.services.admin_resources import get_login_fields
from app.services.admin_meetings import get_authorized_meeting
from app.services.guest_applications import create_application, get_open_meeting, list_applications, review_application

public_router = APIRouter(prefix="/meetings")
admin_router = APIRouter(prefix="/admin/meetings")


def get_public_meeting_or_404(db: DatabaseSession, meeting_id: int) -> Meeting:
    """读取可通过嘉宾入口公开展示的会议。

    入参：db 为数据库会话；meeting_id 为会议 ID，必须为正整数。
    返回值：Meeting：状态为 published 或 ended 的会议。
    异常：会议不存在或仍为草稿时抛出 404 HTTPException。
    """
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.status not in {"published", "ended"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议入口不存在或尚未发布。")
    return meeting


@public_router.get("/{meeting_id}", response_model=PublicMeetingResponse)
def get_public_meeting(meeting_id: int, db: DatabaseSession) -> PublicMeetingResponse:
    """获取嘉宾登录页所需的公开会议信息。

    入参：meeting_id 为会议 ID；db 由 FastAPI 注入。
    返回值：PublicMeetingResponse：会议基础信息、报名开关和当前嘉宾登录字段。
    异常：会议不存在或尚未发布时返回 404。
    """
    meeting = get_public_meeting_or_404(db, meeting_id)
    return PublicMeetingResponse(
        id=meeting.id,
        title=meeting.title,
        description=meeting.description,
        location=meeting.location,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        status=meeting.status,
        registration_enabled=bool(meeting.setting and meeting.setting.registration_enabled),
        guest_login_fields=get_login_fields(meeting),
    )


@public_router.post(
    "/{meeting_id}/guest-applications",
    response_model=GuestApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_guest_application(
    meeting_id: int,
    payload: GuestApplicationCreate,
    db: DatabaseSession,
) -> GuestApplicationResponse:
    """向已发布且开放报名的会议提交嘉宾申请。

    入参：meeting_id 为会议 ID；payload 为嘉宾资料；db 由 FastAPI 注入。
    返回值：GuestApplicationResponse：状态为 pending 的申请详情。
    异常：会议未开放报名返回 404；字段或重复申请无效返回 422。
    """
    meeting = get_open_meeting(db, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或未开放报名。")
    try:
        return create_application(db, meeting, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@admin_router.get("/{meeting_id}/guest-applications", response_model=list[GuestApplicationResponse])
def get_guest_applications(
    meeting_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
    status_filter: Literal["pending", "approved", "rejected"] | None = Query(default=None, alias="status"),
) -> list[GuestApplicationResponse]:
    """查询管理员有权管理会议的报名申请。

    入参：meeting_id 为会议 ID；status_filter 为可选审核状态；db 与 admin 由 FastAPI 注入。
    返回值：list[GuestApplicationResponse]：符合筛选条件的申请列表。
    异常：会议不存在或无权限时返回 404；筛选值无效时由 FastAPI 返回 422。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return list_applications(db, meeting, status_filter)


@admin_router.patch(
    "/{meeting_id}/guest-applications/{application_id}", response_model=GuestApplicationResponse
)
def patch_guest_application(
    meeting_id: int,
    application_id: int,
    payload: GuestApplicationReviewRequest,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> GuestApplicationResponse:
    """批准或拒绝一条待审核报名申请。

    入参：meeting_id、application_id 为资源 ID；payload 为审核结果；db 与 admin 由 FastAPI 注入。
    返回值：GuestApplicationResponse：审核后的申请，批准时包含正式嘉宾 ID。
    异常：会议或申请不存在返回 404；重复审核或字段无效返回 422。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    application = db.get(GuestApplication, application_id)
    if application is None or application.meeting_id != meeting.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报名申请不存在。")
    try:
        return review_application(db, meeting, application, admin, payload.status)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
