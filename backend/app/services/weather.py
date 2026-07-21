"""和风天气查询、转换和短期缓存服务。"""

from __future__ import annotations

import json
import gzip
import logging
import re
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.ssl_context import create_external_ssl_context
from app.schemas.weather import CurrentWeatherResponse, DailyWeatherResponse, HourlyWeatherResponse, MeetingWeatherResponse

logger = logging.getLogger(__name__)

_CACHE: dict[str, tuple[datetime, MeetingWeatherResponse]] = {}
_CACHE_LOCK = Lock()


class WeatherProviderError(RuntimeError):
    """和风天气配置、网络或响应异常。"""


def extract_weather_query(location: str) -> str:
    """从会议地点中提取适合城市搜索的区县或城市关键词。

    入参：location 为会议地点文本，必填，可包含场馆和楼栋信息。
    返回值：str：优先返回最后一个区县，其次返回首个城市，最后返回原始地点。
    异常：地点为空白时抛出 WeatherProviderError。
    """
    normalized = location.strip()
    if not normalized:
        raise WeatherProviderError("会议地点尚未填写，无法查询天气。")
    districts = re.findall(r"[\u4e00-\u9fa5]{2,}(?:区|县)", normalized)
    if districts:
        return districts[-1]
    cities = re.findall(r"[\u4e00-\u9fa5]{2,}市", normalized)
    return cities[0] if cities else normalized


def request_qweather(path: str, params: dict[str, str]) -> dict[str, Any]:
    """调用和风天气 JSON API。

    入参：path 为以斜杠开头的 API 路径；params 为查询参数，均必填。
    返回值：dict[str, Any]：解析后的 JSON 对象。
    异常：配置缺失、网络失败、响应不是对象或业务状态非 200 时抛出 WeatherProviderError。
    """
    host = settings.qweather_api_host.strip().rstrip("/")
    api_key = settings.qweather_api_key.strip()
    if not host or not api_key:
        raise WeatherProviderError("和风天气服务尚未配置。")
    request = Request(
        f"https://{host}{path}?{urlencode(params)}",
        headers={"X-QW-Api-Key": api_key},
    )
    try:
        with urlopen(request, timeout=8, context=create_external_ssl_context()) as response:
            response_body = response.read()
            # 和风天气可能在未显式请求时仍返回 Gzip 压缩内容，解析前按响应头解压。
            if response.headers.get("Content-Encoding", "").lower() == "gzip":
                response_body = gzip.decompress(response_body)
            payload = json.loads(response_body.decode("utf-8"))
    except HTTPError as error:
        logger.warning(
            "和风天气接口返回 HTTP %s，路径=%s，参数=%s，错误=%s",
            error.code, path, params, error.reason,
        )
        raise WeatherProviderError(f"天气服务返回 HTTP {error.code}，请稍后重试。") from error
    except (URLError, TimeoutError, OSError) as error:
        logger.warning(
            "和风天气网络异常，路径=%s，参数=%s，错误=%s",
            path, params, error,
        )
        raise WeatherProviderError("天气服务网络异常，请稍后重试。") from error
    except Exception as error:
        logger.exception(
            "和风天气调用未预期异常，路径=%s，参数=%s",
            path, params,
        )
        raise WeatherProviderError("天气服务暂时不可用，请稍后重试。") from error
    if not isinstance(payload, dict):
        logger.warning("和风天气响应非对象结构，payload 类型=%s", type(payload).__name__)
        raise WeatherProviderError("天气服务返回了异常结果。")
    if str(payload.get("code")) != "200":
        logger.warning(
            "和风天气业务错误，路径=%s，参数=%s，code=%s",
            path, params, payload.get("code"),
        )
        raise WeatherProviderError(
            f"天气服务返回错误（{payload.get('code')}），请稍后重试。"
        )
    return payload


