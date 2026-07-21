"""工作人员签到 API 测试。

覆盖场景：扫码签到、手工签到、重复签到保护、会议过期签到、停用嘉宾签到、
无效二维码、跨会议嘉宾签到、嘉宾搜索、未授权工作人员等。
"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.access import StaffMeeting
from app.models.guest import CheckIn, Guest
from app.models.meeting import Meeting
from app.models.user import User


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
    db.add(CheckIn(meeting_id=meeting.id, guest_id=guest.id, staff_id=staff.id, method="scan"))
    db.commit()

    response = client.get(
        f"/api/staff/meetings/{meeting.id}/guests?query=A12",
        headers=auth_headers(db, staff),
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "陈老师"
    assert response.json()[0]["checked_in"] is True


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
    db.add(CheckIn(meeting_id=meeting.id, guest_id=guest.id, staff_id=staff.id, method="scan"))
    db.commit()

    response = client.get(
        f"/api/staff/meetings/{meeting.id}/check-ins",
        headers=auth_headers(db, staff),
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["guest_id"] == guest.id
    assert response.json()[0]["method"] == "scan"
