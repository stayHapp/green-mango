"""和风天气聚合服务与嘉宾天气接口测试。"""

import gzip
import json
from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.access import MeetingAdmin
from app.models.meeting import Meeting
from app.models.user import User
from app.services import weather
from tests.test_meeting_assistant import create_meeting


def test_request_qweather_decodes_gzip_response(monkeypatch) -> None:
    """验证供应商返回 Gzip 内容时能够先解压再解析 JSON。

    入参：monkeypatch 为 pytest 注入的替换工具。
    返回值：None：断言通过表示压缩响应兼容逻辑正确。
    异常：响应未解压或解析失败时由测试异常报告。
    """
    response = MagicMock()
    response.headers = {"Content-Encoding": "gzip"}
    response.read.return_value = gzip.compress(json.dumps({"code": "200", "location": []}).encode("utf-8"))
    response.__enter__.return_value = response
    monkeypatch.setattr(weather.settings, "qweather_api_host", "test.qweatherapi.com")
    monkeypatch.setattr(weather.settings, "qweather_api_key", "test-key")
    monkeypatch.setattr(weather, "urlopen", MagicMock(return_value=response))

    result = weather.request_qweather("/geo/v2/city/lookup", {"location": "杭州"})

    assert result == {"code": "200", "location": []}


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
            "updateTime": "2026-07-16T12:00+08:00",
            "now": {"obsTime": "2026-07-16T12:00+08:00", "temp": "28", "text": "多云", "icon": "101", "humidity": "81", "windSpeed": "14"},
        }
    if path == "/v7/weather/7d":
        return {
            "code": "200",
            "daily": [{"fxDate": "2026-07-16", "textDay": "多云", "iconDay": "101", "precip": "1.2", "tempMax": "30", "tempMin": "24"}],
        }
    if path == "/v7/weather/24h":
        return {
            "code": "200",
            "hourly": [
                {"fxTime": "2026-07-16T13:00+08:00", "temp": "29", "text": "多云", "icon": "101", "pop": "10", "precip": "0.0"},
            {"fxTime": "2026-07-16T14:00+08:00", "temp": "30", "text": "多云", "icon": "101", "pop": "15", "precip": "0.0"},
            {"fxTime": "2026-07-16T15:00+08:00", "temp": "30", "text": "多云", "icon": "101", "pop": "20", "precip": "0.0"},
                ],
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


def test_build_weather_prefers_navigation_coordinates(monkeypatch) -> None:
    """验证管理员确认坐标存在时天气城市搜索优先使用坐标。

    入参：monkeypatch 为 pytest 注入的替换工具。
    返回值：None：断言通过表示天气与导航共用同一地点。
    异常：坐标未传给和风城市搜索时由断言报告。
    """
    requested_locations: list[str] = []

    def capture_qweather_response(path: str, params: dict[str, str]) -> dict[str, Any]:
        """记录城市搜索参数并复用标准测试响应。

        入参：path 为供应商路径；params 为查询参数，均必填。
        返回值：dict[str, Any]：标准和风天气测试响应。
        异常：未覆盖路径由标准测试响应函数抛出 AssertionError。
        """
        if path == "/geo/v2/city/lookup":
            requested_locations.append(params["location"])
        return fake_qweather_response(path, params)

    monkeypatch.setattr(weather, "request_qweather", capture_qweather_response)

    weather.build_weather("文字地点", 120.123456, 30.234567)

    assert requested_locations == ["120.12,30.23"]


def test_guest_weather_requires_published_feature_and_returns_data(
    client_and_session: tuple[TestClient, Session], create_user, auth_headers, monkeypatch
) -> None:
    """验证嘉宾只能读取已发布会议的天气并获得聚合结果。

    入参：client_and_session 为测试客户端和数据库会话；create_user 为创建用户辅助函数；auth_headers 为请求头辅助函数；monkeypatch 用于隔离外部供应商。
    返回值：None：断言通过表示发布权限与响应结构正确。
    异常：接口状态或返回数据不符合约定时由断言报告。
    """
    client, db = client_and_session
    meeting_id, admin_headers = create_meeting(client, db, create_user, auth_headers, "weather-admin")
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
    monkeypatch.setattr(
        "app.api.routes.meeting_assistant.get_weather",
        lambda location, longitude, latitude: weather.build_weather(location, longitude, latitude),
    )
    monkeypatch.setattr(weather, "request_qweather", fake_qweather_response)

    published = client.get(f"/api/guest/meetings/{meeting_id}/weather", headers=guest_headers)

    assert published.status_code == 200
    assert published.json()["source_name"] == "和风天气"
    assert published.json()["current"]["condition"] == "多云"
    assert isinstance(published.json()["tips"], list)
    if published.json()["current"]:
        # updated_at 是可选字段；后端若填则必须能解析为可比较字符串。
        assert published.json()["current"]["updated_at"] in (None,) or isinstance(published.json()["current"]["updated_at"], str)


def test_build_weather_emits_tips_for_hot_and_rainy_day(monkeypatch) -> None:
    """验证高温并且当日降雨时自动生成对应温馨提示。"""

    def fake_qweather_response(path: str, params: dict[str, str]) -> dict[str, Any]:
        if path == "/geo/v2/city/lookup":
            return {"code": "200", "location": [{"id": "101010100", "name": "杭州", "adm2": "杭州"}]}
        if path == "/v7/weather/now":
            return {
                "code": "200",
                "now": {
                    "obsTime": "2026-07-16T12:00+08:00",
                    "temp": "34",
                    "text": "多云",
                    "icon": "101",
                    "humidity": "60",
                    "windSpeed": "12",
                },
            }
        if path == "/v7/weather/7d":
            return {
                "code": "200",
                "daily": [
                    {"fxDate": "2026-07-16", "textDay": "中雨", "iconDay": "305", "precip": "12.0", "tempMax": "34", "tempMin": "26"},
                ],
            }
        if path == "/v7/weather/24h":
            return {
                "code": "200",
                "hourly": [
                    {"fxTime": "2026-07-16T14:00+08:00", "temp": "34", "text": "中雨", "icon": "305", "pop": "60", "precip": "2.0"},
                ],
            }
        raise AssertionError(f"未覆盖的天气路径：{path}")

    monkeypatch.setattr(weather, "request_qweather", fake_qweather_response)

    result = weather.build_weather("杭州市")

    assert result.available is True
    joined_tips = " ".join(result.tips)
    assert "气温较高" in joined_tips
    assert "降雨" in joined_tips


def test_build_weather_emits_no_warning_tips_in_mild_conditions(monkeypatch) -> None:
    """验证天气舒适时不发出任何高温、降雨或防风的警告提示。"""

    def fake_qweather_response(path: str, params: dict[str, str]) -> dict[str, Any]:
        if path == "/geo/v2/city/lookup":
            return {"code": "200", "location": [{"id": "101010100", "name": "杭州", "adm2": "杭州"}]}
        if path == "/v7/weather/now":
            return {
                "code": "200",
                "now": {
                    "obsTime": "2026-07-16T12:00+08:00",
                    "temp": "22",
                    "text": "晴",
                    "icon": "100",
                    "humidity": "55",
                    "windSpeed": "8",
                },
            }
        if path == "/v7/weather/7d":
            return {
                "code": "200",
                "daily": [
                    {"fxDate": "2026-07-16", "textDay": "晴", "iconDay": "100", "precip": "0", "tempMax": "24", "tempMin": "18"},
                ],
            }
        if path == "/v7/weather/24h":
            return {
                "code": "200",
                "hourly": [
                    {"fxTime": "2026-07-16T13:00+08:00", "temp": "23", "text": "晴", "icon": "100", "pop": "0", "precip": "0"},
                ],
            }
        raise AssertionError(f"未覆盖的天气路径：{path}")

    monkeypatch.setattr(weather, "request_qweather", fake_qweather_response)

    result = weather.build_weather("杭州市")

    assert result.available is True
    joined_tips = " ".join(result.tips)
    assert "气温较高" not in joined_tips
    assert "降雨" not in joined_tips
    assert "风力" not in joined_tips
    assert "保暖" not in joined_tips
    assert "湿度" not in joined_tips
