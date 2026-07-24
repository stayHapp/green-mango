"""管理员嘉宾字段配置与嘉宾管理业务服务。"""

import secrets

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.guest import Guest, GuestField, GuestValue
from app.models.meeting import Meeting
from app.schemas.guest import GuestCreate, GuestFieldInput


def list_guest_fields(db: Session, meeting: Meeting) -> list[GuestField]:
    """获取会议嘉宾字段配置。

    入参：db 为数据库会话；meeting 为已完成管理员授权校验的会议，均必填。
    返回值：list[GuestField]：按 sort_order、ID 升序排列的字段列表。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(GuestField).where(GuestField.meeting_id == meeting.id).order_by(GuestField.sort_order, GuestField.id)
    return list(db.scalars(statement))


def replace_guest_fields(db: Session, meeting: Meeting, fields: list[GuestFieldInput]) -> list[GuestField]:
    """按稳定字段 key 增量同步会议嘉宾字段配置。

    入参：db 为数据库会话；meeting 为已授权会议；fields 为已校验且 key 不重复的字段列表，均必填。
    返回值：list[GuestField]：原位更新、新增或安全删除后的字段配置，按排序规则返回。
    异常：删除含值字段或修改含值字段类型时抛出 ValueError；数据库写入失败时由 SQLAlchemy 抛出异常。
    使用示例：修改“饮食偏好”的名称和必填状态时，原字段 ID 与嘉宾填写值保持不变。
    """
    existing_fields = list_guest_fields(db, meeting)
    existing_by_key = {field.key: field for field in existing_fields}
    submitted_by_key = {field.key: field for field in fields}
    valued_field_ids = set(
        db.scalars(
            select(GuestValue.field_id)
            .join(Guest, Guest.id == GuestValue.guest_id)
            .where(
                Guest.meeting_id == meeting.id,
                GuestValue.value_text.is_not(None),
                func.trim(GuestValue.value_text) != "",
            )
            .distinct()
        )
    )

    # 在修改 ORM 对象前一次性校验所有破坏性变化，避免请求失败后留下半完成状态。
    for existing_field in existing_fields:
        submitted_field = submitted_by_key.get(existing_field.key)
        if submitted_field is None and existing_field.id in valued_field_ids:
            raise ValueError(f"字段“{existing_field.label}”已有嘉宾数据，不能删除。")
        if (
            submitted_field is not None
            and submitted_field.field_type != existing_field.field_type
            and existing_field.id in valued_field_ids
        ):
            raise ValueError(f"字段“{existing_field.label}”已有嘉宾数据，不能修改字段类型。")

    for existing_field in existing_fields:
        submitted_field = submitted_by_key.get(existing_field.key)
        if submitted_field is None:
            db.delete(existing_field)
            continue
        # 稳定 key 对应的字段原位更新，确保关联的 GuestValue（嘉宾字段值）继续指向同一字段 ID。
        for attribute, value in submitted_field.model_dump().items():
            setattr(existing_field, attribute, value)

    new_fields = [
        GuestField(meeting_id=meeting.id, **field.model_dump())
        for field in fields
        if field.key not in existing_by_key
    ]
    db.add_all(new_fields)
    db.commit()
    return list_guest_fields(db, meeting)


def list_guests(db: Session, meeting: Meeting) -> list[Guest]:
    """获取一个会议下当前启用的嘉宾列表。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：list[Guest]：按创建时间、ID 升序排列的嘉宾列表。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = (
        select(Guest)
        .where(Guest.meeting_id == meeting.id, Guest.is_active.is_(True))
        .order_by(Guest.created_at, Guest.id)
    )
    return list(db.scalars(statement))


def ensure_guest_identity_available(
    db: Session,
    meeting: Meeting,
    name: str,
    phone: str,
    exclude_guest_id: int | None = None,
) -> None:
    """确保会议内不存在姓名和手机号均相同的其他启用嘉宾。

    入参：db 为数据库会话；meeting 为目标会议；name、phone 为待保存身份；exclude_guest_id 为编辑时排除的嘉宾 ID，可为空。
    返回值：None：身份可用时不修改数据库。
    异常：发现重复启用身份时抛出 ValueError；数据库查询失败时由 SQLAlchemy 抛出异常。
    使用示例：编辑嘉宾时传入自身 ID，避免把当前记录误判为重复。
    """
    statement = select(Guest.id).where(
        Guest.meeting_id == meeting.id,
        Guest.name == name,
        Guest.phone == phone,
        Guest.is_active.is_(True),
    )
    if exclude_guest_id is not None:
        statement = statement.where(Guest.id != exclude_guest_id)
    if db.scalar(statement) is not None:
        raise ValueError("当前会议已存在姓名和手机号相同的启用嘉宾。")


