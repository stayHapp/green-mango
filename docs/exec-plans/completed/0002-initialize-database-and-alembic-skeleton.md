# 初始化数据库连接与 Alembic 迁移骨架

## 任务名称

初始化数据库连接与 Alembic 迁移骨架。

## 背景

后端已经具备最小 FastAPI 应用、健康检查接口和 pytest 测试，但还没有稳定完成的数据库连接、ORM 基类、Session 管理和迁移骨架。MVP 后续需要创建会议、报名字段和报名记录，必须先建立可测试、可迁移的数据库基础设施。

用户已确认本项目后端使用 Python 3.12。后续执行前需要先对齐当前仓库状态：此前本计划曾被中断，可能已有部分数据库/Alembic 文件写入工作区。正式实施时必须先检查这些文件，按本计划修正，不直接假设当前状态完整或正确。

## 目标

本次任务完成后，应具备：

- Python 3.12 虚拟环境。
- SQLAlchemy 2.x 作为后端 ORM 基础。
- Alembic 作为数据库迁移工具。
- `pydantic-settings` 作为配置管理基础。
- 可配置的数据库连接地址，默认使用本地 SQLite。
- `backend/app/db/` 下的 ORM Base、engine、session 和 FastAPI 依赖入口。
- Alembic 基础目录与配置，可用于后续创建迁移脚本。
- 最小数据库测试，验证 SQLite engine 和 metadata 初始化可用。
- 更新后端 README、数据库文档、后端架构文档、技术决策和 CHANGELOG。
- `scripts/check_all.sh` 继续通过。

## 不在本次范围内的内容

- 不创建 `users`、`meetings` 等真实业务表。
- 不生成首个业务迁移版本。
- 不实现会议管理 API。
- 不连接真实 PostgreSQL 服务。
- 不实现管理员登录、权限或密码逻辑。
- 不修改前端。

## 已确认技术方案

- Python：3.12
- 依赖管理：`venv` + `pip` + `pyproject.toml`
- 后端框架：FastAPI
- 配置管理：`pydantic-settings`
- ORM：SQLAlchemy 2.x
- 数据库迁移：Alembic
- 本地数据库：SQLite
- 正式数据库：PostgreSQL
- 测试：pytest + httpx/FastAPI TestClient

## 涉及文件

预计新增或修改：

- `backend/pyproject.toml`
- `backend/.venv/`，本地虚拟环境，不提交
- `backend/.env.example`
- `backend/app/core/config.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/db/__init__.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/.gitkeep`
- `backend/tests/test_db.py`
- `backend/README.md`
- `README.md`
- `docs/architecture/backend.md`
- `docs/architecture/database.md`
- `docs/decisions/0004-orm-and-migrations.md`
- `CHANGELOG.md`

## 分步计划

1. 检查当前工作区状态。
   - 查看 `git status --short`。
   - 查看 `backend/pyproject.toml`、`backend/app/core/config.py`、`backend/app/db/`、`backend/alembic/`、`backend/tests/`。
   - 判断中断前已写入的数据库骨架是否需要保留、修正或补齐。

2. 确认 Python 3.12 可用。
   - 检查 `python3.12 --version`。
   - 如果本机没有 `python3.12`，停止并提示用户安装或指定 Python 3.12 路径。

3. 创建或重建后端虚拟环境。
   - 使用 `python3.12 -m venv backend/.venv`。
   - 如果已有 `backend/.venv` 且不是 Python 3.12，需要先确认后再重建。
   - `backend/.venv` 不提交到版本库。

4. 更新后端依赖声明。
   - 将 `backend/pyproject.toml` 的 `requires-python` 调整为 `>=3.12`。
   - 加入 `sqlalchemy>=2.0,<3.0`。
   - 加入 `alembic>=1.13,<2.0`。
   - 加入 `pydantic-settings>=2,<3`。
   - 保留 FastAPI、Pydantic、uvicorn、pytest、httpx。

5. 建立配置管理。
   - 使用 `pydantic-settings` 定义 `Settings`。
   - 配置项至少包含：`app_name`、`app_version`、`database_url`。
   - 默认 `database_url` 为 SQLite，例如 `sqlite:///./dev.db`。
   - 支持从环境变量或 `.env` 读取配置。
   - 新增 `backend/.env.example`，只放示例，不放真实凭据。

6. 建立数据库基础模块。
   - 创建 `backend/app/db/base.py`，定义 SQLAlchemy `DeclarativeBase`。
   - 创建 `backend/app/db/session.py`，定义 engine、SessionLocal、`create_db_engine()` 和 `get_db()`。
   - SQLite 自动使用 `check_same_thread=False`。
   - `backend/app/db/__init__.py` 导出必要对象。

7. 建立 Alembic 骨架。
   - 创建 `backend/alembic.ini`。
   - 创建 `backend/alembic/env.py`。
   - 将 Alembic `target_metadata` 指向 `Base.metadata`。
   - Alembic 数据库 URL 从同一套 `Settings` 读取。
   - 创建 `backend/alembic/script.py.mako`。
   - 创建 `backend/alembic/versions/.gitkeep`。

