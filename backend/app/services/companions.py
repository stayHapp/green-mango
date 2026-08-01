"""工作人员端同行人员登记与查询业务服务。"""

from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.check_in import CompanionCreate
from app.schemas.guest import GuestCreate
from app.services.admin_guests import create_guest
from app.services.check_ins import CheckInBusinessError, create_check_in


def create_companion(db: Session, meeting: Meeting, staff: User, payload: CompanionCreate) -> Guest:
    """为已报名主嘉宾登记一名同行人员，并自动标记该同行人员手动签到。

    入参：db 为数据库会话；meeting 为工作人员已授权会议；staff 为执行登记的工作人员；payload 为同行人员输入，均必填。
    返回值：Guest：已持久化且已完成手动签到的同行嘉宾记录，来源为 companion_registration（同行登记）。
    异常：主嘉宾不存在、不属于当前会议、已停用或本身是同行嘉宾时抛出 ValueError；同会议身份重复时同样抛出 ValueError；会议已结束导致签到失败时抛出 CheckInBusinessError。
    使用示例：路由校验工作人员权限后调用本函数，并把结果序列化为 CompanionResponse。
    """
    primary_guest = db.get(Guest, payload.companion_of_id)
    if primary_guest is None or primary_guest.meeting_id != meeting.id:
        raise ValueError("主嘉宾不存在或不属于当前会议。")
    if not primary_guest.is_active:
        raise ValueError("主嘉宾已停用，无法登记同行人员。")
    if primary_guest.companion_of_id is not None:
        raise ValueError("同行嘉宾不能再作为主嘉宾登记其他同行人员。")

    guest_payload = GuestCreate(**payload.model_dump(exclude={"companion_of_id", "companion_note"}))
    companion = create_guest(
        db,
        meeting,
        guest_payload,
        source="companion_registration",
        companion_of_id=primary_guest.id,
        companion_note=payload.companion_note,
    )
    # 登记成功后立即写入当前有效场次的手动签到，同行嘉宾直接进入已签到名单。
    create_check_in(db, meeting, staff, companion, "manual")
    return companion


def list_companions(
    db: Session,
    meeting: Meeting,
    guest_id: int | None = None,
) -> list[tuple[Guest, str | None]]:
    """查询会议内同行嘉宾及其所陪同的主嘉宾姓名。

    入参：db 为数据库会话；meeting 为已授权会议；guest_id 为可选主嘉宾 ID 过滤条件，可为空。
    返回值：list[tuple[Guest, str | None]]：同行嘉宾对象与主嘉宾姓名的组合，按创建时间升序。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    primary_alias = aliased(Guest)
    statement = (
        select(Guest, primary_alias.name)
        .join(primary_alias, primary_alias.id == Guest.companion_of_id)
        .where(
            Guest.meeting_id == meeting.id,
            Guest.companion_of_id.is_not(None),
            Guest.is_active.is_(True),
        )
        .order_by(Guest.created_at, Guest.id)
    )
    if guest_id is not None:
        statement = statement.where(Guest.companion_of_id == guest_id)
    return list(db.execute(statement).tuples())


def list_companion_counts(db: Session, meeting: Meeting) -> dict[int, int]:
    """统计会议内每位主嘉宾当前携带的启用同行人数。

    入参：db 为数据库会话；meeting 为已授权会议，均必填。
    返回值：dict[int, int]：主嘉宾 ID 到启用同行人数的映射，无同行数据时返回空字典。
    异常：数据库查询失败时由 SQLAlchemy 抛出异常。
    """
    rows = db.execute(
        select(Guest.companion_of_id, func.count(Guest.id))
        .where(
            Guest.meeting_id == meeting.id,
            Guest.companion_of_id.is_not(None),
            Guest.is_active.is_(True),
        )
        .group_by(Guest.companion_of_id)
    ).all()
    return {primary_id: count for primary_id, count in rows}