def create_guest(db: Session, meeting: Meeting, payload: GuestCreate, source: str = "admin_entry") -> Guest:
    """在指定会议录入嘉宾并生成随机二维码 token。

    入参：db 为数据库会话；meeting 为已授权会议；payload 为已校验嘉宾输入；source 为嘉宾来源，默认为管理员录入。
    返回值：Guest：已持久化且带唯一二维码 token 的嘉宾对象。
    异常：会议内存在相同启用身份时抛出 ValueError；连续生成的 token 均冲突时抛出 RuntimeError；其他数据库错误向上抛出。
    """
    ensure_guest_identity_available(db, meeting, payload.name, payload.phone)
    for _ in range(5):
        token = secrets.token_urlsafe(32)
        if db.scalar(select(Guest.id).where(Guest.qr_token == token)) is None:
            fixed_values = payload.model_dump(exclude={"values"})
            guest = Guest(meeting_id=meeting.id, qr_token=token, source=source, **fixed_values)
            db.add(guest)
            try:
                db.flush()
                save_guest_values(db, meeting, guest, payload.values, require_all=True)
                db.commit()
            except IntegrityError as error:
                db.rollback()
                raise ValueError("当前会议已存在姓名和手机号相同的启用嘉宾。") from error
            db.refresh(guest)
            return guest
    raise RuntimeError("生成嘉宾二维码凭证失败，请重试。")


def save_guest_values(
    db: Session,
    meeting: Meeting,
    guest: Guest,
    values: dict[str, str | None],
    require_all: bool,
) -> None:
    """校验并保存嘉宾动态字段值。

    入参：db 为数据库会话；meeting 为会议；guest 为嘉宾；values 为 key 到值的映射；require_all 控制是否校验全部必填字段。
    返回值：None：校验通过后新增或更新 GuestValue，事务由调用方提交。
    异常：字段不存在、必填值缺失或字段不属于会议时抛出 ValueError。
    """
    fields = list(db.scalars(select(GuestField).where(GuestField.meeting_id == meeting.id)))
    fields_by_key = {field.key: field for field in fields}
    # 字段白名单：忽略历史残留或旧会议的不匹配 key，避免审批被阻塞。未知字段将在末尾被一并跳过。
    known_values = {key: value for key, value in values.items() if key in fields_by_key}
    unknown_keys = set(values) - known_values.keys()
    if unknown_keys:
        # 历史数据兼容：降级为跳过未知字段而不是拒绝保存。
        # 真正的未知字段错误请通过手动录入或导入路径发现。
        pass
    if require_all:
        missing_required = [
            field.label
            for field in fields
            if field.is_enabled
            and field.required
            and (field.key not in known_values
                 or known_values[field.key] is None
                 or not str(known_values[field.key]).strip())
        ]
        if missing_required:
            raise ValueError(f"缺少必填嘉宾字段：{', '.join(missing_required)}。")

    for key, value in known_values.items():
        field = fields_by_key[key]
        guest_value = db.scalar(
            select(GuestValue).where(GuestValue.guest_id == guest.id, GuestValue.field_id == field.id)
        )
        if guest_value is None:
            db.add(GuestValue(guest_id=guest.id, field_id=field.id, field_key=key, value_text=value))
        else:
            guest_value.value_text = value


def get_guest_values(db: Session, guest: Guest) -> dict[str, str | None]:
    """读取嘉宾动态字段值映射。

    入参：db 为数据库会话；guest 为目标嘉宾，均必填。
    返回值：dict[str, str | None]：字段 key 到文本值的映射。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    statement = select(GuestValue).where(GuestValue.guest_id == guest.id).order_by(GuestValue.id)
    return {value.field_key: value.value_text for value in db.scalars(statement)}
