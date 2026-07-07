# 创建核心数据模型与首个 Alembic 迁移

## 任务名称

创建第一版 MVP 核心数据模型与首个 Alembic 迁移。

## 背景

计划 1 已完成后端 FastAPI 最小骨架。计划 2 已完成 Python 3.12、SQLAlchemy 2.x、Alembic、`pydantic-settings`、数据库连接和迁移骨架。

当前数据库文档已经定义第一版核心表：`users`、`meetings`、`meeting_settings`、`registration_fields`、`registrations`、`registration_values`，但代码中尚未创建 ORM 模型，也没有业务表迁移版本。

本任务的目标是把概念性数据库设计落成可迁移的 SQLAlchemy 模型和首个 Alembic migration，为后续会议管理 API 和报名 API 做准备。

## 目标

本次任务完成后，应具备：

- SQLAlchemy ORM 模型：`User`、`Meeting`、`MeetingSetting`、`RegistrationField`、`Registration`、`RegistrationValue`。
- 模型字段与 `docs/architecture/database.md` 保持一致。
- 模型关系包含必要的外键和关系声明。
- 首个 Alembic 迁移版本，创建上述核心表。
- 数据库测试覆盖核心表创建和基础关系约束。
- 数据库文档同步更新为“已实现模型与迁移”。
- 保持 `./scripts/check_all.sh` 通过。

## 不在本次范围内的内容

- 不实现会议管理 API。
- 不实现报名字段配置 API。
- 不实现报名提交 API。
- 不实现管理员登录、密码哈希或权限系统。
- 不写业务 service 层逻辑。
- 不初始化前端。
- 不连接真实 PostgreSQL 服务。
- 不插入种子数据。
- 不做复杂索引优化，除必要唯一约束和外键约束外保持简洁。

## 已确认技术方案

- Python：3.12
- ORM：SQLAlchemy 2.x
- 迁移：Alembic
- 本地数据库：SQLite
- 正式数据库：PostgreSQL
- 配置：`pydantic-settings`
- 测试：pytest

## 注释要求

新增或修改代码时必须补充有价值的注释或 docstring：

- 模块级 docstring 说明该模块职责。
- 关键 ORM 模型用 docstring 说明业务含义。
- 非显而易见的字段、关系、约束需要注释。
- 注释解释设计意图、业务边界或兼容性原因，不重复代码字面含义。
- 不写无信息量注释，例如“创建变量”“返回结果”。

## 涉及文件

预计新增或修改：

- `backend/app/models/user.py`
- `backend/app/models/meeting.py`
- `backend/app/models/registration.py`
- `backend/app/models/__init__.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/<revision>_create_core_tables.py`
- `backend/tests/test_models.py`
- `docs/architecture/database.md`
- `docs/architecture/backend.md`
- `CHANGELOG.md`
- 本执行计划文件，完成后移入 `docs/exec-plans/completed/`

## 分步计划

1. 执行前状态检查。
   - 查看 `git status --short`。
   - 确认 `docs/exec-plans/active/` 中只有当前计划。
   - 确认 `backend/.venv/bin/python --version` 为 Python 3.12.x。
   - 运行一次 `./scripts/check_all.sh`，确认计划 2 的基线仍通过。

2. 细化表结构实现约定。
   - 确定主键使用整数自增主键。
   - 时间字段使用 timezone-aware `DateTime`。
   - `created_at`、`updated_at` 使用 Python/SQLAlchemy 默认值。
   - JSON 配置字段使用 SQLAlchemy `JSON` 类型。
   - `registration_fields.key` 在同一会议内唯一。
   - `meeting_settings.meeting_id` 对会议一对一唯一。

3. 创建 ORM 模型文件。
   - `user.py` 定义 `User`。
   - `meeting.py` 定义 `Meeting` 和 `MeetingSetting`。
   - `registration.py` 定义 `RegistrationField`、`Registration`、`RegistrationValue`。
   - 使用 SQLAlchemy 2.x `Mapped` 和 `mapped_column`。
   - 添加必要 relationship。
   - 添加模块 docstring、模型 docstring 和关键字段注释。

4. 更新模型导出。
   - 更新 `backend/app/models/__init__.py`。
   - 确保 Alembic env 能导入全部模型，使 `Base.metadata` 包含所有表。

5. 更新 Alembic env。
   - 在 `backend/alembic/env.py` 中导入 `app.models`。
   - 保持 `target_metadata = Base.metadata`。
   - 不在 env.py 中写业务逻辑。

6. 生成首个迁移版本。
   - 使用 Alembic 创建迁移文件。
   - 迁移文件名建议为 `create_core_tables`。
   - 检查自动生成结果，不盲目信任 autogenerate。
   - 确认 `upgrade()` 创建 6 张核心表。
   - 确认 `downgrade()` 按外键依赖逆序删除表。

