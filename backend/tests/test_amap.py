"""高德地点搜索服务测试。"""

import json
from unittest.mock import MagicMock

from app.services import amap


def test_search_amap_places_maps_poi_response(monkeypatch) -> None:
    """验证高德 POI 响应转换为管理员地点候选项。

    入参：monkeypatch 为 pytest 注入的替换工具。
    返回值：None：断言通过表示名称、地址和坐标转换正确。
    异常：供应商响应解析不符合约定时由断言报告。
    """
    payload = {
        "status": "1",
        "pois": [
            {
                "id": "B001",
                "name": "未来教育中心",
                "address": "文一路88号",
                "pname": "浙江省",
                "cityname": "杭州市",
                "adname": "西湖区",
                "location": "120.123456,30.234567",
            }
        ],
    }
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    monkeypatch.setattr(amap.settings, "amap_web_service_key", "test-key")
    monkeypatch.setattr(amap, "urlopen", MagicMock(return_value=response))

    results = amap.search_amap_places("未来教育中心")

    assert len(results) == 1
    assert results[0].name == "未来教育中心"
    assert results[0].district == "浙江省杭州市西湖区"
    assert results[0].longitude == 120.123456
    assert results[0].latitude == 30.234567
