"""为公网领导演示环境创建可重复使用的测试数据。"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.guest import Guest
from app.models.meeting import Meeting
from app.services.meeting_assistant import ensure_meeting_assistant_features
from app.scripts.seed_dev import (
    DEMO_MEETING_TITLE as DEVELOPMENT_MEETING_TITLE,
    GUEST_PHONE,
    seed_development_data,
)

DEMO_MEETING_TITLE = "2026 年教育数字化创新研讨会"
DEMO_ASSISTANT_CONTENT = {
    "agenda": "7 月 18 日\n09:00-09:30 开幕致辞\n09:30-11:30 教育数字化主题报告\n14:00-16:30 分组研讨与案例分享",
    "manual": "请嘉宾提前 20 分钟到达会场，凭嘉宾二维码完成签到。会议期间请将手机调至静音状态。",
    "route": "会场位于未来教育中心 A 座报告厅。抵达园区后请从南门进入，沿现场指示牌前往一楼签到处。",
    "contact": "会务联系人：张老师\n联系电话：138 0000 0000\n服务时间：会议当天 08:00-18:00",
}


def ensure_demo_assistant_features(db: Session, meeting: Meeting) -> None:
    """为领导演示会议准备可直接浏览的会议服务。

    入参：db 为数据库会话；meeting 为已持久化的演示会议，均必填。
    返回值：None：发布日程、资料、路线和联系信息，保留天气当前发布状态。
    异常：会议助手配置创建或数据库写入失败时由 SQLAlchemy 抛出异常。
    """
    features = ensure_meeting_assistant_features(db, meeting.id)
    for feature in features:
        # 天气是否发布由管理员根据第三方服务配置决定，演示脚本不主动覆盖。
        if feature.feature_key == "weather":
            if not feature.content:
                feature.unpublished_message = "天气信息将在会前更新，请关注会议通知。"
            continue
        # 已由管理员维护的正文和发布状态必须保留，演示脚本只补充空白配置。
        if not feature.content:
            feature.content = DEMO_ASSISTANT_CONTENT[feature.feature_key]
            feature.is_published = True


def seed_demo_data(db: Session) -> Meeting:
    """创建或更新公网领导演示会议及会议服务内容。

    入参：db 为数据库会话，必须已完成 Alembic 迁移。
    返回值：Meeting：已提交的领导演示会议。
    异常：基础联调数据、会议助手或数据库写入失败时回滚并向上抛出异常。
    使用示例：执行 `python -m app.scripts.seed_demo` 可重复更新公网演示数据。
    """
    try:
        meeting = db.scalar(
            select(Meeting)
            .join(Guest, Guest.meeting_id == Meeting.id)
            .where(Guest.phone == GUEST_PHONE)
            .order_by(Meeting.id)
        )
        if meeting is None:
            meeting, _ = seed_development_data(db)
        if meeting.title == DEVELOPMENT_MEETING_TITLE:
            now = datetime.now(timezone.utc)
            meeting.title = DEMO_MEETING_TITLE
            meeting.description = "汇聚教育管理者、教研专家与一线教师，共同交流数字技术赋能教育教学的实践经验与创新方向。"
            meeting.location = "杭州市未来教育中心 A 座报告厅"
            meeting.start_time = now + timedelta(days=1)
            meeting.end_time = now + timedelta(days=30)
            meeting.status = "published"
        ensure_demo_assistant_features(db, meeting)
        db.commit()
        db.refresh(meeting)
        return meeting
    except Exception:
        db.rollback()
        raise


def main() -> None:
    """执行公网领导演示数据初始化并输出非敏感说明。

    入参：无；使用应用当前 `DATABASE_URL` 创建数据库会话。
    返回值：None：成功时输出演示会议 ID 和嘉宾登录资料。
    异常：数据表未迁移或写入失败时向上抛出异常并以非零状态退出。
    """
    with SessionLocal() as db:
        meeting = seed_demo_data(db)
    print(f"公网演示数据已就绪，会议 ID：{meeting.id}")
    print("嘉宾：李文博 / 13900000001")


if __name__ == "__main__":
    main()
