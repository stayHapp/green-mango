"""会议资料正文、附件存储与数据库维护服务。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.meeting import MeetingMaterial

ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".doc",
    ".docx",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".txt",
    ".xls",
    ".xlsx",
    ".zip",
}
UPLOAD_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True)
class StoredAttachment:
    """已完成本地写入的附件元数据。"""

    original_filename: str
    storage_key: str
    content_type: str
    size_bytes: int


def validate_material_text(title: str, content: str, has_attachment: bool) -> tuple[str, str]:
    """校验并清理会议资料标题与正文。

    入参：title 为必填资料标题；content 为可空正文；has_attachment 表示保存后是否仍有附件。
    返回值：tuple[str, str]：去除首尾空白后的标题和正文。
    异常：标题为空或超长、正文超长、正文和附件同时为空时抛出 ValueError。
    """
    normalized_title = title.strip()
    normalized_content = content.strip()
    if not normalized_title:
        raise ValueError("请填写资料标题。")
    if len(normalized_title) > 200:
        raise ValueError("资料标题不能超过 200 个字符。")
    if len(normalized_content) > 20_000:
        raise ValueError("资料内容不能超过 20,000 个字符。")
    if not normalized_content and not has_attachment:
        raise ValueError("资料内容和附件至少填写一项。")
    return normalized_title, normalized_content


def material_storage_root() -> Path:
    """获取并创建会议资料附件存储根目录。

    入参：无；读取应用的 material_storage_dir 配置。
    返回值：Path：已创建且规范化的绝对存储目录。
    异常：目录无法创建时由 pathlib 抛出 OSError。
    """
    root = Path(settings.material_storage_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def attachment_path(storage_key: str) -> Path:
    """将服务端存储键安全转换为附件绝对路径。

    入参：storage_key 为数据库保存的相对存储键，必填。
    返回值：Path：位于配置存储根目录内的附件路径。
    异常：存储键尝试越过根目录时抛出 ValueError。
    """
    root = material_storage_root()
    path = (root / storage_key).resolve()
    if root not in path.parents:
        raise ValueError("附件存储路径无效。")
    return path


async def store_uploaded_attachment(upload: UploadFile, meeting_id: int) -> StoredAttachment:
    """校验并分块保存管理员上传的单个会议资料附件。

    入参：upload 为必填上传文件；meeting_id 为正整数会议 ID。
    返回值：StoredAttachment：包含原文件名、随机存储键、媒体类型和字节数。
    异常：文件名、扩展名或大小不合法时抛出 ValueError；磁盘写入失败时抛出 OSError。
    """
    original_filename = Path(upload.filename or "").name.strip()
    suffix = Path(original_filename).suffix.lower()
    if not original_filename or suffix not in ALLOWED_ATTACHMENT_EXTENSIONS:
        supported = "、".join(sorted(extension.removeprefix(".") for extension in ALLOWED_ATTACHMENT_EXTENSIONS))
        raise ValueError(f"附件格式不支持，可上传：{supported}。")

    storage_key = f"{meeting_id}/{uuid4().hex}{suffix}"
    final_path = attachment_path(storage_key)
    temporary_path = final_path.with_suffix(f"{final_path.suffix}.uploading")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    size_bytes = 0
    try:
        with temporary_path.open("wb") as output:
            while chunk := await upload.read(UPLOAD_CHUNK_BYTES):
                size_bytes += len(chunk)
                if size_bytes > settings.material_max_file_bytes:
                    raise ValueError(
                        f"单个附件不能超过 {settings.material_max_file_bytes // 1024 // 1024}MB。"
                    )
                output.write(chunk)
        if size_bytes == 0:
            raise ValueError("不能上传空文件。")
        temporary_path.replace(final_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    return StoredAttachment(
        original_filename=original_filename[:255],
        storage_key=storage_key,
        content_type=(upload.content_type or "application/octet-stream")[:150],
        size_bytes=size_bytes,
    )


def delete_stored_attachment(storage_key: str | None) -> None:
    """删除资料记录对应的本地附件文件。

    入参：storage_key 为可空相对存储键；为空时不执行操作。
    返回值：None：文件存在时删除，不存在时保持幂等。
    异常：存储路径非法或文件系统拒绝删除时抛出异常。
    """
    if storage_key:
        attachment_path(storage_key).unlink(missing_ok=True)


def list_meeting_materials(db: Session, meeting_id: int) -> list[MeetingMaterial]:
    """按稳定顺序读取指定会议的全部资料。

    入参：db 为数据库会话；meeting_id 为已完成权限校验的会议 ID。
    返回值：list[MeetingMaterial]：按 sort_order 和主键升序排列的资料列表。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    return list(
        db.scalars(
            select(MeetingMaterial)
            .where(MeetingMaterial.meeting_id == meeting_id)
            .order_by(MeetingMaterial.sort_order, MeetingMaterial.id)
        )
    )


