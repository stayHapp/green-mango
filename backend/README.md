# Backend

这里是知会后端项目。

当前已完成三端 MVP 后端：管理员、工作人员和嘉宾安全会话，会议与授权管理，嘉宾动态字段和 Excel 导入，二维码签到、统计导出，以及补充报名审核。

## 技术栈

- Python 3.12
- FastAPI
- Pydantic
- pydantic-settings
- SQLAlchemy 2.x
- Alembic
- pytest

## 目录结构

```text
backend/
  alembic/
    versions/
    env.py
    script.py.mako
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
  alembic.ini
  pyproject.toml
```

## 安装依赖

建议在 `backend/` 目录创建虚拟环境：

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"
```

## 配置

本地联调推荐使用 PostgreSQL；未创建 PostgreSQL 时，可临时把 `DATABASE_URL` 改回 `sqlite:///./dev.db`：

```text
DATABASE_URL=postgresql+psycopg://green_mango_user:本地开发密码@127.0.0.1:5432/green_mango
SESSION_EXPIRE_HOURS=12
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

可参考 `.env.example` 创建本地 `.env`。`.env` 不提交到版本库。

## 运行开发服务

```bash
uvicorn app.main:app --reload
```

默认健康检查接口：

```text
GET /api/health
```

## 数据库迁移

查看当前迁移状态：

```bash
alembic current
```

初始化或升级本地数据库：

```bash
alembic upgrade head
```

当前迁移头为 `20260729_0012`。

## 外部服务配置

天气和地点搜索均由后端代理，真实凭据只写入本地 `.env`：

```text
QWEATHER_API_HOST=和风天气专属Host
QWEATHER_API_KEY=和风天气服务端Key
WEATHER_CACHE_SECONDS=1800
AMAP_WEB_SERVICE_KEY=高德Web服务API类型Key
MATERIAL_STORAGE_DIR=./data/meeting-materials
MATERIAL_MAX_FILE_BYTES=20971520
```

未配置高德 Key 时，管理员仍可编辑会议与路线正文，但无法搜索并确认导航点位。
会议资料附件默认存放于后端本地 `data/meeting-materials`，单个附件默认最大 20MB。

## 正式数据说明

正式发布包不内置演示账号、演示会议或测试嘉宾数据。数据库迁移只创建或更新表结构，不会生成业务数据。

首个管理员账号、会议、工作人员和嘉宾信息应通过正式管理流程或受控运维脚本创建；不要在生产数据库中使用公开示例账号或测试手机号。

## 运行测试

```bash
python -m pytest
```

也可以在仓库根目录运行：

```bash
./scripts/check_all.sh
```