7. 新增模型和迁移测试。
   - 使用临时 SQLite 数据库。
   - 验证 `Base.metadata.create_all()` 能创建核心表。
   - 验证核心表名集合包含 6 张表。
   - 验证关键唯一约束或索引至少可被 inspector 读取。
   - 保持测试不依赖本地 `dev.db`。

8. 运行验证。
   - 运行 `./scripts/check_all.sh`。
   - 运行 `cd backend && ./.venv/bin/alembic upgrade head`。
   - 运行 `cd backend && ./.venv/bin/alembic current`。
   - 如迁移命令生成本地 `dev.db`，确认该文件被 `.gitignore` 忽略。

9. 更新文档。
   - 更新 `docs/architecture/database.md`，标记核心表模型和首个迁移已实现。
   - 补充关键约束：一对一设置、同会议字段 key 唯一、外键关系。
   - 更新 `docs/architecture/backend.md`，说明 models 目录已包含核心模型。
   - 更新 `CHANGELOG.md`。

10. 完成记录与归档。
    - 在本计划“完成记录”中记录实际完成内容、验证命令和结果。
    - 将本文件移动到 `docs/exec-plans/completed/`。

## 验收标准

- `backend/app/models/` 中存在第一版核心 ORM 模型。
- `Base.metadata.tables` 包含：`users`、`meetings`、`meeting_settings`、`registration_fields`、`registrations`、`registration_values`。
- Alembic 存在首个业务迁移版本。
- `alembic upgrade head` 可在本地 SQLite 上成功执行。
- `./scripts/check_all.sh` 通过。
- 数据库文档与模型实现一致。
- 新增代码包含必要 docstring 或注释。
- 没有实现业务 API、认证、前端或超出本任务范围的功能。

## 验证方式

计划运行：

```bash
backend/.venv/bin/python --version
./scripts/check_all.sh

cd backend
./.venv/bin/alembic upgrade head
./.venv/bin/alembic current
```

必要时检查表结构：

```bash
cd backend
./.venv/bin/python -m pytest tests/test_models.py
```

## 风险与注意事项

- 当前项目路径为 `/Users/wenguang/project/dm/zhihui-meet`，不在当前工具默认 writable root 内，文件写入需要提升权限。
- 迁移文件必须人工检查，不能只依赖 Alembic autogenerate。
- SQLite 和 PostgreSQL 的 JSON、DateTime、约束表现存在差异，本任务只保证本地 SQLite 可验证，正式 PostgreSQL 兼容性在后续部署计划中验证。
- 不要在本任务中实现密码哈希或登录逻辑；`users.password_hash` 只是字段，不代表认证能力已完成。
- 不要在测试中依赖本地 `backend/dev.db`，避免测试污染开发数据库。

## 完成记录

完成日期：2026-07-07

实际完成内容：

- 新增核心 ORM 模型：`User`、`Meeting`、`MeetingSetting`、`RegistrationField`、`Registration`、`RegistrationValue`。
- 新增模型文件：`backend/app/models/user.py`、`backend/app/models/meeting.py`、`backend/app/models/registration.py`。
- 更新 `backend/app/models/__init__.py`，统一导出并注册模型。
- 更新 `backend/alembic/env.py`，导入 `app.models`，确保 Alembic 可读取完整 `Base.metadata`。
- 新增首个业务迁移：`backend/alembic/versions/20260707_0001_create_core_tables.py`。
- 更新 `backend/tests/test_db.py`，适配核心表已存在的状态。
- 新增 `backend/tests/test_models.py`，验证核心表 metadata 和关键唯一约束。
- 更新 `docs/architecture/database.md`，记录已实现表、约束和迁移版本。
- 更新 `docs/architecture/backend.md`，记录 models 和迁移状态。
- 更新根 README 和 `CHANGELOG.md`。
- 新增代码已包含模块 docstring、模型 docstring 和关键字段/约束注释。

验证结果：

```bash
backend/.venv/bin/python --version
# Python 3.12.13

./scripts/check_all.sh
# 4 passed, 1 warning

cd backend
./.venv/bin/alembic upgrade head
# Running upgrade  -> 20260707_0001, create core tables

cd backend
./.venv/bin/alembic current
# 20260707_0001 (head)
```

注意事项：

- 当前只完成数据模型和迁移，不包含业务 API、认证、前端或 service 层逻辑。
- `users.password_hash` 只是数据字段，密码哈希生成和校验逻辑尚未实现。
- `backend/dev.db` 可能由 Alembic 本地验证生成，已被 `.gitignore` 忽略。
- pytest 仍有一个 FastAPI/Starlette TestClient 依赖弃用警告，不影响当前验证结果。