def build_weather(
    location: str,
    longitude: float | None = None,
    latitude: float | None = None,
) -> MeetingWeatherResponse:
    """查询并聚合会议地点的实时天气与七日预报。

    入参：location 为会议地点文本；longitude 与 latitude 为管理员确认的高德坐标，可选。
    返回值：MeetingWeatherResponse：包含地点、实况、七日预报和来源信息。
    异常：地点无法匹配或供应商调用异常时抛出 WeatherProviderError。
    """
    query = f"{longitude:.2f},{latitude:.2f}" if longitude is not None and latitude is not None else extract_weather_query(location)
    lookup = request_qweather("/geo/v2/city/lookup", {"location": query, "range": "cn", "number": "1", "lang": "zh"})
    locations = lookup.get("location") or []
    if not locations:
        raise WeatherProviderError("未能识别会议地点对应的天气区域。")
    matched = locations[0]
    location_id = str(matched["id"])
    current_payload = request_qweather("/v7/weather/now", {"location": location_id, "lang": "zh", "unit": "m"})
    daily_payload = request_qweather("/v7/weather/7d", {"location": location_id, "lang": "zh", "unit": "m"})
    hourly_payload = request_qweather("/v7/weather/24h", {"location": location_id, "lang": "zh", "unit": "m"})
    current = current_payload["now"]
    daily = daily_payload.get("daily") or []
    hourly = hourly_payload.get("hourly") or []
    return MeetingWeatherResponse(
        available=True,
        location_name=f"{matched.get('name', query)} · {matched.get('adm2') or matched.get('adm1') or '中国'}",
        message="以下为和风天气提供的近期天气预报。",
        current=CurrentWeatherResponse(
            observed_at=str(current["obsTime"]),
            updated_at=str(current_payload.get("updateTime")) if current_payload.get("updateTime") else None,
            temperature=int(current["temp"]),
            condition=str(current["text"]),
            icon_code=str(current["icon"]),
            humidity=int(current["humidity"]),
            wind_speed=int(current["windSpeed"]),
        ),
        daily=[
            DailyWeatherResponse(
                date=str(item["fxDate"]),
                condition=str(item["textDay"]),
                icon_code=str(item["iconDay"]),
                precipitation=float(item.get("precip") or 0),
                high=int(item["tempMax"]),
                low=int(item["tempMin"]),
            )
            for item in daily
        ],
        hourly=[
            HourlyWeatherResponse(
                forecast_at=str(item["fxTime"]),
                condition=str(item["text"]),
                icon_code=str(item["icon"]),
                temperature=int(item["temp"]),
                precipitation_probability=int(float(item.get("pop") or 0)),
                precipitation=float(item.get("precip") or 0),
            )
            for item in hourly[:6]
        ],
        tips=_build_weather_tips(current, daily),
    )


# 阈值常量集中存放，便于运营调整。
_RAIN_TIP_MM = 5.0        # 当天降水 ≥ 5mm 提示带伞
_STRONG_WIND_KMH = 30     # 风速 ≥ 30 km/h 提示防风
_HOT_TEMP_C = 32          # 高温阈值
_COLD_TEMP_C = 5          # 低温阈值
_HIGH_HUMIDITY_PCT = 80   # 高湿阈值


def _build_weather_tips(current: dict[str, Any], daily: list[dict[str, Any]]) -> list[str]:
    """根据实时天气和短期预报生成简洁温馨提示列表。

    入参：current 为和风天气当前实况；daily 为未来 7 天预报列表。
    返回值：list[str]：条件触发的提示文案列表，未触发时为空列表。
    异常：解析失败时静默忽略，不向路由抛出异常。
    """

    def safe_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def safe_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    temperature = safe_int(current.get("temp"))
    humidity = safe_int(current.get("humidity"))
    wind_speed = safe_int(current.get("windSpeed"))

    today_precipitation = 0.0
    if daily:
        today_precipitation = safe_float(daily[0].get("precip")) or 0.0

    tips: list[str] = []
    if wind_speed is not None and wind_speed >= _STRONG_WIND_KMH:
        tips.append("今日风力较大，外出注意避风并适当添衣")
    if today_precipitation >= _RAIN_TIP_MM:
        tips.append("近期有降雨，建议携带雨具")
    if temperature is not None and temperature >= _HOT_TEMP_C:
        tips.append("气温较高，外出注意防晒与补水")
    elif temperature is not None and temperature <= _COLD_TEMP_C:
        tips.append("气温偏低，建议添衣保暖")
    if humidity is not None and humidity >= _HIGH_HUMIDITY_PCT:
        tips.append("空气湿度较高，请注意防潮与通风")
    if not tips and temperature is not None and 12 <= temperature <= 26 and (humidity or 0) < 70:
        tips.append("天气舒适，适合户外活动")
    return tips


def get_weather(
    location: str,
    longitude: float | None = None,
    latitude: float | None = None,
) -> MeetingWeatherResponse:
    """读取会议地点天气并应用进程内短期缓存。

    入参：location 为会议地点文本；longitude 与 latitude 为管理员确认的坐标，可选。
    返回值：MeetingWeatherResponse：缓存有效时直接返回，否则查询供应商并写入缓存。
    异常：供应商异常时返回 `available=false` 的降级响应，不继续向路由抛出。
    """
    cache_key = f"{longitude},{latitude}" if longitude is not None and latitude is not None else location.strip()
    now = datetime.now(timezone.utc)
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]
    try:
        result = build_weather(location, longitude, latitude)
    except WeatherProviderError as error:
        return MeetingWeatherResponse(available=False, location_name=extract_weather_query(location) if location.strip() else "会议地点", message=str(error))
    expires_at = now + timedelta(seconds=max(settings.weather_cache_seconds, 60))
    with _CACHE_LOCK:
        _CACHE[cache_key] = (expires_at, result)
    return result
