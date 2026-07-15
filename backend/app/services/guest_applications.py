"""嘉宾自主报名与管理员审核业务服务。"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import GuestApplication
from app.models.guest import GuestField
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.guest import GuestCreate
from app.schemas.guest_application import GuestApplicationCreate
from app.services.admin_guests import create_guest


def get_open_meeting(db: Session, meeting_id: int) -> Meeting | None:
    """读取当前允许公开报名的会议。

    入参：db 为数据库会话；meeting_id 为会议 ID，必须为正整数。
    返回值：Meeting | None：会议已发布且报名开关开启时返回会议，否则返回 None。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.status != "published":
        return None
    if meeting.setting is None or not meeting.setting.registration_enabled:
        return None
    if meeting.end_time is not None:
        end_time = meeting.end_time
        # SQLite 可能返回无时区时间，比较前统一补充 UTC 时区。
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        if end_time <= datetime.now(timezone.utc):
            return None
    return meeting


def validate_application_values(
    db: Session,
    meeting: Meeting,
    values: dict[str, str | None],
) -> None:
    """校验公开报名提交的动态字段和值。

    入参：db 为数据库会话；meeting 为开放报名会议；values 为动态字段 key 到文本的映射。
    返回值：None：校验通过时不修改数据库。
    异常：包含隐藏字段、未知字段或缺少公开必填字段时抛出 ValueError。
    """
    fields = list(db.scalars(select(GuestField).where(GuestField.meeting_id == meeting.id)))
    visible_fields = {field.key: field for field in fields if field.visible_to_guest}
    unknown_keys = set(values) - set(visible_fields)
    if unknown_keys:
        raise ValueError(f"存在不可填写的嘉宾字段：{', '.join(sorted(unknown_keys))}。")
    missing_required = [
        field.label
        for field in visible_fields.values()
        if field.required and (not values.get(field.key) or not str(values[field.key]).strip())
    ]
    if missing_required:
        raise ValueError(f"缺少必填嘉宾字段：{', '.join(missing_required)}。")


def create_application(db: Session, meeting: Meeting, payload: GuestApplicationCreate) -> GuestApplication:
    """创建待审核的嘉宾报名申请。

    入参：db 为数据库会话；meeting 为开放报名会议；payload 为已校验报名数据，均必填。
    返回值：GuestApplication：已持久化且状态为 pending 的申请。
    异常：动态字段不合法或同一会议存在相同手机号待审核申请时抛出 ValueError。
    """
    validate_application_values(db, meeting, payload.values)
    duplicate = db.scalar(
        select(GuestApplication.id).where(
            GuestApplication.meeting_id == meeting.id,
            GuestApplication.phone == payload.phone,
            GuestApplication.status == "pending",
        )
    )
    if duplicate is not None:
        raise ValueError("该手机号已有待审核报名申请。")
    values = payload.model_dump(exclude={"values"})
    application = GuestApplication(meeting_id=meeting.id, values_json=payload.values, **values)
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_applications(db: Session, meeting: Meeting, status_filter: str | None) -> list[GuestApplication]:
    """查询会议报名申请，可按审核状态过滤。

    入参：db 为数据库会话；meeting 为已授权会议；status_filter 可为 pending、approved、rejected 或 None。
    返回值：list[GuestApplication]：按提交时间倒序排列的申请列表。
    异常：状态值不受支持时抛出 ValueError；数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    if status_filter not in {None, "pending", "approved", "rejected"}:
        raise ValueError("报名申请状态筛选值无效。")
    statement = select(GuestApplication).where(GuestApplication.meeting_id == meeting.id)
    if status_filter:
        statement = statement.where(GuestApplication.status == status_filter)
    return list(db.scalars(statement.order_by(GuestApplication.created_at.desc(), GuestApplication.id.desc())))


def review_application(
    db: Session,
    meeting: Meeting,
    application: GuestApplication,
    reviewer: User,
    target_status: str,
) -> GuestApplication:
    """批准或拒绝一条待审核报名申请。

    入参：db 为数据库会话；meeting 为已授权会议；application 为申请；reviewer 为审核管理员；target_status 为 approved 或 rejected。
    返回值：GuestApplication：带审核人、审核时间及可选 guest_id 的最新申请。
    异常：申请不属于会议、已审核或目标状态无效时抛出 ValueError；批准时嘉宾字段校验错误会向上抛出。
    使用示例：target_status 为 approved 时创建正式嘉宾及随机二维码，再把新嘉宾 ID 写回申请。
    """
    if application.meeting_id != meeting.id:
        raise ValueError("报名申请不属于当前会议。")
    if application.status != "pending":
        raise ValueError("该报名申请已完成审核。")
    if target_status not in {"approved", "rejected"}:
        raise ValueError("审核状态必须为 approved 或 rejected。")
    if target_status == "approved":
        guest = create_guest(
            db,
            meeting,
            GuestCreate(
                name=application.name,
                phone=application.phone,
                organization=application.organization,
                title=application.title,
                tag=application.tag,
                seat=application.seat,
                values=application.values_json,
            ),
        )
        application.guest_id = guest.id
    application.status = target_status
    application.reviewed_by_id = reviewer.id
    application.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(application)
    return application