8. 新增最小数据库测试。
   - 新增 `backend/tests/test_db.py`。
   - 使用临时 SQLite 文件验证 engine 可创建。
   - 调用 `Base.metadata.create_all()`，确认当前无业务表时表列表为空。
   - 测试不依赖本地 `dev.db`。

9. 安装依赖并运行验证。
   - 使用 `backend/.venv/bin/python -m pip install ".[dev]"`。
   - 从仓库根目录运行 `./scripts/check_all.sh`。
   - 必要时运行 `cd backend && . .venv/bin/activate && alembic current`。

10. 更新文档。
    - 更新 `backend/README.md`：Python 3.12、虚拟环境、依赖安装、Alembic 命令。
    - 更新根 `README.md`：当前后端基础设施状态。
    - 更新 `docs/architecture/backend.md`：数据库层和迁移骨架说明。
    - 更新 `docs/architecture/database.md`：说明当前只建立连接与迁移骨架，尚未创建业务表。
    - 新增或更新 `docs/decisions/0004-orm-and-migrations.md`：记录 SQLAlchemy 2.x + Alembic 的选择原因。
    - 更新 `CHANGELOG.md`。

11. 完成记录与归档。
    - 在本计划的“完成记录”中记录实际完成内容、验证命令和验证结果。
    - 将计划从 `docs/exec-plans/active/` 移到 `docs/exec-plans/completed/`。

## 验收标准

- 后端虚拟环境使用 Python 3.12。
- 后端依赖声明包含 SQLAlchemy 和 Alembic。
- 后端配置使用 `pydantic-settings`。
- 默认数据库地址使用本地 SQLite，且可通过环境变量覆盖。
- `backend/app/db/` 有明确的 Base、engine、session 和依赖入口。
- Alembic 能读取同一套数据库配置和 ORM metadata。
- pytest 至少包含数据库基础设施测试并通过。
- `./scripts/check_all.sh` 通过。
- 文档同步说明数据库骨架状态。
- 没有新增业务表、业务 API 或前端代码。

## 验证方式

计划运行：

```bash
./scripts/check_all.sh
```

必要时额外运行：

```bash
python3.12 --version

cd backend
. .venv/bin/activate
python --version
alembic current
```

## 风险与注意事项

- 当前项目路径为 `/Users/wenguang/project/dm/zhihui-meet`，不在当前工具默认 writable root 内，文件写入需要提升权限。
- 当前计划曾被中断，执行前必须先做状态检查，不能假设已有文件完整。
- 如果本机缺少 Python 3.12，应停止实施并让用户安装或指定解释器路径。
- 安装 SQLAlchemy 和 Alembic 可能需要网络访问。
- 本任务只建立迁移骨架，不生成业务迁移，避免过早固化业务表结构。
- `.env` 不提交，数据库连接示例只写入文档。
- 未收到用户明确“开始”指令前，不执行本计划的构建步骤。

## 完成记录

完成日期：2026-07-07

实际完成内容：

- 确认系统可用 Python 3.12.13。
- 将旧的 Python 3.9 虚拟环境移动到 `/private/tmp/zhihui-meet-backend-venv-py39-backup` 备份。
- 使用 Python 3.12 创建新的 `backend/.venv`。
- 将后端 `requires-python` 调整为 `>=3.12`。
- 引入 SQLAlchemy 2.x、Alembic 和 `pydantic-settings`。
- 建立 `backend/app/db/base.py`、`backend/app/db/session.py` 和数据库依赖出口。
- 建立 Alembic 骨架：`backend/alembic.ini`、`backend/alembic/env.py`、`backend/alembic/script.py.mako`、`backend/alembic/versions/.gitkeep`。
- 新增 `backend/.env.example`。
- 新增数据库基础设施测试 `backend/tests/test_db.py`。
- 更新后端 README、根 README、后端架构文档、数据库文档、ORM 决策记录和 CHANGELOG。
- 修正 `pyproject.toml` 的 setuptools 包发现配置，只打包 `app*`，避免将 `alembic/` 当作 Python 包。

验证结果：

```bash
python3.12 --version
# Python 3.12.13

backend/.venv/bin/python --version
# Python 3.12.13

./scripts/check_all.sh
# 2 passed, 1 warning

cd backend
./.venv/bin/alembic current
# Alembic 使用 SQLiteImpl 正常启动迁移上下文
```

注意事项：

- 当前没有业务表，也没有业务迁移版本。
- `alembic current` 会使用默认 SQLite 配置，可能生成本地 `backend/dev.db`，该文件已通过 `.gitignore` 忽略。
- pytest 当前有一个 FastAPI/Starlette TestClient 依赖弃用警告，不影响当前验证结果，后续可在依赖版本稳定后处理。
