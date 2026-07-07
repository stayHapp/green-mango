# 后端规划

本文档记录后端方向，不包含具体业务代码。

## FastAPI 项目分层

后端采用清晰分层：

```text
backend/
  pyproject.toml
  alembic.ini
  alembic/
    env.py
    script.py.mako
    versions/
  app/
    api/
      routes/
    core/
    db/
    models/
    schemas/
    services/
    main.py
  tests/
```

当前已提供最小 FastAPI 应用入口 `backend/app/main.py`，并注册 `GET /api/health` 健康检查接口。

## models

`models` 保存 ORM 模型，对应数据库表结构。

当前已实现第一版核心模型：

- `User`
- `Meeting`
- `MeetingSetting`
- `RegistrationField`
- `Registration`
- `RegistrationValue`

模型文件：

- `backend/app/models/user.py`
- `backend/app/models/meeting.py`
- `backend/app/models/registration.py`

`backend/app/models/__init__.py` 负责导入所有模型，确保 Alembic 能通过 `Base.metadata` 发现业务表。

## schemas

`schemas` 保存 Pydantic 请求和响应结构，用于 API 输入输出校验。

当前已有 `HealthResponse`，用于健康检查接口响应。业务 API schema 尚未实现。

## routes

`app/api/routes/` 保存 FastAPI 路由定义，负责接收请求、调用服务层和返回响应。

`app/api/router.py` 负责汇总各模块路由，并由 `app/main.py` 挂载到 `/api` 前缀下。

当前只实现健康检查路由，业务路由尚未实现。

## services

`services` 保存业务逻辑，例如会议创建、字段配置校验、报名提交和报名记录查询。

当前尚未添加业务服务。

## db

`db` 保存数据库连接、Session 管理和迁移相关入口。

当前已建立：

- `app/db/base.py`：SQLAlchemy Declarative Base。
- `app/db/session.py`：engine、SessionLocal、`create_db_engine()` 和 `get_db()`。
- `alembic.ini` 与 `alembic/`：Alembic 迁移骨架。
- `alembic/versions/20260707_0001_create_core_tables.py`：首个核心表迁移。

默认数据库为本地 SQLite，正式环境通过 `DATABASE_URL` 指向 PostgreSQL。

## core

`core` 保存配置、安全、日志等基础能力。

当前使用 `pydantic-settings` 管理配置，支持从环境变量和 `.env` 读取 `DATABASE_URL`。

## tests

`backend/tests/` 保存 pytest 测试。

当前已有：

- 健康检查测试。
- 数据库 engine 基础测试。
- 核心模型 metadata 和约束测试。

后续 MVP 至少应继续覆盖会议创建、字段配置、报名提交和报名记录查询的核心路径。
