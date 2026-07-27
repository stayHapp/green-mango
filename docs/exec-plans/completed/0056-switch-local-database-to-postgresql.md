# 切换本地数据库到 PostgreSQL

## 任务名称

切换本地数据库到 PostgreSQL 并完成迁移验证。

## 背景

项目当前默认使用 SQLite，本地已生成 `backend/dev.db`。代码和文档已经预留通过 `DATABASE_URL` 指向 PostgreSQL 的能力，但本地尚未实际切换。项目进入 MVP 收口与试运行准备阶段，数据库应先切换到更接近正式环境的 PostgreSQL，以便提前暴露迁移、索引、驱动和连接配置问题。

## 用户确认状态

用户已明确要求“开始执行”，允许在本任务范围内修改依赖配置、创建本地环境配置、安装必要依赖、执行数据库迁移、运行验证并同步文档。

## 执行前必须读取

执行前必须读取并遵守：

- `AGENTS.md`
- `docs/architecture/database.md`
- `docs/architecture/backend.md`
- `docs/architecture/api.md`
- `docs/development/local-startup.md`
- 当前 active 执行计划

## 目标

- 后端依赖中明确包含 PostgreSQL 驱动。
- 本地后端通过 `DATABASE_URL` 连接 PostgreSQL。
- PostgreSQL 数据库完成 Alembic `upgrade head`。
- 本地联调种子数据可写入 PostgreSQL。
- 后端测试、前端构建和基础健康检查通过。
- 文档准确说明当前数据库配置方式和本地切换步骤。

## 不在本次范围内的内容

- 不迁移既有 SQLite 演示数据到 PostgreSQL。
- 不部署远程 PostgreSQL 或生产数据库。
- 不引入 Docker、云数据库或新的主要基础设施。
- 不处理和 PostgreSQL 切换无关的新功能。

## 技术决策与待确认项

- 使用同步 SQLAlchemy 连接，驱动优先选择 `psycopg[binary]`。
- 本地 PostgreSQL 数据库名、用户和密码使用开发环境专用值，不提交真实 `.env`。
- 当前环境尚未发现 PostgreSQL、Homebrew 或 Docker；如本机缺少 PostgreSQL 运行环境，需要先安装或由用户提供现有 PostgreSQL 连接串。

## 注释要求

新增、补全、重构或修复代码时，必须遵守 `AGENTS.md` 的全局代码注释强制规范：

- 所有代码注释和 docstring 必须使用简体中文。
- 保留必要英文技术名词时，首次出现应括号标注中文释义。
- 每个函数/方法必须有中文文档注释，说明功能、入参、返回值和异常/报错场景。
- 关键逻辑、判断分支、循环、复杂计算和重要约束必须添加中文注释说明意图。
- 不写无信息量注释，不重复代码字面含义。

## 涉及文件

- `backend/pyproject.toml`
- `backend/.env`
- `backend/.env.example`
- `docs/architecture/database.md`
- `docs/architecture/backend.md`
- `docs/development/local-startup.md`
- `README.md`

## 分步计划

1. 检查本机 PostgreSQL、客户端工具、服务监听和可用安装路径。
2. 更新后端 PostgreSQL 驱动依赖并安装到 `.venv`。
3. 创建或接入本地 PostgreSQL 数据库。
4. 写入本地 `backend/.env`，将 `DATABASE_URL` 指向 PostgreSQL。
5. 执行 Alembic 迁移和 `seed_dev` 种子数据。
6. 运行后端测试、前端构建和健康检查。
7. 同步更新文档并记录验证结果。

## 验收标准

- `backend/.env` 指向 PostgreSQL 连接串。
- `alembic current` 显示 PostgreSQL 数据库处于最新迁移头。
- `seed_dev` 能成功创建三端演示账号和会议。
- 后端健康检查正常返回。
- 文档不再误导本地当前数据库状态。

## 验证方式

- `backend/.venv/bin/alembic upgrade head`
- `backend/.venv/bin/alembic current`
- `backend/.venv/bin/python -m app.scripts.seed_dev`
- `backend/.venv/bin/pytest -q`
- `cd frontend && npm run build`
- `curl http://127.0.0.1:8000/api/health`

## 风险与注意事项

- 本地缺少 PostgreSQL 运行环境时，无法完成数据库切换，只能先完成代码依赖和文档准备。
- PostgreSQL 与 SQLite 对索引、布尔条件和约束支持存在差异，必须实际跑迁移验证。
- `.env` 包含本地连接信息，不提交到 Git。
- 本任务不删除 `backend/dev.db`，避免破坏既有 SQLite 演示数据。

## 完成记录

- 已确认当前本机没有 `psql`、`postgres`、`pg_isready`、Homebrew、Docker、Conda/Mamba，且 `5432` 端口无 PostgreSQL 服务监听。
- 已将 `psycopg[binary]>=3.2,<4.0` 加入 `backend/pyproject.toml`。
- 已在 `backend/.venv` 中安装新增依赖，`psycopg` 当前版本为 `3.3.4`。
- 已运行后端测试，结果为 `61 passed`，仅保留第三方依赖弃用警告。
- 已完成 PostgreSQL 18.4 安装，安装目录为 `/Library/PostgreSQL/18`，安装日志显示服务名为 `postgresql-18`、端口为 `5432`、超级用户为 `postgres`。
- 已确认 PostgreSQL 服务在提权环境中返回 `127.0.0.1:5432 - accepting connections`。
- 已由用户在本机终端完成项目数据库与用户创建。
- 已验证 `green_mango_user` 可连接 `green_mango` 数据库。
- 已将 `backend/.env` 的 `DATABASE_URL` 切换为 PostgreSQL 连接串，并保留既有本地第三方服务配置。
- 首次 PostgreSQL 迁移暴露 Alembic 版本号过长问题：`20260721_0009_add_assistant_contacts` 超过 `alembic_version.version_num` 的 32 字符限制。
- 已将最新迁移 revision 缩短为 `20260721_0009`，并补齐该迁移函数的中文文档注释。
- 已在 PostgreSQL 空库执行 `alembic upgrade head`，当前版本为 `20260721_0009 (head)`。
- 已执行 `python -m app.scripts.seed_dev`，三端联调数据已写入 PostgreSQL，会议 ID 为 `1`。
- 已启动读取 PostgreSQL 配置的新后端服务，并验证 `/api/health` 返回正常、管理员演示账号可登录、PostgreSQL `meetings` 表有 1 条种子会议。
- 已运行后端测试，结果为 `61 passed`，仅保留第三方依赖弃用警告。
- 已运行前端生产构建并通过，仅保留既有第三方注释和大包体积提示。
- 已同步更新 `backend/.env.example`、`backend/README.md`、`docs/architecture/database.md`、`docs/architecture/backend.md` 和 `docs/development/local-startup.md`。
- 完成日期：2026-07-27。
