"""管理员 Excel 嘉宾导入、模板下载和签到导出路由。"""

from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.api.dependencies import CurrentAdmin, DatabaseSession
from app.models.meeting import Meeting
from app.schemas.admin_resources import GuestImportResponse
from app.services.admin_meetings import get_authorized_meeting
from app.services.excel_files import (
    build_check_in_export,
    build_guest_import_template,
    build_guest_status_export,
    read_import_rows,
)

router = APIRouter(prefix="/admin/meetings")
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def load_meeting_or_404(db: DatabaseSession, admin: CurrentAdmin, meeting_id: int) -> Meeting:
    """读取管理员已授权会议并隐藏越权资源。

    入参：db 为数据库会话；admin 为已验证管理员；meeting_id 为会议 ID，均必填。
    返回值：Meeting：当前管理员可管理的会议对象。
    异常：会议不存在或未授权时抛出 404 HTTPException。
    """
    meeting = get_authorized_meeting(db, admin, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在或无访问权限。")
    return meeting


def excel_response(content: bytes, filename: str) -> Response:
    """创建带 UTF-8 文件名的 XLSX 下载响应。

    入参：content 为完整 XLSX 字节；filename 为建议下载文件名，均必填。
    返回值：Response：设置正确媒体类型与 Content-Disposition 的下载响应。
    异常：文件名无法编码时由标准库抛出异常。
    """
    encoded_filename = quote(filename)
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/{meeting_id}/guests/import-template")
def get_guest_import_template(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> Response:
    """下载当前会议的嘉宾导入模板。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：Response：包含固定字段和会议动态字段的 XLSX 文件。
    异常：会议不存在或无访问权限时返回 404。
    """
    meeting = load_meeting_or_404(db, admin, meeting_id)
    return excel_response(build_guest_import_template(db, meeting), f"{meeting.title}-嘉宾导入模板.xlsx")


@router.post("/{meeting_id}/guests/import", response_model=GuestImportResponse)
async def post_guest_import(
    meeting_id: int,
    db: DatabaseSession,
    admin: CurrentAdmin,
    file: UploadFile = File(...),
) -> GuestImportResponse:
    """上传 XLSX 文件并逐行导入有效嘉宾。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入；file 为不超过 10MB 的 .xlsx 文件。
    返回值：GuestImportResponse：成功数量及错误行列表。
    异常：会议无权限返回 404；文件类型、大小、表头或内容不合法时返回 422。
    """
    meeting = load_meeting_or_404(db, admin, meeting_id)
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="仅支持 .xlsx 文件。")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Excel 文件不能超过 10MB。")
    try:
        from io import BytesIO

        return read_import_rows(db, meeting, BytesIO(content))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error


@router.get("/{meeting_id}/check-ins/export")
def get_check_in_export(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> Response:
    """导出当前会议完整嘉宾签到表。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：Response：包含已签到和未签到嘉宾的 XLSX 文件。
    异常：会议不存在或无访问权限时返回 404。
    """
    meeting = load_meeting_or_404(db, admin, meeting_id)
    return excel_response(build_check_in_export(db, meeting), f"{meeting.title}-签到明细.xlsx")


@router.get("/{meeting_id}/guests/export")
def get_guest_status_export(meeting_id: int, db: DatabaseSession, admin: CurrentAdmin) -> Response:
    """导出当前会议的嘉宾信息与管理状态表。

    入参：meeting_id 为会议 ID；db 与 admin 由 FastAPI 注入。
    返回值：Response：包含嘉宾信息、来源、管理状态和签到状态的 XLSX 文件。
    异常：会议不存在或无访问权限时返回 404。
    """
    meeting = load_meeting_or_404(db, admin, meeting_id)
    return excel_response(build_guest_status_export(db, meeting), f"{meeting.title}-嘉宾状态表.xlsx")
