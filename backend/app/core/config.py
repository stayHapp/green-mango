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

    异常：
        配置值类型不符合声明时，Pydantic 会在实例化配置时抛出校验异常。
    """

    app_name: str = "知会 API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./dev.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