def get_meeting_material(db: Session, meeting_id: int, material_id: int) -> MeetingMaterial | None:
    """读取会议下的单条资料并防止跨会议访问。

    入参：db 为数据库会话；meeting_id 为会议 ID；material_id 为资料 ID，均必填。
    返回值：MeetingMaterial | None：匹配当前会议时返回资料，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    return db.scalar(
        select(MeetingMaterial).where(
            MeetingMaterial.id == material_id,
            MeetingMaterial.meeting_id == meeting_id,
        )
    )


def next_material_sort_order(db: Session, meeting_id: int) -> int:
    """计算新资料追加到列表末尾所需的排序值。

    入参：db 为数据库会话；meeting_id 为会议 ID，均必填。
    返回值：int：当前最大排序值加一；没有资料时返回零。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    current_max = db.scalar(
        select(func.max(MeetingMaterial.sort_order)).where(MeetingMaterial.meeting_id == meeting_id)
    )
    return (current_max + 1) if current_max is not None else 0


def create_meeting_material(
    db: Session,
    meeting_id: int,
    title: str,
    content: str,
    attachment: StoredAttachment | None,
) -> MeetingMaterial:
    """创建一条会议资料并提交数据库事务。

    入参：db 为数据库会话；meeting_id 为会议 ID；title 为标题；content 为正文；
    attachment 为可空附件元数据。
    返回值：MeetingMaterial：已提交并刷新的资料记录。
    异常：字段不合法时抛出 ValueError；数据库写入失败时清理新附件并继续抛出。
    """
    normalized_title, normalized_content = validate_material_text(title, content, attachment is not None)
    material = MeetingMaterial(
        meeting_id=meeting_id,
        title=normalized_title,
        content=normalized_content,
        original_filename=attachment.original_filename if attachment else None,
        storage_key=attachment.storage_key if attachment else None,
        content_type=attachment.content_type if attachment else None,
        size_bytes=attachment.size_bytes if attachment else None,
        sort_order=next_material_sort_order(db, meeting_id),
    )
    db.add(material)
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_stored_attachment(attachment.storage_key if attachment else None)
        raise
    db.refresh(material)
    return material


def update_meeting_material(
    db: Session,
    material: MeetingMaterial,
    title: str,
    content: str,
    attachment: StoredAttachment | None,
    remove_attachment: bool,
) -> MeetingMaterial:
    """更新会议资料正文并按需替换或移除附件。

    入参：db 为数据库会话；material 为目标资料；title 和 content 为新文本；
    attachment 为可空新附件；remove_attachment 表示未上传新文件时是否删除旧附件。
    返回值：MeetingMaterial：已提交并刷新的资料记录。
    异常：字段不合法时抛出 ValueError；数据库更新失败时删除尚未生效的新附件并继续抛出。
    """
    keeps_old_attachment = material.storage_key is not None and not remove_attachment and attachment is None
    normalized_title, normalized_content = validate_material_text(
        title,
        content,
        attachment is not None or keeps_old_attachment,
    )
    old_storage_key = material.storage_key
    material.title = normalized_title
    material.content = normalized_content
    if attachment is not None:
        material.original_filename = attachment.original_filename
        material.storage_key = attachment.storage_key
        material.content_type = attachment.content_type
        material.size_bytes = attachment.size_bytes
    elif remove_attachment:
        material.original_filename = None
        material.storage_key = None
        material.content_type = None
        material.size_bytes = None
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_stored_attachment(attachment.storage_key if attachment else None)
        raise
    db.refresh(material)
    # 新记录持久化成功后再清理旧附件，避免数据库回滚时丢失仍在引用的文件。
    if old_storage_key and old_storage_key != material.storage_key:
        delete_stored_attachment(old_storage_key)
    return material


def delete_meeting_material(db: Session, material: MeetingMaterial) -> None:
    """删除单条会议资料并清理对应附件。

    入参：db 为数据库会话；material 为待删除资料记录，均必填。
    返回值：None：数据库记录提交删除后清理附件。
    异常：数据库提交或磁盘删除失败时继续抛出异常。
    """
    storage_key = material.storage_key
    db.delete(material)
    db.commit()
    delete_stored_attachment(storage_key)
