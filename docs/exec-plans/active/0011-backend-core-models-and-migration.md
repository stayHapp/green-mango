# 后端核心模型与数据库迁移

## 背景

前端已用 Mock 数据验证管理员、嘉宾、工作人员三端的会议管理与签到闭环；但后端仍使用早期“报名字段与报名记录”数据模型，仅提供健康检查接口，无法支撑当前 MVP。

## 用户确认状态

用户已确认开始后端开发。当前任务仅处理新 MVP 所需的数据模型、数据库迁移、模型测试和架构文档，不实现业务 API。

## 执行前必须读取

- `AGENTS.md`
- `docs/product/mvp-scope.md`
- `docs/product/client-model.md`
- `docs/product/admin-workflow.md`
- `docs/product/guest-workflow.md`
- `docs/product/staff-workflow.md`
- `docs/architecture/database.md`
- `docs/architecture/api.md`
- 当前 active 执行计划

## 目标

- 通过新的 Alembic 前向迁移扩展现有数据库，使其能够表示当前 MVP 的会议、管理员、工作人员、嘉宾、动态嘉宾字段和签到关系。
- 补充 SQLAlchemy 模型、关系和关键唯一性约束。
- 为新增模型与约束编写 pytest 测试，并同步数据库、后端和 API 文档。

## 不在本次范围内的内容

- 不删除或重写已提交的首个迁移。
- 不实现认证、密码哈希策略、会话令牌、权限中间件或业务 API。
- 不接入 Excel 上传、二维码图像生成、导出任务和真实前端联调。

## 技术决策与待确认项

- 使用前向迁移保留 `20260707_0001_create_core_tables`，避免改写已共享的迁移历史。
- 保留早期 `registration_*` 表作为历史基线；新增面向当前 MVP 的 `guest_*` 表，不在本任务迁移旧报名数据。
- `users` 增加角色、手机号、启用状态等基础账号属性；管理员与工作人员均使用该表。
- 新增 `meeting_admins` 和 `staff_meetings` 表表达多对多授权关系。
- 新增 `guests`、`guest_fields`、`guest_values` 与 `check_ins`；签到以 `guest_id` 唯一约束保证每位嘉宾每场会议只能签到一次。
- 会议二维码 token 仅保存不可逆或随机凭证标识；具体签发与校验逻辑留给后续业务服务实现。

## 涉及文件

- `backend/app/models/`
- `backend/alembic/versions/`
- `backend/tests/`
- `docs/architecture/database.md`
- `docs/architecture/backend.md`
- `docs/architecture/api.md`

## 分步计划

1. 审阅现有首个迁移、数据库会话与模型测试，明确可安全扩展的表结构。
2. 定义当前 MVP 的 ORM 模型、关联关系、索引与关键约束。
3. 新增 Alembic 前向迁移，并更新模型 metadata 测试。
4. 更新架构文档，明确已实现与后续 API 边界。
5. 运行 Alembic 升级与 pytest 验证。

## 验收标准

- 新数据库可升级至最新版本，且不修改既有迁移。
- 会议可关联多个管理员和工作人员。
- 嘉宾可关联会议、字段值与二维码凭证。
- 数据库保证同一嘉宾仅有一条签到记录，嘉宾字段 key 在同一会议内唯一。
- ORM metadata 与迁移结构的关键表、列、索引和约束有自动化测试。
- 数据库与 API 文档与实现状态一致。

## 验证方式

- 在 `backend` 目录运行 `alembic upgrade head`。
- 在 `backend` 目录运行 `pytest`。
- 运行 `git diff --check`。

## 风险与注意事项

- 这是共享仓库的基础数据结构调整；前端并行修改不应改动本分支的后端模型和数据库文档。
- SQLite 与 PostgreSQL 对部分索引和约束的行为存在差异，迁移应只使用两者均支持的基础能力。

## 完成记录

- 已保留 `20260707_0001_create_core_tables` 作为历史基线，并新增 `20260715_0002_add_meeting_guest_checkin_models` 前向迁移。
- 已扩展 `users` 的角色、手机号和启用状态，并新增会议管理员、工作人员授权、嘉宾字段、嘉宾、嘉宾字段值和签到 ORM 模型。
- 已为会议授权、嘉宾字段 key、嘉宾二维码 token、嘉宾字段值和单次签到添加关键唯一约束或索引。
- 已更新数据库、后端和 API 架构文档，明确新模型已实现而业务 API 仍待开发。
- 已在 Python 3.12 虚拟环境运行 `pytest`，4 项测试全部通过；已在临时 SQLite 数据库执行 `alembic upgrade head`，版本成功升级至 `20260715_0002`。
