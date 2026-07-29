"""会议资料多条目、附件与访问权限 API 测试。"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.guest import Guest
from tests.test_meeting_assistant import create_meeting


def test_admin_manages_multiple_materials_and_guest_downloads_attachment(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
    monkeypatch,
    tmp_path,
) -> None:
    """验证管理员维护多份资料、嘉宾读取正文和下载附件的完整闭环。

    入参：client_and_session 为客户端和数据库；create_user、auth_headers 为认证辅助；
    monkeypatch 和 tmp_path 用于隔离附件存储目录。
    返回值：None：断言通过表示多条资料、附件下载和权限规则均正确。
    异常：断言失败表示资料管理或下载闭环存在缺陷。
    """
    monkeypatch.setattr(settings, "material_storage_dir", str(tmp_path / "materials"))
    client, db = client_and_session
    meeting_id, admin_headers = create_meeting(
        client,
        db,
        create_user,
        auth_headers,
        "materials-admin",
    )
    guest = Guest(
        meeting_id=meeting_id,
        name="资料测试嘉宾",
        phone="13910000021",
        qr_token="materials-guest-token",
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    guest_headers = auth_headers(db, guest)

    text_response = client.post(
        f"/api/admin/meetings/{meeting_id}/materials",
        headers=admin_headers,
        data={"title": "参会须知", "content": "请提前十五分钟到场。"},
    )
    file_response = client.post(
        f"/api/admin/meetings/{meeting_id}/materials",
        headers=admin_headers,
        data={"title": "会议手册", "content": ""},
        files={"attachment": ("第二届会议手册.pdf", b"%PDF-test-content", "application/pdf")},
    )

    assert text_response.status_code == 201
    assert file_response.status_code == 201
    assert file_response.json()["original_filename"] == "第二届会议手册.pdf"
    assert file_response.json()["size_bytes"] == len(b"%PDF-test-content")

    list_response = client.get(
        f"/api/admin/meetings/{meeting_id}/materials",
        headers=admin_headers,
    )
    assert list_response.status_code == 200
    assert [item["title"] for item in list_response.json()] == ["参会须知", "会议手册"]

    publish_response = client.patch(
        f"/api/admin/meetings/{meeting_id}/assistant-features/manual",
        headers=admin_headers,
        json={
            "content": "",
            "unpublished_message": "会议资料正在准备中。",
            "is_published": True,
            "access_level": "guest",
        },
    )
    assert publish_response.status_code == 200

    guest_list_response = client.get(
        f"/api/guest/meetings/{meeting_id}/materials",
        headers=guest_headers,
    )
    public_list_response = client.get(f"/api/meetings/{meeting_id}/materials")
    download_response = client.get(
        f"/api/guest/meetings/{meeting_id}/materials/{file_response.json()['id']}/download",
        headers=guest_headers,
    )

    assert guest_list_response.status_code == 200
    assert len(guest_list_response.json()) == 2
    assert public_list_response.status_code == 401
    assert download_response.status_code == 200
    assert download_response.content == b"%PDF-test-content"
    assert "filename*=utf-8''" in download_response.headers["content-disposition"].lower()


def test_material_validation_update_delete_and_draft_isolation(
    client_and_session: tuple[TestClient, Session],
    create_user,
    auth_headers,
    monkeypatch,
    tmp_path,
) -> None:
    """验证资料字段约束、附件替换删除和未发布隔离。

    入参：client_and_session 为客户端和数据库；create_user、auth_headers 为认证辅助；
    monkeypatch 和 tmp_path 用于隔离附件存储目录。
    返回值：None：断言通过表示无内容资料被拒绝、附件可移除且草稿不向嘉宾返回。
    异常：断言失败表示资料校验、清理或发布隔离存在缺陷。
    """
    storage_root = tmp_path / "materials"
    monkeypatch.setattr(settings, "material_storage_dir", str(storage_root))
    client, db = client_and_session
    meeting_id, admin_headers = create_meeting(
        client,
        db,
        create_user,
        auth_headers,
        "materials-validation-admin",
    )
    guest = Guest(
        meeting_id=meeting_id,
        name="资料草稿嘉宾",
        phone="13910000022",
        qr_token="materials-draft-token",
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    guest_headers = auth_headers(db, guest)

    empty_response = client.post(
        f"/api/admin/meetings/{meeting_id}/materials",
        headers=admin_headers,
        data={"title": "空资料", "content": ""},
    )
    unsupported_response = client.post(
        f"/api/admin/meetings/{meeting_id}/materials",
        headers=admin_headers,
        data={"title": "危险附件", "content": ""},
        files={"attachment": ("run.exe", b"unsafe", "application/octet-stream")},
    )
    created_response = client.post(
        f"/api/admin/meetings/{meeting_id}/materials",
        headers=admin_headers,
        data={"title": "可更新资料", "content": "初始正文"},
        files={"attachment": ("说明.txt", b"old attachment", "text/plain")},
    )

    assert empty_response.status_code == 422
    assert unsupported_response.status_code == 422
    assert created_response.status_code == 201
    material_id = created_response.json()["id"]
    stored_files = [path for path in storage_root.rglob("*") if path.is_file()]
    assert len(stored_files) == 1

    draft_response = client.get(
        f"/api/guest/meetings/{meeting_id}/materials",
        headers=guest_headers,
    )
    assert draft_response.status_code == 404

    update_response = client.patch(
        f"/api/admin/meetings/{meeting_id}/materials/{material_id}",
        headers=admin_headers,
        data={
            "title": "更新后的资料",
            "content": "保留正文",
            "remove_attachment": "true",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["original_filename"] is None
    assert not [path for path in storage_root.rglob("*") if path.is_file()]

    delete_response = client.delete(
        f"/api/admin/meetings/{meeting_id}/materials/{material_id}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 204
    assert client.get(
        f"/api/admin/meetings/{meeting_id}/materials",
        headers=admin_headers,
    ).json() == []
