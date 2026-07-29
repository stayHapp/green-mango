"""工作人员签到 API 测试。

覆盖场景：扫码签到、手工签到、重复签到保护、会议过期签到、停用嘉宾签到、
无效二维码、跨会议嘉宾签到、嘉宾搜索、未授权工作人员等。
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.access import StaffMeeting
from app.models.guest import CheckIn, Guest
from app.models.meeting import CheckInSession, Meeting, MeetingSetting
from app.models.user import User
from app.services.check_in_sessions import get_current_check_in_session, get_default_check_in_session


def test_staff_can_scan_check_in(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证工作人员扫码签到成功。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示扫码签到核心路径可用。
    异常：当前函数不主动抛出业务异常；断言失败表示签到逻辑异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-scan")
    staff = create_user(db, "staff-scan", role="staff")
    meeting = Meeting(
        title="扫码签到会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(meeting_id=meeting.id, name="扫码嘉宾", phone="13900000030", qr_token="scan-token")
    db.add(guest)
    db.commit()

    response = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/scan",
        headers=auth_headers(db, staff),
        json={"qr_token": "scan-token"},
    )
    assert response.status_code == 201
    assert response.json()["method"] == "scan"
    assert response.json()["guest_id"] == guest.id
    assert response.json()["meeting_id"] == meeting.id


def test_staff_can_manual_check_in(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证工作人员手工签到成功。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示手工签到核心路径可用。
    异常：当前函数不主动抛出业务异常；断言失败表示签到逻辑异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-manual")
    staff = create_user(db, "staff-manual", role="staff")
    meeting = Meeting(
        title="手工签到会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(meeting_id=meeting.id, name="手工嘉宾", phone="13900000031", qr_token="manual-token")
    db.add(guest)
    db.commit()

    response = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/manual",
        headers=auth_headers(db, staff),
        json={"guest_id": guest.id},
    )
    assert response.status_code == 201
    assert response.json()["method"] == "manual"
    assert response.json()["guest_id"] == guest.id


def test_duplicate_scan_check_in_returns_409(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证重复扫码签到返回 409 冲突。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示签到唯一性约束生效。
    异常：当前函数不主动抛出业务异常；断言失败表示可能出现重复签到。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-dup-scan")
    staff = create_user(db, "staff-dup-scan", role="staff")
    meeting = Meeting(
        title="重复扫码会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(meeting_id=meeting.id, name="重复嘉宾", phone="13900000032", qr_token="dup-scan-token")
    db.add(guest)
    db.commit()
    headers = auth_headers(db, staff)

    # 第一次签到成功
    first = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/scan",
        headers=headers,
        json={"qr_token": "dup-scan-token"},
    )
    assert first.status_code == 201

    # 第二次重复签到
    second = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/scan",
        headers=headers,
        json={"qr_token": "dup-scan-token"},
    )
    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail["code"] == "already_checked_in"
    assert detail["guest_id"] == guest.id
    assert detail["guest_name"] == "重复嘉宾"
    assert detail["phone"] == "13900000032"
    assert detail["method"] == "scan"
    assert detail["staff_id"] == staff.id
    assert detail["staff_name"] == staff.username
    assert detail["checked_in_at"]


def test_duplicate_manual_check_in_returns_409(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证重复手工签到返回 409 冲突。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示手工签到唯一性约束生效。
    异常：当前函数不主动抛出业务异常；断言失败表示可能出现重复签到。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-dup-manual")
    staff = create_user(db, "staff-dup-manual", role="staff")
    meeting = Meeting(
        title="重复手工会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(meeting_id=meeting.id, name="手工重复嘉宾", phone="13900000033", qr_token="dup-manual-token")
    db.add(guest)
    db.commit()
    headers = auth_headers(db, staff)

    # 手工签到成功
    first = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/manual",
        headers=headers,
        json={"guest_id": guest.id},
    )
    assert first.status_code == 201

    # 再次手工签到
    second = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/manual",
        headers=headers,
        json={"guest_id": guest.id},
    )
    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail["code"] == "already_checked_in"
    assert detail["guest_id"] == guest.id
    assert detail["guest_name"] == "手工重复嘉宾"
    assert detail["method"] == "manual"
    assert detail["staff_id"] == staff.id
    assert detail["staff_name"] == staff.username


def test_expired_meeting_check_in_returns_422(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证会议结束后签到返回 422。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示会议过期校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示过期会议仍可签到。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-expired")
    staff = create_user(db, "staff-expired", role="staff")
    meeting = Meeting(
        title="已结束会议",
        created_by_id=admin.id,
        status="ended",
        end_time=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(meeting_id=meeting.id, name="过期嘉宾", phone="13900000034", qr_token="expired-token")
    db.add(guest)
    db.commit()

    response = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/scan",
        headers=auth_headers(db, staff),
        json={"qr_token": "expired-token"},
    )
    assert response.status_code == 422


def test_inactive_guest_check_in_returns_422(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证已停用嘉宾签到返回 422。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示停用嘉宾校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示停用嘉宾仍可签到。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-inactive-guest")
    staff = create_user(db, "staff-inactive-guest", role="staff")
    meeting = Meeting(
        title="停用嘉宾签到会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(
        meeting_id=meeting.id,
        name="停用嘉宾",
        phone="13900000035",
        qr_token="inactive-guest-token",
        is_active=False,
    )
    db.add(guest)
    db.commit()

    response = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/scan",
        headers=auth_headers(db, staff),
        json={"qr_token": "inactive-guest-token"},
    )
    assert response.status_code == 422


def test_invalid_qr_token_returns_422(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证无效二维码 token 返回 422。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示二维码校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示无效二维码可签到。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-invalid-qr")
    staff = create_user(db, "staff-invalid-qr", role="staff")
    meeting = Meeting(
        title="无效二维码会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    db.commit()

    response = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/scan",
        headers=auth_headers(db, staff),
        json={"qr_token": "nonexistent-token"},
    )
    assert response.status_code == 422


def test_cross_meeting_guest_check_in_returns_422(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证跨会议嘉宾签到返回 422。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示嘉宾归属校验生效。
    异常：当前函数不主动抛出业务异常；断言失败表示跨会议签到可能成功。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-cross-checkin")
    staff = create_user(db, "staff-cross-checkin", role="staff")
    active_meeting = Meeting(
        title="进行中会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    other_meeting = Meeting(
        title="其他会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add_all([active_meeting, other_meeting])
    db.flush()
    db.add(StaffMeeting(meeting_id=active_meeting.id, user_id=staff.id))
    guest = Guest(meeting_id=other_meeting.id, name="跨会嘉宾", phone="13900000036", qr_token="cross-checkin-token")
    db.add(guest)
    db.commit()

    response = client.post(
        f"/api/staff/meetings/{active_meeting.id}/check-ins/scan",
        headers=auth_headers(db, staff),
        json={"qr_token": "cross-checkin-token"},
    )
    assert response.status_code == 422


def test_staff_can_search_guests_with_check_in_status(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证工作人员可搜索嘉宾并查看签到状态。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示搜索功能与签到状态返回正确。
    异常：当前函数不主动抛出业务异常；断言失败表示搜索或状态数据异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-search-checkin")
    staff = create_user(db, "staff-search-checkin", role="staff")
    meeting = Meeting(
        title="搜索签到会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(
        meeting_id=meeting.id,
        name="陈老师",
        phone="13900000037",
        organization="知会学校",
        seat="A12",
        qr_token="search-checkin-token",
    )
    db.add(guest)
    db.flush()
    default_session = get_default_check_in_session(db, meeting)
    db.add(CheckIn(meeting_id=meeting.id, session_id=default_session.id, guest_id=guest.id, staff_id=staff.id, method="scan"))
    db.commit()

    response = client.get(
        f"/api/staff/meetings/{meeting.id}/guests?query=A12",
        headers=auth_headers(db, staff),
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "陈老师"
    assert response.json()[0]["checked_in"] is True
    assert "seat" in response.json()[0]["visible_fields"]
    assert response.json()[0]["seat"] == "A12"


def test_staff_guest_search_hides_disabled_seat_field(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证后台未启用座位号时工作人员端不展示也不按座位号搜索。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示工作人员端字段显隐遵循会议配置。
    异常：当前函数不主动抛出业务异常；断言失败表示座位号可能在关闭后泄露。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-hidden-seat")
    staff = create_user(db, "staff-hidden-seat", role="staff")
    meeting = Meeting(
        title="隐藏座位会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    db.add(
        MeetingSetting(
            meeting_id=meeting.id,
            settings_json={
                "guest_enabled_fixed_fields": ["name", "phone", "organization", "title", "tag"],
            },
        )
    )
    db.add(
        Guest(
            meeting_id=meeting.id,
            name="隐藏座位嘉宾",
            phone="13900000041",
            organization="知会学院",
            seat="B18",
            qr_token="hidden-seat-token",
        )
    )
    db.commit()

    by_name = client.get(
        f"/api/staff/meetings/{meeting.id}/guests?query=隐藏座位嘉宾",
        headers=auth_headers(db, staff),
    )
    assert by_name.status_code == 200
    assert len(by_name.json()) == 1
    assert by_name.json()[0]["seat"] is None
    assert "seat" not in by_name.json()[0]["visible_fields"]

    by_seat = client.get(
        f"/api/staff/meetings/{meeting.id}/guests?query=B18",
        headers=auth_headers(db, staff),
    )
    assert by_seat.status_code == 200
    assert by_seat.json() == []


def test_unauthorized_staff_cannot_check_in(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证未授权工作人员无法签到。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示未授权工作人员签到被拒绝。
    异常：当前函数不主动抛出业务异常；断言失败表示存在越权风险。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-unauth-staff")
    staff = create_user(db, "staff-unauth", role="staff")
    other_staff = create_user(db, "staff-other-unauth", role="staff")
    meeting = Meeting(
        title="未授权签到会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    # 只授权 staff，未授权 other_staff
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(meeting_id=meeting.id, name="未授权嘉宾", phone="13900000038", qr_token="unauth-token")
    db.add(guest)
    db.commit()

    # 未授权的工作人员尝试签到
    response = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/scan",
        headers=auth_headers(db, other_staff),
        json={"qr_token": "unauth-token"},
    )
    assert response.status_code == 404


def test_staff_can_list_check_in_records(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证工作人员可查看签到记录。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示签到记录查询可用。
    异常：当前函数不主动抛出业务异常；断言失败表示签到记录查询异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-records")
    staff = create_user(db, "staff-records", role="staff")
    meeting = Meeting(
        title="签到记录会议",
        created_by_id=admin.id,
        status="published",
        end_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    guest = Guest(meeting_id=meeting.id, name="记录嘉宾", phone="13900000039", qr_token="records-token")
    db.add(guest)
    db.flush()
    default_session = get_default_check_in_session(db, meeting)
    db.add(CheckIn(meeting_id=meeting.id, session_id=default_session.id, guest_id=guest.id, staff_id=staff.id, method="scan"))
    db.commit()

    response = client.get(
        f"/api/staff/meetings/{meeting.id}/check-ins",
        headers=auth_headers(db, staff),
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["guest_id"] == guest.id
    assert response.json()[0]["method"] == "scan"


def test_date_mode_resolves_current_session_by_injected_date(
    client_and_session: tuple[TestClient, Session],
    create_user,
) -> None:
    """验证日期签到规则可按注入日期解析当前有效场次。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数。
    返回值：None：断言通过表示日期规则不会固定停留在旧默认场次。
    异常：当前函数不主动抛出业务异常；断言失败表示日期自动切换规则异常。
    """
    _, db = client_and_session
    admin = create_user(db, "admin-date-current")
    meeting = Meeting(title="日期自动切换会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    db.add(MeetingSetting(meeting_id=meeting.id, settings_json={"check_in_mode": "date"}))
    first_session = CheckInSession(
        meeting_id=meeting.id,
        title="第一天签到",
        starts_at=datetime(2026, 8, 1, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        ends_at=datetime(2026, 8, 1, 23, 59, tzinfo=ZoneInfo("Asia/Shanghai")),
        is_default=True,
        sort_order=0,
    )
    second_session = CheckInSession(
        meeting_id=meeting.id,
        title="第二天签到",
        starts_at=datetime(2026, 8, 2, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        ends_at=datetime(2026, 8, 2, 23, 59, tzinfo=ZoneInfo("Asia/Shanghai")),
        is_default=False,
        sort_order=1,
    )
    db.add_all([first_session, second_session])
    db.commit()

    current_session = get_current_check_in_session(
        db,
        meeting,
        now=datetime(2026, 8, 2, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
    )

    assert current_session.id == second_session.id
    assert current_session.is_default is True


def test_staff_check_in_uses_today_session_in_date_mode(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证工作人员签到写入日期规则下的当天场次。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示工作人员端不再固定写入旧默认场次。
    异常：当前函数不主动抛出业务异常；断言失败表示工作人员签到场次解析异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-date-staff")
    staff = create_user(db, "staff-date-mode", role="staff")
    china_now = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Shanghai"))
    yesterday = china_now - timedelta(days=1)
    meeting = Meeting(
        title="工作人员日期场次会议",
        created_by_id=admin.id,
        status="published",
        end_time=china_now + timedelta(days=2),
    )
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    db.add(MeetingSetting(meeting_id=meeting.id, settings_json={"check_in_mode": "date"}))
    yesterday_session = CheckInSession(
        meeting_id=meeting.id,
        title="前一天签到",
        starts_at=yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
        ends_at=yesterday.replace(hour=23, minute=59, second=0, microsecond=0),
        is_default=True,
        sort_order=0,
    )
    today_session = CheckInSession(
        meeting_id=meeting.id,
        title="当天签到",
        starts_at=china_now.replace(hour=0, minute=0, second=0, microsecond=0),
        ends_at=china_now.replace(hour=23, minute=59, second=0, microsecond=0),
        is_default=False,
        sort_order=1,
    )
    guest = Guest(meeting_id=meeting.id, name="日期规则嘉宾", phone="13900000042", qr_token="date-mode-token")
    db.add_all([yesterday_session, today_session, guest])
    db.commit()

    response = client.post(
        f"/api/staff/meetings/{meeting.id}/check-ins/scan",
        headers=auth_headers(db, staff),
        json={"qr_token": "date-mode-token"},
    )

    assert response.status_code == 201
    assert response.json()["session_id"] == today_session.id


def test_staff_can_get_current_check_in_session(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证工作人员可读取当前有效签到场次。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示工作人员端可在无签到记录时展示当前场次。
    异常：当前函数不主动抛出业务异常；断言失败表示当前场次接口异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-staff-session")
    staff = create_user(db, "staff-session-current", role="staff")
    meeting = Meeting(title="工作人员当前场次会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    db.add(StaffMeeting(meeting_id=meeting.id, user_id=staff.id))
    default_session = get_default_check_in_session(db, meeting)
    db.commit()

    response = client.get(
        f"/api/staff/meetings/{meeting.id}/check-in-session",
        headers=auth_headers(db, staff),
    )

    assert response.status_code == 200
    assert response.json()["id"] == default_session.id
    assert response.json()["title"] == "默认签到"
