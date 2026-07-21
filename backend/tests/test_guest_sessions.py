"""嘉宾登录与会话 API 测试。

覆盖场景：正常登录、会议查看、二维码获取、登录失败、跨会议访问拒绝等。
"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.meeting import Meeting
from app.models.user import User


def test_guest_normal_login_and_get_meetings(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证嘉宾正常登录并可获取会议列表。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示嘉宾端核心路径可用。
    异常：当前函数不主动抛出业务异常；断言失败表示登录或访问控制异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-guest-login")
    meeting = Meeting(title="嘉宾会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    guest = Guest(meeting_id=meeting.id, name="李文博", phone="13900000007", qr_token="guest-session-token")
    db.add(guest)
    db.commit()

    login_response = client.post("/api/guest/sessions", json={
        "meeting_id": meeting.id,
        "name": "李文博",
        "phone": "13900000007",
    })
    assert login_response.status_code == 200
    assert login_response.json()["guest_id"] == guest.id
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    meetings_response = client.get("/api/guest/meetings", headers=headers)
    assert meetings_response.status_code == 200
    assert len(meetings_response.json()) == 1
    assert meetings_response.json()[0]["id"] == meeting.id


def test_guest_can_view_meeting_detail_and_profile(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证嘉宾可查看会议详情与个人信息。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示嘉宾端资料接口可用。
    异常：当前函数不主动抛出业务异常；断言失败表示接口行为不符合预期。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-guest-detail")
    meeting = Meeting(title="嘉宾详情会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    guest = Guest(
        meeting_id=meeting.id,
        name="王敏",
        phone="13900000008",
        organization="知会教育",
        title="研究员",
        tag="主讲嘉宾",
        seat="A42",
        qr_token="detail-token",
    )
    db.add(guest)
    db.commit()

    login_response = client.post("/api/guest/sessions", json={
        "meeting_id": meeting.id,
        "name": "王敏",
        "phone": "13900000008",
    })
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    detail_response = client.get(f"/api/guest/meetings/{meeting.id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "嘉宾详情会议"

    profile_response = client.get(f"/api/guest/meetings/{meeting.id}/profile", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["name"] == "王敏"
    assert profile_response.json()["organization"] == "知会教育"


def test_guest_can_get_checkin_qr(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证嘉宾可获取签到二维码 token。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示嘉宾端二维码接口可用。
    异常：当前函数不主动抛出业务异常；断言失败表示二维码生成逻辑异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-guest-qr")
    meeting = Meeting(
        title="签到二维码会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    guest = Guest(meeting_id=meeting.id, name="张老师", phone="13900000009", qr_token="qr-token")
    db.add(guest)
    db.commit()

    login_response = client.post("/api/guest/sessions", json={
        "meeting_id": meeting.id,
        "name": "张老师",
        "phone": "13900000009",
    })
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    qr_response = client.get(f"/api/guest/meetings/{meeting.id}/check-in-qr", headers=headers)
    assert qr_response.status_code == 200
    assert qr_response.json()["qr_token"] == "qr-token"
    assert qr_response.json()["is_checked_in"] is False


def test_guest_login_failure_returns_401(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证嘉宾姓名或手机号不匹配时登录失败。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示登录校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示认证逻辑存在缺口。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-guest-fail")
    meeting = Meeting(title="登录失败会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    guest = Guest(meeting_id=meeting.id, name="赵敏", phone="13900000010", qr_token="fail-token")
    db.add(guest)
    db.commit()

    # 错误手机号
    response = client.post("/api/guest/sessions", json={
        "meeting_id": meeting.id,
        "name": "赵敏",
        "phone": "错误的手机号",
    })
    assert response.status_code == 401

    # 正确姓名但错误手机号
    response = client.post("/api/guest/sessions", json={
        "meeting_id": meeting.id,
        "name": "赵敏",
        "phone": "13900000099",
    })
    assert response.status_code == 401


def test_draft_meeting_guest_cannot_login(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证草稿会议中的嘉宾无法登录。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示草稿会议登录过滤生效。
    异常：当前函数不主动抛出业务异常；断言失败表示草稿会议嘉宾可越权登录。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-guest-draft")
    meeting = Meeting(title="草稿会议", created_by_id=admin.id, status="draft")
    db.add(meeting)
    db.flush()
    guest = Guest(meeting_id=meeting.id, name="草稿嘉宾", phone="13900000020", qr_token="draft-token")
    db.add(guest)
    db.commit()

    response = client.post("/api/guest/sessions", json={
        "meeting_id": meeting.id,
        "name": "草稿嘉宾",
        "phone": "13900000020",
    })
    assert response.status_code == 401


def test_inactive_guest_cannot_login(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证已停用嘉宾无法登录。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示停用嘉宾登录过滤生效。
    异常：当前函数不主动抛出业务异常；断言失败表示停用嘉宾可越权登录。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-guest-inactive")
    meeting = Meeting(title="停用嘉宾会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    guest = Guest(
        meeting_id=meeting.id,
        name="停用嘉宾",
        phone="13900000021",
        qr_token="inactive-token",
        is_active=False,
    )
    db.add(guest)
    db.commit()

    response = client.post("/api/guest/sessions", json={
        "meeting_id": meeting.id,
        "name": "停用嘉宾",
        "phone": "13900000021",
    })
    assert response.status_code == 401


def test_guest_cross_meeting_access_rejected(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证嘉宾无法访问不属于自己会议的详情。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示跨会议访问被拒绝。
    异常：当前函数不主动抛出业务异常；断言失败表示存在越权风险。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-guest-cross")
    first_meeting = Meeting(title="我的会议", created_by_id=admin.id, status="published")
    second_meeting = Meeting(title="其他会议", created_by_id=admin.id, status="published")
    db.add_all([first_meeting, second_meeting])
    db.flush()
    guest = Guest(meeting_id=first_meeting.id, name="孙老师", phone="13900000011", qr_token="cross-token")
    db.add(guest)
    db.commit()

    cross_access = client.get(f"/api/guest/meetings/{second_meeting.id}", headers=auth_headers(db, guest))
    assert cross_access.status_code == 404


def test_guest_unauthenticated_access_returns_401(client_and_session: tuple[TestClient, Session]) -> None:
    """验证未认证访问嘉宾接口返回 401。

    入参：client_and_session 为测试客户端和数据库会话夹具。
    返回值：None：断言通过表示身份校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示权限检查缺失。
    """
    client, db = client_and_session

    response = client.get("/api/guest/meetings")
    assert response.status_code == 401
