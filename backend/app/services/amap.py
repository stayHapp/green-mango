"""高德地点搜索服务。"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.meeting import MeetingLocationOptionResponse


class AmapProviderError(RuntimeError):
    """高德配置、网络或业务响应异常。"""


def search_amap_places(query: str, city: str = "") -> list[MeetingLocationOptionResponse]:
    """按关键词搜索可用于会议导航的高德 POI（兴趣点）。

    入参：query 为地点名称或结构化地址，必填；city 为可选城市范围。
    返回值：list[MeetingLocationOptionResponse]：最多十条包含名称、地址和坐标的候选项。
    异常：Key 未配置、网络失败或高德返回异常时抛出 AmapProviderError。
    """
    api_key = settings.amap_web_service_key.strip()
    if not api_key:
        raise AmapProviderError("高德地点搜索尚未配置。")
    params = {
        "key": api_key,
        "keywords": query.strip(),
        "city": city.strip(),
        "citylimit": "false",
        "offset": "10",
        "page": "1",
        "extensions": "base",
        "output": "JSON",
    }
    request = Request(f"https://restapi.amap.com/v3/place/text?{urlencode(params)}")
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise AmapProviderError("高德地点搜索暂时不可用，请稍后重试。") from error
    if not isinstance(payload, dict) or payload.get("status") != "1":
        raise AmapProviderError("高德地点搜索返回了异常结果。")
    results: list[MeetingLocationOptionResponse] = []
    for item in payload.get("pois") or []:
        location = str(item.get("location") or "")
        if "," not in location:
            continue
        longitude_text, latitude_text = location.split(",", 1)
        address = item.get("address")
        if not isinstance(address, str):
            address = ""
        district = "".join(
            str(item.get(field) or "") for field in ("pname", "cityname", "adname")
        )
        results.append(
            MeetingLocationOptionResponse(
                poi_id=str(item.get("id") or ""),
                name=str(item.get("name") or query),
                address=address,
                district=district,
                longitude=float(longitude_text),
                latitude=float(latitude_text),
            )
        )
    return results
