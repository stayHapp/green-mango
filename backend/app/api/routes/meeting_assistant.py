"""管理员维护与嘉宾读取会议助手配置的路由。"""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentAdmin, CurrentGuest, DatabaseSession
from app.models.meeting import Meeting, MeetingAssistantFeature
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
from app.services.meeting_materials import attachment_path, delete_stored_attachment, store_uploaded_attachment
from app.services.weather import get_weather

admin_router = APIRouter(prefix="/admin/meetings")
guest_router = APIRouter(prefix="/guest/meetings")
public_router = APIRouter(prefix="/meetings")


def get_public_meeting_or_404(db: DatabaseSession, meeting_id: int) -> Meeting:
    """读取允许通过公开入口访问的会议。

    入参：db 为数据库会话；meeting_id 为目标会议 ID，均必填。
    返回值：Meeting：状态为已发布或已结束的会议。
    异常：会议不存在或仍为草稿时抛出 404 HTTPException。
    """
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.status not in {"published", "ended"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议入口不存在或尚未发布。")
    return meeting


def build_feature_response(
    meeting_id: int,
    feature_key: MeetingAssistantFeatureKey,
    feature: MeetingAssistantFeature,
) -> GuestMeetingAssistantFeatureResponse:
    """构造对外会议服务响应并隔离全部未发布草稿。

    入参：meeting_id 为会议 ID；feature_key 为固定服务标识；feature 为数据库配置记录，均必填。
    返回值：GuestMeetingAssistantFeatureResponse：已发布内容或仅含提醒的未发布状态。
    异常：联系人历史数据结构不合法时由 Pydantic 抛出校验异常。
    """
    return GuestMeetingAssistantFeatureResponse(
        meeting_id=meeting_id,
        feature_key=feature_key,
        content=feature.content if feature.is_published else None,
        unpublished_message=feature.unpublished_message,
        is_published=feature.is_published,
        access_level=feature.access_level,
        # 联系人同样属于草稿内容，未发布时不得返回。
        contacts=[ContactPerson(**item) for item in (feature.contacts or [])] if feature.is_published else [],
        contact_qr_title=feature.contact_qr_title,
        contact_qr_original_filename=feature.contact_qr_original_filename if feature.is_published else None,
    )


def build_contact_qr_response(feature: MeetingAssistantFeature) -> FileResponse:
    """构造联系会务二维码图片响应。

    入参：feature 为联系会务功能配置，必填。
    返回值：FileResponse：二维码图片文件响应。
    异常：未配置图片、路径非法或文件不存在时抛出 404 HTTPException。
    """
    if not feature.contact_qr_storage_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="尚未上传会务二维码。")
    try:
        path = attachment_path(feature.contact_qr_storage_key)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会务二维码文件不存在。") from error
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会务二维码文件不存在。")
    return FileResponse(
        path,
        media_type=feature.contact_qr_content_type or "image/png",
        filename=feature.contact_qr_original_filename or "contact-qr.png",
    )


def require_contact_feature(feature: MeetingAssistantFeature) -> None:
    """确认当前会议服务配置属于联系会务。

    入参：feature 为会议服务配置，必填。
    返回值：None：联系会务配置允许继续处理。
    异常：非联系会务配置时抛出 404 HTTPException。
    """
    if feature.feature_key != "contact":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="联系会务配置不存在。")


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


