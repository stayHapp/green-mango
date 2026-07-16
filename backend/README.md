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

本地开发默认使用 SQLite：

```text
DATABASE_URL=sqlite:///./dev.db
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

当前迁移头为 `20260716_0006`。

## 外部服务配置

天气和地点搜索均由后端代理，真实凭据只写入本地 `.env`：

```text
QWEATHER_API_HOST=和风天气专属Host
QWEATHER_API_KEY=和风天气服务端Key
WEATHER_CACHE_SECONDS=1800
AMAP_WEB_SERVICE_KEY=高德Web服务API类型Key
```

未配置高德 Key 时，管理员仍可编辑会议与路线正文，但无法搜索并确认导航点位。

## 准备本地联调数据

迁移完成后，可显式执行幂等脚本创建或重置三端演示账号和会议：

```bash
python -m app.scripts.seed_dev
```

该命令仅用于本地开发，会重置以下演示凭据：

- 管理员：`admin` / `admin-pass-123`
- 工作人员：`staff01` / `staff-pass-123`
- 嘉宾：`李文博` / `13900000001`

命令执行后会输出嘉宾入口所需的数字会议 ID。

## 运行测试

```bash
python -m pytest
```

也可以在仓库根目录运行：

```bash
./scripts/check_all.sh
```
