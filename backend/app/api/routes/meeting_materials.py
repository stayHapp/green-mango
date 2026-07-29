"""会议资料多条目维护、公开读取与鉴权下载路由。"""

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentAdmin, CurrentGuest, DatabaseSession
from app.models.meeting import Meeting, MeetingAssistantFeature, MeetingMaterial
from app.schemas.meeting_assistant import MeetingMaterialResponse
from app.services.admin_meetings import get_authorized_meeting
from app.services.guest_sessions import get_guest_meeting
from app.services.meeting_assistant import get_meeting_assistant_feature
from app.services.meeting_materials import (
    attachment_path,
    create_meeting_material,
    delete_meeting_material,
    get_meeting_material,
    list_meeting_materials,
    store_uploaded_attachment,
    update_meeting_material,
    validate_material_text,
)

admin_router = APIRouter(prefix="/admin/meetings")
guest_router = APIRouter(prefix="/guest/meetings")
public_router = APIRouter(prefix="/meetings")


def get_public_meeting_or_404(db: DatabaseSession, meeting_id: int) -> Meeting:
    """读取允许通过公开入口访问的会议。

    入参：db 为数据库会话；meeting_id 为会议 ID，均必填。
    返回值：Meeting：已发布或已结束的会议。
    异常：会议不存在或仍为草稿时抛出 404 HTTPException。
    """
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.status not in {"published", "ended"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议入口不存在或尚未发布。")
    return meeting


def get_admin_meeting_or_404(
    db: DatabaseSession,
    admin: CurrentAdmin,
    meeting_id: int,
) -> Meeting:
    """读取管理员已授权会议并隐藏越权资源。

    入参：db 为数据库会话；admin 为当前管理员；meeting_id 为会议 ID，均必填。
    返回值：Meeting：当前管理员可维护的会议。
    异常：会议不存在或管理员无权访问时抛出 404 HTTPException。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return meeting


def get_material_or_404(
    db: DatabaseSession,
    meeting_id: int,
    material_id: int,
) -> MeetingMaterial:
    """读取当前会议下的资料并统一处理不存在或跨会议访问。

    入参：db 为数据库会话；meeting_id 为会议 ID；material_id 为资料 ID，均必填。
    返回值：MeetingMaterial：属于当前会议的资料。
    异常：资料不存在或不属于当前会议时抛出 404 HTTPException。
    """
    material = get_meeting_material(db, meeting_id, material_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议资料不存在。")
    return material


def require_published_manual(feature: MeetingAssistantFeature) -> None:
    """确认会议资料功能已经发布。

    入参：feature 为当前会议的 manual 功能配置，必填。
    返回值：None：已发布时允许调用方继续处理。
    异常：资料功能未发布时抛出 404，避免泄露草稿条目和附件。
    """
    if not feature.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议资料尚未发布。")


def build_attachment_response(material: MeetingMaterial) -> FileResponse:
    """构造保留原始文件名的附件下载响应。

    入参：material 为已通过访问权限校验且包含附件的资料。
    返回值：FileResponse：通过分块方式发送附件并建议使用原始文件名下载。
    异常：资料没有附件或磁盘文件缺失时抛出 404 HTTPException。
    """
    if not material.storage_key or not material.original_filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该资料没有可下载附件。")
    try:
        path = attachment_path(material.storage_key)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件文件不存在。") from error
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件文件不存在。")
    return FileResponse(
        path=path,
        media_type=material.content_type or "application/octet-stream",
        filename=material.original_filename,
    )


@admin_router.get("/{meeting_id}/materials", response_model=list[MeetingMaterialResponse])
def get_admin_materials(
    meeting_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> list[MeetingMaterial]:
    """获取管理员有权维护会议的全部资料。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：list[MeetingMaterial]：包含正文和附件元数据的完整资料列表。
    异常：会议不存在或管理员未授权时返回 404。
    """
    get_admin_meeting_or_404(db, admin, meeting_id)
    return list_meeting_materials(db, meeting_id)


@admin_router.post(
    "/{meeting_id}/materials",
    response_model=MeetingMaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_admin_material(
    meeting_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
    title: str = Form(...),
    content: str = Form(""),
    attachment: UploadFile | None = File(None),
) -> MeetingMaterial:
    """新增一条可含正文和附件的会议资料。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入；title 为必填标题；
    content 为可空正文；attachment 为可空且不超过配置大小的常用文档附件。
    返回值：MeetingMaterial：保存后的资料记录。
    异常：会议无权限返回 404；字段、附件格式或大小不合法时返回 422。
    """
    get_admin_meeting_or_404(db, admin, meeting_id)
    try:
        # 先校验文本，避免无效表单仍在磁盘生成附件。
        validate_material_text(title, content, attachment is not None)
        stored_attachment = (
            await store_uploaded_attachment(attachment, meeting_id) if attachment is not None else None
        )
        return create_meeting_material(db, meeting_id, title, content, stored_attachment)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@admin_router.patch(
    "/{meeting_id}/materials/{material_id}",
    response_model=MeetingMaterialResponse,
)
async def patch_admin_material(
    meeting_id: int,
    material_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
    title: str = Form(...),
    content: str = Form(""),
    remove_attachment: bool = Form(False),
    attachment: UploadFile | None = File(None),
) -> MeetingMaterial:
    """编辑会议资料并按需替换或删除附件。

    入参：meeting_id 和 material_id 标识目标资料；db 与 admin 由 FastAPI 注入；
    title、content 为完整新值；remove_attachment 表示删除旧附件；attachment 为可空新附件。
    返回值：MeetingMaterial：保存后的资料记录。
    异常：会议或资料不存在返回 404；字段、附件格式或大小不合法时返回 422。
    """
    get_admin_meeting_or_404(db, admin, meeting_id)
    material = get_material_or_404(db, meeting_id, material_id)
    try:
        has_attachment = attachment is not None or (material.storage_key is not None and not remove_attachment)
        validate_material_text(title, content, has_attachment)
        stored_attachment = (
            await store_uploaded_attachment(attachment, meeting_id) if attachment is not None else None
        )
        return update_meeting_material(
            db,
            material,
            title,
            content,
            stored_attachment,
            remove_attachment,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@admin_router.delete(
    "/{meeting_id}/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_admin_material(
    meeting_id: int,
    material_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> Response:
    """删除管理员有权维护的单条会议资料及其附件。

    入参：meeting_id 和 material_id 标识目标资料；db 与 admin 由 FastAPI 注入。
    返回值：Response：成功时返回 204 空响应。
    异常：会议或资料不存在时返回 404；数据库或文件删除失败时返回 500。
    """
    get_admin_meeting_or_404(db, admin, meeting_id)
    material = get_material_or_404(db, meeting_id, material_id)
    delete_meeting_material(db, material)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.get("/{meeting_id}/materials/{material_id}/download")
def get_admin_material_download(
    meeting_id: int,
    material_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
) -> FileResponse:
    """下载管理员有权维护的会议资料附件。

    入参：meeting_id 和 material_id 标识附件；db 与 admin 由 FastAPI 注入。
    返回值：FileResponse：保留原始文件名的附件。
    异常：会议、资料或附件不存在时返回 404。
    """
    get_admin_meeting_or_404(db, admin, meeting_id)
    return build_attachment_response(get_material_or_404(db, meeting_id, material_id))


@guest_router.get("/{meeting_id}/materials", response_model=list[MeetingMaterialResponse])
def get_guest_materials(
    meeting_id: int,
    db: DatabaseSession,
    guest: CurrentGuest,
) -> list[MeetingMaterial]:
    """获取当前嘉宾所属会议已发布的资料列表。

    入参：meeting_id 为会议 ID；db 与 guest 由 FastAPI 注入。
    返回值：list[MeetingMaterial]：按稳定顺序排列的已发布资料。
    异常：跨会议访问或资料未发布时返回 404。
    """
    if get_guest_meeting(db, guest, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    require_published_manual(get_meeting_assistant_feature(db, meeting_id, "manual"))
    return list_meeting_materials(db, meeting_id)


@guest_router.get("/{meeting_id}/materials/{material_id}/download")
def get_guest_material_download(
    meeting_id: int,
    material_id: int,
    db: DatabaseSession,
    guest: CurrentGuest,
) -> FileResponse:
    """下载当前嘉宾所属会议已发布的资料附件。

    入参：meeting_id 和 material_id 标识附件；db 与 guest 由 FastAPI 注入。
    返回值：FileResponse：保留原始文件名的附件。
    异常：跨会议访问、资料未发布或附件不存在时返回 404。
    """
    if get_guest_meeting(db, guest, meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    require_published_manual(get_meeting_assistant_feature(db, meeting_id, "manual"))
    return build_attachment_response(get_material_or_404(db, meeting_id, material_id))


@public_router.get("/{meeting_id}/materials", response_model=list[MeetingMaterialResponse])
def get_public_materials(
    meeting_id: int,
    db: DatabaseSession,
) -> list[MeetingMaterial]:
    """获取公开会议中公开且已发布的资料列表。

    入参：meeting_id 为会议 ID；db 由 FastAPI 注入。
    返回值：list[MeetingMaterial]：公开可见的资料列表。
    异常：会议不可公开或资料未发布返回 404；资料仅限嘉宾时返回 401。
    """
    get_public_meeting_or_404(db, meeting_id)
    feature = get_meeting_assistant_feature(db, meeting_id, "manual")
    if feature.access_level != "public":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="该服务需要登录后查看。")
    require_published_manual(feature)
    return list_meeting_materials(db, meeting_id)


@public_router.get("/{meeting_id}/materials/{material_id}/download")
def get_public_material_download(
    meeting_id: int,
    material_id: int,
    db: DatabaseSession,
) -> FileResponse:
    """下载公开会议中公开且已发布的资料附件。

    入参：meeting_id 和 material_id 标识附件；db 由 FastAPI 注入。
    返回值：FileResponse：保留原始文件名的附件。
    异常：会议或附件不存在、资料未发布返回 404；仅限嘉宾时返回 401。
    """
    get_public_meeting_or_404(db, meeting_id)
    feature = get_meeting_assistant_feature(db, meeting_id, "manual")
    if feature.access_level != "public":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="该服务需要登录后查看。")
    require_published_manual(feature)
    return build_attachment_response(get_material_or_404(db, meeting_id, material_id))
