"""Excel 导入导出 API 测试。

覆盖场景：模板下载、正常导入、错误行汇总、签到表导出、嘉宾状态导出等。
"""

from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access import MeetingAdmin
from app.models.guest import CheckIn, Guest, GuestField
from app.models.meeting import Meeting
from app.models.user import User


def test_download_import_template_with_dynamic_fields(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证下载的导入模板包含动态字段列头。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示模板生成包含动态字段。
    异常：当前函数不主动抛出业务异常；断言失败表示模板生成逻辑异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-template")
    meeting = Meeting(title="模板会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    db.add(MeetingAdmin(meeting_id=meeting.id, user_id=admin.id))
    db.add(GuestField(meeting_id=meeting.id, label="学科", key="subject", field_type="text", required=True))
    db.commit()

    response = client.get(
        f"/api/admin/meetings/{meeting.id}/guests/import-template",
        headers=auth_headers(db, admin),
    )
    assert response.status_code == 200
    workbook = load_workbook(BytesIO(response.content))
    header_row = [cell.value for cell in workbook["嘉宾导入"][1]][:7]
    assert header_row == ["姓名", "手机号", "单位", "职务", "身份", "座位号", "学科"]
    workbook.close()


def test_normal_import_succeeds(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证正常导入嘉宾成功。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示正常导入路径可用。
    异常：当前函数不主动抛出业务异常；断言失败表示导入逻辑异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-import")
    meeting = Meeting(title="导入会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    db.add(MeetingAdmin(meeting_id=meeting.id, user_id=admin.id))
    db.add(GuestField(meeting_id=meeting.id, label="学科", key="subject", field_type="text", required=True))
    db.commit()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["姓名", "手机号", "单位", "职务", "身份", "座位号", "学科"])
    worksheet.append(["有效嘉宾", "13800000001", "第一学校", "教师", "参会嘉宾", "B01", "数学"])
    upload = BytesIO()
    workbook.save(upload)
    workbook.close()

    response = client.post(
        f"/api/admin/meetings/{meeting.id}/guests/import",
        headers=auth_headers(db, admin),
        files={"file": ("guests.xlsx", upload.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    assert response.json()["imported_count"] == 1
    assert len(response.json()["errors"]) == 0

    imported_guest = db.scalar(select(Guest).where(Guest.meeting_id == meeting.id, Guest.phone == "13800000001"))
    assert imported_guest is not None
    assert imported_guest.name == "有效嘉宾"


def test_import_with_invalid_rows_reports_errors(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证导入含错误行时返回行级错误汇总。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示错误行被识别并报告。
    异常：当前函数不主动抛出业务异常；断言失败表示错误行处理逻辑异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-import-err")
    meeting = Meeting(title="错误导入会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    db.add(MeetingAdmin(meeting_id=meeting.id, user_id=admin.id))
    db.commit()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["姓名", "手机号", "单位", "职务", "身份", "座位号"])
    worksheet.append(["有效嘉宾", "13800000002", "第一学校", None, None, None])
    worksheet.append(["缺手机号嘉宾", None, None, None, None, None])
    upload = BytesIO()
    workbook.save(upload)
    workbook.close()

    response = client.post(
        f"/api/admin/meetings/{meeting.id}/guests/import",
        headers=auth_headers(db, admin),
        files={"file": ("guests.xlsx", upload.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    assert response.json()["imported_count"] == 1
    assert len(response.json()["errors"]) == 1
    assert response.json()["errors"][0]["row_number"] == 3


def test_check_in_export_produces_valid_xlsx(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证签到表导出为有效 XLSX 文件。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示签到导出生成正确文件。
    异常：当前函数不主动抛出业务异常；断言失败表示导出逻辑异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-export")
    staff = create_user(db, "staff-export", role="staff")
    meeting = Meeting(title="导出会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    db.add(MeetingAdmin(meeting_id=meeting.id, user_id=admin.id))
    guest = Guest(meeting_id=meeting.id, name="导出嘉宾", phone="13800000003", qr_token="export-token")
    db.add(guest)
    db.flush()
    db.add(CheckIn(meeting_id=meeting.id, guest_id=guest.id, staff_id=staff.id, method="manual"))
    db.commit()

    response = client.get(
        f"/api/admin/meetings/{meeting.id}/check-ins/export",
        headers=auth_headers(db, admin),
    )
    assert response.status_code == 200
    workbook = load_workbook(BytesIO(response.content), data_only=True)
    rows = list(workbook["签到明细"].iter_rows(values_only=True))
    workbook.close()
    assert len(rows) >= 2  # 至少表头 + 1 行数据
    assert rows[1][1] == "导出嘉宾"
    assert rows[1][7] == "已签到"


def test_guest_status_export_produces_valid_xlsx(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
) -> None:
    """验证嘉宾状态导出为有效 XLSX 文件。

    入参：client_and_session 为测试客户端和数据库会话夹具；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数。
    返回值：None：断言通过表示嘉宾状态导出生成正确文件。
    异常：当前函数不主动抛出业务异常；断言失败表示导出逻辑异常。
    """
    client, db = client_and_session
    admin = create_user(db, "admin-status-export")
    meeting = Meeting(title="状态导出会议", created_by_id=admin.id, status="published")
    db.add(meeting)
    db.flush()
    db.add(MeetingAdmin(meeting_id=meeting.id, user_id=admin.id))
    guest = Guest(
        meeting_id=meeting.id,
        name="状态嘉宾",
        phone="13800000004",
        source="admin_import",
        qr_token="status-export-token",
    )
    db.add(guest)
    db.commit()

    response = client.get(
        f"/api/admin/meetings/{meeting.id}/guests/export",
        headers=auth_headers(db, admin),
    )
    assert response.status_code == 200
    workbook = load_workbook(BytesIO(response.content), data_only=True)
    rows = list(workbook["嘉宾状态"].iter_rows(values_only=True))
    workbook.close()
    assert len(rows) >= 2  # 至少表头 + 1 行数据
    # 查找嘉宾所在行
    guest_rows = [r for r in rows[1:] if r[1] == "状态嘉宾"]
    assert len(guest_rows) == 1
