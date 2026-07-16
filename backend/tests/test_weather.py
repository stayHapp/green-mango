"""和风天气聚合服务与嘉宾天气接口测试。"""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.services import weather
from tests.test_admin_meetings import auth_headers, client_and_session
from tests.test_meeting_assistant import create_meeting


def fake_qweather_response(path: str, params: dict[str, str]) -> dict[str, Any]:
    """返回覆盖城市搜索、实况和七日预报的和风天气测试响应。

    入参：path 为供应商路径；params 为查询参数，均必填。
    返回值：dict[str, Any]：与目标路径对应的最小合法响应。
    异常：收到未覆盖路径时抛出 AssertionError，避免测试静默通过。
    """
    assert params
    if path == "/geo/v2/city/lookup":
        return {"code": "200", "location": [{"id": "101210101", "name": "杭州", "adm2": "杭州"}]}
    if path == "/v7/weather/now":
        return {
            "code": "200",
            "now": {"obsTime": "2026-07-16T12:00+08:00", "temp": "28", "text": "多云", "icon": "101", "humidity": "81", "windSpeed": "14"},
        }
    if path == "/v7/weather/7d":
        return {
            "code": "200",
            "daily": [{"fxDate": "2026-07-16", "textDay": "多云", "iconDay": "101", "precip": "1.2", "tempMax": "30", "tempMin": "24"}],
        }
    raise AssertionError(f"未覆盖的天气路径：{path}")


def test_build_weather_maps_qweather_response(monkeypatch) -> None:
    """验证和风天气响应被转换为稳定的页面聚合结构。

    入参：monkeypatch 为 pytest 注入的替换工具。
    返回值：None：断言通过表示地点、实况和预报转换正确。
    异常：字段转换不符合约定时由断言报告。
    """
    monkeypatch.setattr(weather, "request_qweather", fake_qweather_response)

    result = weather.build_weather("杭州市未来教育中心")

    assert result.available is True
    assert result.location_name == "杭州 · 杭州"
    assert result.current is not None
    assert result.current.temperature == 28
    assert result.daily[0].precipitation == 1.2


def test_guest_weather_requires_published_feature_and_returns_data(
    client_and_session: tuple[TestClient, Session], monkeypatch
) -> None:
    """验证嘉宾只能读取已发布会议的天气并获得聚合结果。

    入参：client_and_session 为测试客户端和数据库会话；monkeypatch 用于隔离外部供应商。
    返回值：None：断言通过表示发布权限与响应结构正确。
    异常：接口状态或返回数据不符合约定时由断言报告。
    """
    client, db = client_and_session
    meeting_id, admin_headers = create_meeting(client, db, "weather-admin")
    meeting_response = client.patch(
        f"/api/admin/meetings/{meeting_id}",
        headers=admin_headers,
        json={"location": "杭州市未来教育中心"},
    )
    assert meeting_response.status_code == 200
    guest = Guest(meeting_id=meeting_id, name="天气嘉宾", phone="13910000009", qr_token="weather-token")
    db.add(guest)
    db.commit()
    db.refresh(guest)
    guest_headers = auth_headers(db, guest)
    unpublished = client.get(f"/api/guest/meetings/{meeting_id}/weather", headers=guest_headers)
    assert unpublished.status_code == 404
    client.patch(
        f"/api/admin/meetings/{meeting_id}/assistant-features/weather",
        headers=admin_headers,
        json={"content": "注意防暑。", "unpublished_message": "天气待发布。", "is_published": True},
    )
    monkeypatch.setattr("app.api.routes.meeting_assistant.get_weather", lambda location: weather.build_weather(location))
    monkeypatch.setattr(weather, "request_qweather", fake_qweather_response)

    published = client.get(f"/api/guest/meetings/{meeting_id}/weather", headers=guest_headers)

    assert published.status_code == 200
    assert published.json()["source_name"] == "和风天气"
    assert published.json()["current"]["condition"] == "多云"
