"""FastAPI 应用入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。

    入参：
        无。

    返回值：
        FastAPI：已注册 API 路由和应用元信息的 FastAPI 实例。

    异常：
        当前函数不主动抛出业务异常；配置加载失败时会由配置模块抛出异常。
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
