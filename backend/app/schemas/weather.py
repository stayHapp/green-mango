"""会议天气响应结构。"""

from pydantic import BaseModel, Field


class CurrentWeatherResponse(BaseModel):
    """会议地点当前天气。"""

    observed_at: str
    temperature: int
    condition: str
    icon_code: str
    humidity: int
    wind_speed: int


class DailyWeatherResponse(BaseModel):
    """会议地点单日天气预报。"""

    date: str
    condition: str
    icon_code: str
    precipitation: float
    high: int
    low: int


class MeetingWeatherResponse(BaseModel):
    """嘉宾天气页所需的聚合天气数据。"""

    available: bool
    location_name: str
    message: str
    source_name: str = "和风天气"
    source_url: str = "https://www.qweather.com/"
    current: CurrentWeatherResponse | None = None
    daily: list[DailyWeatherResponse] = Field(default_factory=list)
