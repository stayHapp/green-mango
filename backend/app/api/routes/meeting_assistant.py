"""管理员维护与嘉宾读取会议助手配置的路由。"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentAdmin, CurrentGuest, DatabaseSession
from app.schemas.meeting_assistant import (
    ContactPerson,
    GuestMeetingAssistantFeatureResponse,
    MeetingAssistantFeatureKey,
    MeetingAssistantFeatureResponse,
    MeetingAssistantFeatureUpdate,
)
from app.schemas.weather import MeetingWeatherResponse
from app.services.admin_meetings import get_authorized_meeting
from app.services.guest_sessions import get_guest_meeting
from app.services.meeting_assistant import (
    get_meeting_assistant_feature,
    list_meeting_assistant_features,
    update_meeting_assistant_feature,
)
from app.services.weather import get_weather

admin_router = APIRouter(prefix="/admin/meetings")
guest_router = APIRouter(prefix="/guest/meetings")


@admin_router.get(
    "/{meeting_id}/assistant-features", response_model=list[MeetingAssistantFeatureResponse]
)
def get_admin_assistant_features(
    meeting_id: int, db: DatabaseSession, admin: CurrentAdmin
) -> list[MeetingAssistantFeatureResponse]:
    """获取管理员有权访问会议的五项完整会议助手配置。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：list[MeetingAssistantFeatureResponse]：包含草稿正文的五项配置。
    异常：会议不存在或管理员未授权时返回 404；身份无效时返回 401 或 403。
    """
    if get_authorized_meeting(db, admin, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return list_meeting_assistant_features(db, meeting_id)


@admin_router.patch(
    "/{meeting_id}/assistant-features/{feature_key}", response_model=MeetingAssistantFeatureResponse
)
def patch_admin_assistant_feature(
    meeting_id: int,
    feature_key: MeetingAssistantFeatureKey,
    payload: MeetingAssistantFeatureUpdate,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> MeetingAssistantFeatureResponse:
    """修改管理员有权访问会议的单项会议助手配置。

    入参：meeting_id 为会议 ID；feature_key 为固定功能标识；payload 为配置；db 与 admin 由 FastAPI 注入。
    返回值：MeetingAssistantFeatureResponse：保存后的完整配置。
    异常：会议不存在或未授权时返回 404；功能标识或字段不合法时返回 422。
    """
    if get_authorized_meeting(db, admin, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return update_meeting_assistant_feature(db, meeting_id, feature_key, payload)


@guest_router.get(
    "/{meeting_id}/assistant-features/{feature_key}",
    response_model=GuestMeetingAssistantFeatureResponse,
)
def get_guest_assistant_feature(
    meeting_id: int,
    feature_key: MeetingAssistantFeatureKey,
    db: DatabaseSession,
    guest: CurrentGuest,
) -> GuestMeetingAssistantFeatureResponse:
    """获取嘉宾所属会议的单项公开配置并隔离未发布正文。

    入参：meeting_id 为会议 ID；feature_key 为固定功能标识；db 与 guest 由 FastAPI 注入。
    返回值：GuestMeetingAssistantFeatureResponse：已发布正文或未发布提醒。
    异常：会议不存在、跨会议访问时返回 404；功能标识不合法时返回 422。
    """
    if get_guest_meeting(db, guest, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    feature = get_meeting_assistant_feature(db, meeting_id, feature_key)
    return GuestMeetingAssistantFeatureResponse(
        meeting_id=meeting_id,
        feature_key=feature_key,
        content=feature.content if feature.is_published else None,
        unpublished_message=feature.unpublished_message,
        is_published=feature.is_published,
        contacts=[ContactPerson(**item) for item in (feature.contacts or [])],
    )


@guest_router.get("/{meeting_id}/weather", response_model=MeetingWeatherResponse)
def get_guest_weather(meeting_id: int, db: DatabaseSession, guest: CurrentGuest) -> MeetingWeatherResponse:
    """获取当前嘉宾所属会议的真实天气数据。

    入参：meeting_id 为会议 ID；db 与 guest 由 FastAPI 注入。
    返回值：MeetingWeatherResponse：和风天气实况、七日预报或可展示的降级信息。
    异常：跨会议访问或天气功能未发布时返回 404。
    """
    meeting = get_guest_meeting(db, guest, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    feature = get_meeting_assistant_feature(db, meeting_id, "weather")
    if not feature.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="天气情况尚未发布。")
    return get_weather(
        meeting.location or "",
        meeting.navigation_longitude,
        meeting.navigation_latitude,
    )
