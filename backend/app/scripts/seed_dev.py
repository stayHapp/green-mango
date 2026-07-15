"""为本地前后端联调创建可重复使用的最小演示数据。"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.access import MeetingAdmin, StaffMeeting
from app.models.guest import Guest
from app.models.meeting import Meeting, MeetingSetting
from app.models.user import User

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin-pass-123"
STAFF_USERNAME = "staff01"
STAFF_PASSWORD = "staff-pass-123"
GUEST_NAME = "李文博"
GUEST_PHONE = "13900000001"
DEMO_MEETING_TITLE = "前后端联调演示会议"


def ensure_user(
    db: Session,
    username: str,
    password: str,
    role: str,
    display_name: str,
    phone: str,
) -> User:
    """创建或重置一名本地联调用户。

    入参：db 为数据库会话；username、password、role、display_name、phone 为联调账号资料，均必填。
    返回值：User：已加入当前事务且具有主键的管理员或工作人员。
    异常：数据库查询、密码哈希或写入失败时向上抛出对应异常。
    """
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        user = User(username=username, password_hash="", role=role)
        db.add(user)
        db.flush()
    # 脚本仅在开发者主动执行时重置演示凭据，保证说明文档中的账号始终可用。
    user.password_hash = hash_password(password)
    user.role = role
    user.display_name = display_name
    user.phone = phone
    user.is_active = True
    return user


def ensure_meeting(db: Session, admin: User) -> Meeting:
    """创建或更新一场处于有效期内的公开联调会议。

    入参：db 为数据库会话；admin 为已创建的演示管理员，均必填。
    返回值：Meeting：已发布、允许报名并授权演示管理员的会议。
    异常：数据库查询或写入失败时由 SQLAlchemy 抛出异常。
    """
    meeting = db.scalar(select(Meeting).where(Meeting.title == DEMO_MEETING_TITLE))
    now = datetime.now(timezone.utc)
    if meeting is None:
        meeting = Meeting(title=DEMO_MEETING_TITLE, created_by_id=admin.id)
        db.add(meeting)
        db.flush()
    meeting.description = "用于验证管理员、工作人员和嘉宾真实 API 登录及签到流程。"
    meeting.location = "杭州市未来教育中心 A 座报告厅"
    meeting.start_time = now + timedelta(days=1)
    meeting.end_time = now + timedelta(days=30)
    meeting.status = "published"
    if meeting.setting is None:
        db.add(MeetingSetting(meeting_id=meeting.id, registration_enabled=True))
    admin_assignment = db.scalar(
        select(MeetingAdmin).where(MeetingAdmin.meeting_id == meeting.id, MeetingAdmin.user_id == admin.id)
    )
    if admin_assignment is None:
        db.add(MeetingAdmin(meeting_id=meeting.id, user_id=admin.id))
    return meeting


def ensure_staff_assignment(db: Session, meeting: Meeting, staff: User) -> None:
    """确保演示工作人员被授权负责联调会议。

    入参：db 为数据库会话；meeting 为演示会议；staff 为演示工作人员，均必填。
    返回值：None：缺少授权时加入当前事务，已有授权时不重复创建。
    异常：数据库查询或写入失败时由 SQLAlchemy 抛出异常。
    """
    assignment = db.scalar(
        select(StaffMeeting).where(StaffMeeting.meeting_id == meeting.id, StaffMeeting.user_id == staff.id)
    )
    if assignment is None:
        db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))


def ensure_guest(db: Session, meeting: Meeting) -> Guest:
    """创建或更新联调会议中的演示嘉宾。

    入参：db 为数据库会话；meeting 为演示会议，均必填。
    返回值：Guest：可通过姓名和手机号登录并展示二维码的嘉宾。
    异常：数据库查询或写入失败时由 SQLAlchemy 抛出异常。
    """
    guest = db.scalar(
        select(Guest).where(Guest.meeting_id == meeting.id, Guest.phone == GUEST_PHONE)
    )
    if guest is None:
        guest = Guest(
            meeting_id=meeting.id,
            name=GUEST_NAME,
            phone=GUEST_PHONE,
            qr_token=f"dev-guest-{meeting.id}-qr-token",
        )
        db.add(guest)
    guest.name = GUEST_NAME
    guest.organization = "省教育科学研究院"
    guest.title = "研究员"
    guest.tag = "主讲嘉宾"
    guest.seat = "A01"
    guest.is_active = True
    return guest


def seed_development_data(db: Session) -> tuple[Meeting, Guest]:
    """在一个事务中创建完整三端联调数据。

    入参：db 为数据库会话，必须已完成 Alembic 迁移。
    返回值：tuple[Meeting, Guest]：提交后的演示会议和嘉宾。
    异常：数据表未迁移、唯一约束冲突或提交失败时回滚并向上抛出异常。
    使用示例：执行 `python -m app.scripts.seed_dev` 可重复重置本地演示数据。
    """
    try:
        admin = ensure_user(db, ADMIN_USERNAME, ADMIN_PASSWORD, "admin", "联调管理员", "13800000001")
        staff = ensure_user(db, STAFF_USERNAME, STAFF_PASSWORD, "staff", "现场一组", "13700000001")
        meeting = ensure_meeting(db, admin)
        ensure_staff_assignment(db, meeting, staff)
        guest = ensure_guest(db, meeting)
        db.commit()
        db.refresh(meeting)
        db.refresh(guest)
        return meeting, guest
    except Exception:
        db.rollback()
        raise


def main() -> None:
    """执行本地联调数据初始化并输出非敏感使用说明。

    入参：无；使用应用当前 `DATABASE_URL` 创建数据库会话。
    返回值：None：成功时打印会议 ID 和演示账号，数据库保存相应数据。
    异常：数据库未迁移或写入失败时向上抛出异常并以非零状态退出。
    """
    with SessionLocal() as db:
        meeting, _ = seed_development_data(db)
    print(f"联调数据已就绪，会议 ID：{meeting.id}")
    print(f"管理员：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print(f"工作人员：{STAFF_USERNAME} / {STAFF_PASSWORD}")
    print(f"嘉宾：{GUEST_NAME} / {GUEST_PHONE}")


if __name__ == "__main__":
    main()
