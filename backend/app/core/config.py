"""应用配置定义。

本模块集中管理运行时配置，优先从环境变量和 `.env` 文件读取，避免配置读取逻辑分散在业务代码中。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """后端应用配置。

    属性：
        app_name：应用名称，用于 FastAPI 文档标题。
        app_version：应用版本，用于 FastAPI 元信息。
        database_url：数据库连接地址，默认指向本地 SQLite。
        session_expire_hours：登录会话有效小时数。
        cors_origins：允许跨域访问 API 的前端来源，以英文逗号分隔。
        qweather_api_host：和风天气控制台分配的专属 API Host。
        qweather_api_key：和风天气服务端 API KEY，仅从环境变量读取。
        weather_cache_seconds：天气结果内存缓存秒数。
        amap_web_service_key：高德 Web 服务 API Key，仅用于后端地点搜索。

    异常：
        配置值类型不符合声明时，Pydantic 会在实例化配置时抛出校验异常。
    """

    app_name: str = "知会 API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./dev.db"
    session_expire_hours: int = 12
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    qweather_api_host: str = ""
    qweather_api_key: str = ""
    weather_cache_seconds: int = 1800
    amap_web_service_key: str = ""

    def get_cors_origins(self) -> list[str]:
        """解析允许跨域访问的前端来源列表。

        入参：无；读取当前配置对象的 cors_origins 字符串。
        返回值：list[str]：去除空白和空项后的来源 URL 列表。
        异常：当前函数不主动抛出业务异常。
        """
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
