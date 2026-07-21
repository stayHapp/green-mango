"""会议助手默认配置、管理员维护和嘉宾草稿隔离 API 测试。"""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.meeting import MeetingAssistantFeature


def create_meeting(client: TestClient, db: Session, create_user, auth_headers, admin_username: str = "assistant-admin") -> tuple[int, dict[str, str]]:
    """通过真实管理员接口创建带默认会议助手配置的测试会议。

    入参：client 为测试客户端；db 为数据库会话；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数；admin_username 为唯一管理员账号，均必填。
    返回值：tuple[int, dict[str, str]]：新会议 ID 和管理员认证请求头。
    异常：接口创建失败时由测试断言报告，不主动转换异常。
    """
    admin = create_user(db, admin_username)
    headers = auth_headers(db, admin)
    response = client.post(
        "/api/admin/meetings",
        headers=headers,
        json={"title": "会议助手测试会议", "status": "published"},
    )
    assert response.status_code == 201
    return response.json()["id"], headers


def test_new_meeting_has_five_default_assistant_features(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证新会议在创建事务内生成顺序稳定的五项默认配置。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示默认配置数量、顺序和状态正确。
    异常：断言失败表示默认初始化行为不符合设计。
    """
    client, db = client_and_session
    meeting_id, headers = create_meeting(client, db, create_user, auth_headers)

    response = client.get(f"/api/admin/meetings/{meeting_id}/assistant-features", headers=headers)

    assert response.status_code == 200
    assert [item["feature_key"] for item in response.json()] == [
        "agenda",
        "manual",
        "weather",
        "route",
        "contact",
    ]
    assert all(item["is_published"] is False for item in response.json())
    assert db.query(MeetingAssistantFeature).filter_by(meeting_id=meeting_id).count() == 5


def test_admin_can_publish_feature_and_guest_cannot_read_unpublished_draft(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证管理员发布闭环及嘉宾在撤回后无法读取已保存草稿。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示发布内容可见且撤回后正文为 null。
    异常：断言失败表示发布状态或草稿隔离存在缺陷。
    """
    client, db = client_and_session
    meeting_id, admin_headers = create_meeting(client, db, create_user, auth_headers, "assistant-publisher")
    guest = Guest(
        meeting_id=meeting_id,
        name="会议助手嘉宾",
        phone="13910000001",
        qr_token="assistant-guest-token",
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    guest_headers = auth_headers(db, guest)
    payload = {
        "content": "请携带雨具。",
        "unpublished_message": "天气信息正在更新。",
        "is_published": True,
    }

    publish_response = client.patch(
        f"/api/admin/meetings/{meeting_id}/assistant-features/weather",
        headers=admin_headers,
        json=payload,
    )
    guest_published_response = client.get(
        f"/api/guest/meetings/{meeting_id}/assistant-features/weather", headers=guest_headers
    )

    assert publish_response.status_code == 200
    assert guest_published_response.status_code == 200
    assert guest_published_response.json()["content"] == "请携带雨具。"
    assert guest_published_response.json()["is_published"] is True

    payload["is_published"] = False
    withdraw_response = client.patch(
        f"/api/admin/meetings/{meeting_id}/assistant-features/weather",
        headers=admin_headers,
        json=payload,
    )
    guest_unpublished_response = client.get(
        f"/api/guest/meetings/{meeting_id}/assistant-features/weather", headers=guest_headers
    )

    assert withdraw_response.status_code == 200
    assert guest_unpublished_response.status_code == 200
    assert guest_unpublished_response.json() == {
        "meeting_id": meeting_id,
        "feature_key": "weather",
        "content": None,
        "unpublished_message": "天气信息正在更新。",
        "is_published": False,
        "contacts": [],
    }


def test_assistant_feature_rejects_unauthorized_access_and_invalid_input(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证管理员越权、嘉宾跨会议和非法功能配置均被拒绝。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示权限边界和请求字段限制生效。
    异常：断言失败表示接口授权或校验规则存在回归。
    """
    client, db = client_and_session
    meeting_id, owner_headers = create_meeting(client, db, create_user, auth_headers, "assistant-owner")
    visitor = create_user(db, "assistant-visitor")
    visitor_headers = auth_headers(db, visitor)
    guest = Guest(
        meeting_id=meeting_id,
        name="跨会议嘉宾",
        phone="13910000002",
        qr_token="assistant-cross-token",
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    guest_headers = auth_headers(db, guest)

    unauthorized_response = client.get(
        f"/api/admin/meetings/{meeting_id}/assistant-features", headers=visitor_headers
    )
    invalid_key_response = client.patch(
        f"/api/admin/meetings/{meeting_id}/assistant-features/unknown",
        headers=owner_headers,
        json={"content": "内容", "unpublished_message": "提醒", "is_published": False},
    )
    oversized_response = client.patch(
        f"/api/admin/meetings/{meeting_id}/assistant-features/agenda",
        headers=owner_headers,
        json={"content": "内容", "unpublished_message": "提" * 501, "is_published": False},
    )
    cross_meeting_response = client.get(
        f"/api/guest/meetings/{meeting_id + 1}/assistant-features/agenda", headers=guest_headers
    )

    assert unauthorized_response.status_code == 404
    assert invalid_key_response.status_code == 422
    assert oversized_response.status_code == 422
    assert cross_meeting_response.status_code == 404


def test_historical_meeting_missing_features_is_backfilled(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证迁移前历史会议首次读取时补齐缺少的默认配置。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示缺失配置补齐且已有内容不被覆盖。
    异常：断言失败表示历史数据兼容逻辑不正确。
    """
    client, db = client_and_session
    meeting_id, headers = create_meeting(client, db, create_user, auth_headers, "assistant-history")
    weather = db.scalar(
        select(MeetingAssistantFeature).where(
            MeetingAssistantFeature.meeting_id == meeting_id,
            MeetingAssistantFeature.feature_key == "weather",
        )
    )
    assert weather is not None
    weather.content = "保留的历史天气正文"
    db.query(MeetingAssistantFeature).filter(
        MeetingAssistantFeature.meeting_id == meeting_id,
        MeetingAssistantFeature.feature_key != "weather",
    ).delete(synchronize_session=False)
    db.commit()

    response = client.get(f"/api/admin/meetings/{meeting_id}/assistant-features", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 5
    weather_response = next(item for item in response.json() if item["feature_key"] == "weather")
    assert weather_response["content"] == "保留的历史天气正文"
