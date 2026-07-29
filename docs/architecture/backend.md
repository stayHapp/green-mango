# 后端规划

本文档记录后端当前实现和分层边界。

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

`backend/app/main.py` 创建 FastAPI 应用、配置 CORS，并把全部业务路由挂载到 `/api`。

## models

`models` 保存 ORM 模型，对应数据库表结构。

当前已实现第一版核心模型：

- `User`
- `Meeting`
- `MeetingSetting`
- `MeetingAssistantFeature`
- `MeetingMaterial`
- `CheckInSession`
- `RegistrationField`
- `Registration`
- `RegistrationValue`
- `MeetingAdmin`
- `StaffMeeting`
- `GuestField`
- `Guest`
- `GuestValue`
- `CheckIn`
- `AuthSession`
- `GuestApplication`

模型文件：

- `backend/app/models/user.py`
- `backend/app/models/meeting.py`
- `backend/app/models/registration.py`
- `backend/app/models/access.py`
- `backend/app/models/guest.py`
- `backend/app/models/auth.py`
- `backend/app/models/application.py`

`backend/app/models/__init__.py` 负责导入所有模型，确保 Alembic 能通过 `Base.metadata` 发现业务表。

## schemas

`schemas` 保存 Pydantic 请求和响应结构，用于 API 输入输出校验。

当前 schema 覆盖会话、会议、会议服务、会议资料、天气、嘉宾与动态字段、工作人员、签到场次、按场次签到统计、Excel 导入摘要和报名审核等全部 MVP 请求响应。

## routes

`app/api/routes/` 保存 FastAPI 路由定义，负责接收请求、调用服务层和返回响应。

`app/api/router.py` 负责汇总各模块路由，并由 `app/main.py` 挂载到 `/api` 前缀下。

当前路由覆盖健康检查、安全登录退出、管理员会议和资源管理、会议服务配置、会议资料上传下载、天气代理、嘉宾登录与个人信息、工作人员签到、签到场次管理、Excel 导入导出和报名审核。接口清单以 `docs/architecture/api.md` 为准。

## services

`services` 保存业务逻辑，例如会议创建、字段配置校验、报名提交和报名记录查询。

服务层负责密码与会话、会议授权、嘉宾动态字段、工作人员授权、签到场次规则、二维码签到、会议服务、会议资料附件、高德地点搜索、天气代理、Excel 文件和报名审核。路由层只负责协议转换、依赖注入和 HTTP 错误映射。

签到场次由 `check_in_sessions.py` 统一解析：没有场次时自动创建默认场次；日期场次无手动覆盖时按服务端当前日期选择；自定义场次由管理员手动设置默认。扫码、手工签到、嘉宾签到状态和后台统计都使用同一解析结果，避免多天会议出现口径不一致。

会议资料由 `meeting_materials.py` 统一处理标题、正文、附件元数据、文件落盘、删除和下载授权。管理员接口可以读取草稿和附件元数据；嘉宾和公开接口必须先通过会议服务发布状态与访问级别判断。

## db

`db` 保存数据库连接、Session 管理和迁移相关入口。

当前已建立：

- `app/db/base.py`：SQLAlchemy Declarative Base。
- `app/db/session.py`：engine、SessionLocal、`create_db_engine()` 和 `get_db()`。
- `alembic.ini` 与 `alembic/`：Alembic 迁移骨架。
- `alembic/versions/20260707_0001_create_core_tables.py`：首个核心表迁移。
- `alembic/versions/20260715_0002_add_meeting_guest_checkin_models.py`：三端 MVP 的授权、嘉宾和签到数据结构迁移。
- `alembic/versions/20260715_0003_add_auth_sessions.py`：可过期和撤销的统一会话表。
- `alembic/versions/20260715_0004_add_guest_applications.py`：嘉宾补充报名和审核表。
- `alembic/versions/20260716_0005_add_meeting_assistant_features.py`：五项会议服务配置表。
- `alembic/versions/20260716_0006_add_meeting_navigation_location.py`：会议导航地点、地址和坐标字段。
- `alembic/versions/20260720_0007_add_guest_source_and_field_status.py`：嘉宾来源和字段状态。
- `alembic/versions/20260721_0008_add_active_guest_identity_index.py`：启用嘉宾身份唯一索引。
- `alembic/versions/20260721_0009_add_assistant_contacts.py`：会议助手联系人字段迁移。
- `alembic/versions/20260728_0010_add_assistant_access_level.py`：会议服务公开或仅登录访问级别。
- `alembic/versions/20260728_0011_add_check_in_sessions.py`：签到场次和按场次签到唯一约束。
- `alembic/versions/20260729_0012_add_meeting_materials.py`：会议资料条目和附件元数据。

本地联调和正式环境均通过 `DATABASE_URL` 指向 PostgreSQL；未提供 `.env` 时，代码默认回退到 SQLite 便于临时开发。

## core

`core` 保存配置、安全、日志等基础能力。

当前使用 `pydantic-settings` 管理配置，支持从环境变量和 `.env` 读取 `DATABASE_URL`、`SESSION_EXPIRE_HOURS`、`CORS_ORIGINS`、高德地图配置、和风天气配置、会议资料附件目录与附件大小限制。密码和 token 工具位于 `app/core/security.py`。

## tests

`backend/tests/` 保存 pytest 测试。

自动化测试覆盖健康检查、模型和约束、三端会话、会议权限、嘉宾与动态字段、工作人员、扫码和人工签到、统计、真实 XLSX 往返、报名审核与 CORS。
## 外部天气服务

会议助手天气数据由后端统一代理和风天气，前端不持有供应商凭据。运行环境通过 `QWEATHER_API_HOST` 和 `QWEATHER_API_KEY` 配置专属 Host 与服务端 API Key；查询结果默认在应用进程内缓存 30 分钟，可使用 `WEATHER_CACHE_SECONDS` 调整。

服务先从会议地点提取区县或城市，通过 GeoAPI 获取 Location ID，再并行语义上组合实时天气与七日预报。天气功能未发布时接口拒绝访问；地点无法识别、凭据未配置或供应商异常时返回 `available=false` 和中文降级说明，不向嘉宾暴露凭据或底层异常。
