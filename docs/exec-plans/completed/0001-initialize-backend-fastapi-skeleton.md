# 初始化后端 FastAPI 项目骨架

## 任务名称

初始化后端 FastAPI 项目骨架。

## 背景

项目已经完成基础目录和文档体系初始化，但 `backend/` 目录目前只有 README，还没有可运行的后端工程。

根据 MVP 范围，后续需要实现会议管理、报名字段配置、前台报名和后台报名管理。为了避免直接进入业务代码导致结构混乱，第一步应先建立最小后端工程骨架、依赖管理方式、测试入口和配置约定。

## 目标

本次任务完成后，应具备一个最小但可扩展的 FastAPI 后端骨架：

- 明确 Python 依赖管理方式。
- 建立 `backend/app/` 基础目录结构。
- 提供 FastAPI 应用入口。
- 提供健康检查接口。
- 建立配置、数据库、路由、模型、schema、service、测试等目录。
- 建立 pytest 最小测试。
- 更新后端 README 和相关架构文档。
- 更新 `scripts/check_all.sh`，让它能运行后端测试。

## 不在本次范围内的内容

- 不实现会议管理业务 API。
- 不创建真实数据库模型。
- 不编写 Alembic 迁移脚本。
- 不实现管理员登录或权限系统。
- 不初始化前端 Vue 项目。
- 不连接 PostgreSQL。
- 不实现报名字段和报名提交逻辑。

## 涉及文件

预计新增或修改：

- `backend/README.md`
- `backend/pyproject.toml` 或其他依赖配置文件
- `backend/app/main.py`
- `backend/app/api/`
- `backend/app/core/`
- `backend/app/db/`
- `backend/app/models/`
- `backend/app/schemas/`
- `backend/app/services/`
- `backend/tests/`
- `scripts/check_all.sh`
- `docs/architecture/backend.md`
- `docs/architecture/api.md`
- `docs/architecture/security.md`
- `CHANGELOG.md`

## 分步计划

1. 阅读 `AGENTS.md`、`docs/product/mvp-scope.md`、`docs/architecture/backend.md`、`docs/architecture/api.md`。
2. 确认后端依赖管理方式，优先选择简单、清晰、适合早期项目的方案。
3. 创建 FastAPI 最小应用入口。
4. 创建健康检查路由，例如 `GET /api/health`。
5. 建立后端分层目录，但只放必要的占位文件或最小代码。
6. 添加 pytest 最小测试，验证健康检查接口可用。
7. 更新 `scripts/check_all.sh`，纳入后端测试命令。
8. 更新后端 README，说明如何安装依赖、运行服务和运行测试。
9. 同步更新架构和 API 文档，记录新增健康检查接口。
10. 运行检查脚本，记录验证结果。

## 验收标准

- 后端目录结构清晰，符合 `docs/architecture/backend.md` 的分层方向。
- 可以启动 FastAPI 应用。
- `GET /api/health` 返回成功响应。
- pytest 至少包含一个健康检查测试并通过。
- `scripts/check_all.sh` 可以运行后端测试。
- 文档与实际骨架保持一致。
- 未实现超出本次范围的业务功能。

## 验证方式

计划使用以下方式验证：

```bash
./scripts/check_all.sh
```

如需要单独验证后端，可在 `backend/` 目录运行后端测试命令。具体命令在任务实施时根据最终依赖管理方式写入 `backend/README.md`。

## 风险与注意事项

- 当前项目目录已移动到 `/Users/wenguang/project/dm/zhihui-meet`，后续工具工作目录需要使用新路径。
- 不要在本任务中引入过多业务代码。
- 如果选择依赖管理工具，需要保持简单，避免为了工具链牺牲早期推进速度。
- 若安装依赖需要网络，应先说明并请求确认。
- 新增 API 后必须同步更新 `docs/architecture/api.md`。

## 完成记录

完成日期：2026-07-07

实际完成内容：

- 创建 `backend/pyproject.toml`，声明 FastAPI、Pydantic、uvicorn、pytest、httpx 等依赖。
- 创建 `backend/app/` 最小 FastAPI 应用骨架。
- 新增 `GET /api/health` 健康检查接口。
- 新增 `backend/tests/test_health.py`，验证健康检查接口。
- 更新 `scripts/check_all.sh`，自动使用 `backend/.venv` 运行后端测试。
- 更新 `backend/README.md`、后端架构文档、API 文档、安全文档和 `CHANGELOG.md`。
- 新增 `.gitignore`，忽略 `.env`、虚拟环境和缓存文件。

验证结果：

```bash
./scripts/check_all.sh
```

结果：后端 pytest 收集 1 个测试，1 个通过。

后续建议：

- 下一个任务可以初始化数据库连接和 Alembic 骨架，但仍不急于实现完整业务。
- 也可以先创建前端 Vue 3 最小骨架，让前后端都具备基础运行入口。