@admin_router.post(
    "/{meeting_id}/assistant-features/contact/qr",
    response_model=MeetingAssistantFeatureResponse,
)
async def post_admin_contact_qr(
    meeting_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
    image: UploadFile = File(...),
) -> MeetingAssistantFeatureResponse:
    """上传或替换联系会务二维码图片。

    入参：meeting_id 为会议 ID；image 为管理员上传的图片文件；db 与 admin 由 FastAPI 注入。
    返回值：MeetingAssistantFeatureResponse：更新图片后的联系会务配置。
    异常：会议不存在或无权限返回 404；文件类型不合法时返回 422。
    """
    if get_authorized_meeting(db, admin, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    feature = get_meeting_assistant_feature(db, meeting_id, "contact")
    old_storage_key = feature.contact_qr_storage_key
    try:
        stored = await store_uploaded_attachment(image, meeting_id)
        if not stored.content_type.startswith("image/"):
            delete_stored_attachment(stored.storage_key)
            raise ValueError("请上传 PNG、JPG 或 JPEG 图片。")
        feature.contact_qr_original_filename = stored.original_filename
        feature.contact_qr_storage_key = stored.storage_key
        feature.contact_qr_content_type = stored.content_type
        feature.contact_qr_size_bytes = stored.size_bytes
        db.commit()
        db.refresh(feature)
        if old_storage_key and old_storage_key != feature.contact_qr_storage_key:
            delete_stored_attachment(old_storage_key)
        return feature
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@admin_router.delete(
    "/{meeting_id}/assistant-features/contact/qr",
    response_model=MeetingAssistantFeatureResponse,
)
def delete_admin_contact_qr(
    meeting_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> MeetingAssistantFeatureResponse:
    """删除联系会务二维码图片并保留标题和联系人配置。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：MeetingAssistantFeatureResponse：删除图片后的联系会务配置。
    异常：会议不存在或无权限返回 404。
    """
    if get_authorized_meeting(db, admin, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    feature = get_meeting_assistant_feature(db, meeting_id, "contact")
    old_storage_key = feature.contact_qr_storage_key
    feature.contact_qr_original_filename = None
    feature.contact_qr_storage_key = None
    feature.contact_qr_content_type = None
    feature.contact_qr_size_bytes = None
    db.commit()
    db.refresh(feature)
    delete_stored_attachment(old_storage_key)
    return feature


@admin_router.get("/{meeting_id}/assistant-features/contact/qr")
def get_admin_contact_qr(
    meeting_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> FileResponse:
    """读取管理员可预览的联系会务二维码图片。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：FileResponse：二维码图片文件响应。
    异常：会议无权限、未上传图片或文件缺失时返回 404。
    """
    if get_authorized_meeting(db, admin, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    feature = get_meeting_assistant_feature(db, meeting_id, "contact")
    return build_contact_qr_response(feature)


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
    return build_feature_response(meeting_id, feature_key, feature)


@guest_router.get("/{meeting_id}/assistant-features/contact/qr")
def get_guest_contact_qr(meeting_id: int, db: DatabaseSession, guest: CurrentGuest) -> FileResponse:
    """读取登录嘉宾可查看的联系会务二维码图片。

    入参：meeting_id 为会议 ID；db 与 guest 由 FastAPI 注入。
    返回值：FileResponse：二维码图片文件响应。
    异常：会议无权限、联系会务未发布或未上传图片时返回 404。
    """
    if get_guest_meeting(db, guest, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    feature = get_meeting_assistant_feature(db, meeting_id, "contact")
    if not feature.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="联系会务尚未发布。")
    return build_contact_qr_response(feature)


@public_router.get(
    "/{meeting_id}/assistant-features/{feature_key}",
    response_model=GuestMeetingAssistantFeatureResponse,
)
def get_public_assistant_feature(
    meeting_id: int,
    feature_key: MeetingAssistantFeatureKey,
    db: DatabaseSession,
) -> GuestMeetingAssistantFeatureResponse:
    """获取无需登录即可查看的单项会议服务配置。

    入参：meeting_id 为会议 ID；feature_key 为固定服务标识；db 由 FastAPI 注入。
    返回值：GuestMeetingAssistantFeatureResponse：公开服务的已发布正文或未发布提醒。
    异常：会议不可公开时返回 404；服务仅限登录嘉宾时返回 401；功能标识非法时返回 422。
    """
    get_public_meeting_or_404(db, meeting_id)
    feature = get_meeting_assistant_feature(db, meeting_id, feature_key)
    if feature.access_level != "public":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="该服务需要登录后查看。",
        )
    return build_feature_response(meeting_id, feature_key, feature)


@public_router.get("/{meeting_id}/assistant-features/contact/qr")
def get_public_contact_qr(meeting_id: int, db: DatabaseSession) -> FileResponse:
    """读取公开联系会务二维码图片。

    入参：meeting_id 为会议 ID；db 由 FastAPI 注入。
    返回值：FileResponse：二维码图片文件响应。
    异常：会议不可公开、服务仅限登录、未发布或未上传图片时返回 404/401。
    """
    get_public_meeting_or_404(db, meeting_id)
    feature = get_meeting_assistant_feature(db, meeting_id, "contact")
    if feature.access_level != "public":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="该服务需要登录后查看。")
    if not feature.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="联系会务尚未发布。")
    return build_contact_qr_response(feature)


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


@public_router.get("/{meeting_id}/weather", response_model=MeetingWeatherResponse)
def get_public_weather(meeting_id: int, db: DatabaseSession) -> MeetingWeatherResponse:
    """获取公开且已发布天气服务的真实天气数据。

    入参：meeting_id 为会议 ID；db 由 FastAPI 注入。
    返回值：MeetingWeatherResponse：和风天气实况、预报或降级信息。
    异常：会议不可公开时返回 404；天气仅限登录嘉宾时返回 401；功能未发布时返回 404。
    """
    meeting = get_public_meeting_or_404(db, meeting_id)
    feature = get_meeting_assistant_feature(db, meeting_id, "weather")
    if feature.access_level != "public":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="该服务需要登录后查看。",
        )
    if not feature.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="天气情况尚未发布。")
    return get_weather(
        meeting.location or "",
        meeting.navigation_longitude,
        meeting.navigation_latitude,
    )
