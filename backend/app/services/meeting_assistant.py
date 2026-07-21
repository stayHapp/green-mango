"""会议助手默认配置、管理员维护和嘉宾公开读取服务。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.meeting import MeetingAssistantFeature
from app.schemas.meeting_assistant import MeetingAssistantFeatureKey, MeetingAssistantFeatureUpdate

MEETING_ASSISTANT_DEFAULTS: tuple[tuple[MeetingAssistantFeatureKey, str], ...] = (
    ("agenda", "会议日程尚未发布，请稍后查看。"),
    ("manual", "会议手册尚未发布，请稍后查看。"),
    ("weather", "天气情况尚未发布，请稍后查看。"),
    ("route", "路线指引尚未发布，请稍后查看。"),
    ("contact", "联系我们尚未发布，请稍后查看。"),
)
MEETING_ASSISTANT_FEATURE_KEYS = tuple(item[0] for item in MEETING_ASSISTANT_DEFAULTS)


def ensure_meeting_assistant_features(db: Session, meeting_id: int) -> list[MeetingAssistantFeature]:
    """补齐会议缺少的固定会议助手配置并返回顺序稳定的五项记录。

    入参：db 为数据库会话；meeting_id 为已存在的会议 ID，均必填。
    返回值：list[MeetingAssistantFeature]：按固定入口顺序排列的五项配置。
    异常：会议不存在、外键约束或数据库写入失败时由 SQLAlchemy 抛出异常。
    """
    existing = list(
        db.scalars(
            select(MeetingAssistantFeature).where(MeetingAssistantFeature.meeting_id == meeting_id)
        )
    )
    by_key = {feature.feature_key: feature for feature in existing}
    for feature_key, unpublished_message in MEETING_ASSISTANT_DEFAULTS:
        if feature_key not in by_key:
            feature = MeetingAssistantFeature(
                meeting_id=meeting_id,
                feature_key=feature_key,
                unpublished_message=unpublished_message,
            )
            db.add(feature)
            by_key[feature_key] = feature
    db.flush()
    return [by_key[feature_key] for feature_key in MEETING_ASSISTANT_FEATURE_KEYS]


def list_meeting_assistant_features(db: Session, meeting_id: int) -> list[MeetingAssistantFeature]:
    """读取会议全部配置，并持久化历史会议缺失的默认项。

    入参：db 为数据库会话；meeting_id 为已通过权限校验的会议 ID，均必填。
    返回值：list[MeetingAssistantFeature]：固定顺序的五项完整管理员配置。
    异常：数据库读取、补齐或提交失败时由 SQLAlchemy 抛出异常。
    """
    features = ensure_meeting_assistant_features(db, meeting_id)
    db.commit()
    return features


def update_meeting_assistant_feature(
    db: Session,
    meeting_id: int,
    feature_key: MeetingAssistantFeatureKey,
    payload: MeetingAssistantFeatureUpdate,
) -> MeetingAssistantFeature:
    """全量更新单项会议助手可编辑字段。

    入参：db 为数据库会话；meeting_id 为会议 ID；feature_key 为固定功能标识；payload 为配置请求，均必填。
    返回值：MeetingAssistantFeature：提交并刷新的配置记录。
    异常：数据库读取或提交失败时由 SQLAlchemy 抛出异常。
    """
    features = ensure_meeting_assistant_features(db, meeting_id)
    feature = next(item for item in features if item.feature_key == feature_key)
    feature.content = payload.content
    feature.unpublished_message = payload.unpublished_message
    feature.is_published = payload.is_published
    if payload.contacts is not None:
        feature.contacts = [contact.model_dump() for contact in payload.contacts]
    db.commit()
    db.refresh(feature)
    return feature


def get_meeting_assistant_feature(
    db: Session, meeting_id: int, feature_key: MeetingAssistantFeatureKey
) -> MeetingAssistantFeature:
    """读取嘉宾访问的单项配置，并自动补齐历史会议默认项。

    入参：db 为数据库会话；meeting_id 为会议 ID；feature_key 为固定功能标识，均必填。
    返回值：MeetingAssistantFeature：目标功能的服务端配置，路由层负责隔离未发布正文。
    异常：数据库读取、补齐或提交失败时由 SQLAlchemy 抛出异常。
    """
    features = ensure_meeting_assistant_features(db, meeting_id)
    db.commit()
    return next(item for item in features if item.feature_key == feature_key)
