# 管理员会议管理最小 API

## 背景

当前后端已具备三端 MVP 的数据模型，但仅提供健康检查接口。前端 Mock 原型已验证管理员创建、查看和修改会议的流程，下一步需要先落地该流程对应的最小业务 API。

## 用户确认状态

用户已确认继续实现后端。本任务只实现管理员会议管理 API，不接入前端，也不实现完整认证体系。

## 执行前必须读取

- `AGENTS.md`
- `docs/product/mvp-scope.md`
- `docs/product/admin-workflow.md`
- `docs/architecture/api.md`
- `docs/architecture/database.md`
- `docs/architecture/security.md`
- 当前 active 执行计划

## 目标

- 实现管理员会议列表、创建、详情和修改接口。
- 确保管理员只能读取和修改被授权的会议。
- 通过测试覆盖创建、授权过滤、未授权访问和基础校验。

## 不在本次范围内的内容

- 不实现正式登录、密码校验、JWT（JSON Web Token）或刷新令牌。
- 不实现会议删除、嘉宾、工作人员、签到、导入导出 API。
- 不接入 Vue 前端真实请求。

## 技术决策与待确认项

- 正式认证上线前，管理员接口使用必填请求头 `X-Admin-Id` 表示当前管理员；服务端查询 `users` 表并校验角色为 `admin` 与账号启用状态。
- `X-Admin-Id` 仅为本地开发和接口测试过渡机制，后续认证任务必须替换，不能视为生产安全方案。
- 创建会议时写入 `meetings.created_by`，同时创建一条 `meeting_admins` 授权关系，并初始化默认 `meeting_settings`。

## 涉及文件

- `backend/app/api/`
- `backend/app/schemas/`
- `backend/app/services/`
- `backend/tests/`
- `docs/architecture/api.md`
- `docs/architecture/security.md`

## 分步计划

1. 定义会议请求、响应与错误语义，并实现过渡期管理员依赖。
2. 实现会议管理服务与路由。
3. 使用独立 SQLite 测试数据库覆盖授权和 CRUD 核心路径。
4. 更新 API 与安全文档，并运行测试和静态检查。

## 验收标准

- 管理员可创建会议、查看自己可管理的会议、查看详情并修改会议。
- 非管理员、禁用账号和无授权管理员无法访问管理员会议资源。
- 创建会议后自动生成管理员授权与默认会议设置。
- 所有接口返回结构受 Pydantic schema 校验。

## 验证方式

- 在 `backend` 目录使用 Python 3.12 虚拟环境运行 `pytest`。
- 使用临时 SQLite 数据库运行 `alembic upgrade head`。
- 运行 `git diff --check`。

## 风险与注意事项

- `X-Admin-Id` 可被客户端伪造，仅能用于本地开发和测试；不得部署为生产鉴权方案。

## 完成记录

- 已新增会议创建、更新和响应 schema，并校验会议结束时间必须晚于开始时间。
- 已新增开发期 `X-Admin-Id` 管理员依赖，校验账号存在、已启用且角色为 `admin`。
- 已实现管理员会议列表、创建、详情和修改路由与服务层；创建会议会同步创建默认会议设置和创建人授权。
- 已新增 4 项 API 测试，覆盖 CRUD 核心路径、会议授权过滤、非管理员或禁用账号拒绝访问和时间校验。
- 已运行 Python 3.12 下的 `pytest`，8 项测试全部通过。
