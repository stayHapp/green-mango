# 0059 签到场次与签到管理

## 任务名称

后台签到管理与多签到场次支持。

## 背景

当前系统以会议为单位保存唯一签到记录，同一嘉宾在同一会议只能签到一次。用户希望重新实现 0059，并确认后台管理中的“签到记录”是否可以改为“签到管理”，在同一入口中包含签到场次设置和签到记录查看；同时希望看到后面签到场次相较前面场次新增和减少的嘉宾。

## 用户确认状态

用户已要求再次实现 0059，并明确提出后台入口命名和功能组织方式。本计划已获得执行授权。

## 执行前必须读取

- `AGENTS.md`
- `docs/architecture/api.md`
- `docs/architecture/database.md`
- `docs/architecture/frontend.md`
- `docs/product/admin-workflow.md`
- `docs/product/check-in-flow.md`
- 当前相关后端模型、路由、服务和前端会议详情页

## 目标

1. 新增会议级签到场次模型和数据库迁移。
2. 历史签到记录迁移到默认签到场次，保留旧数据含义。
3. 管理员可以查看、创建、更新签到场次。
4. 管理员签到统计和明细按选中场次返回。
5. 管理员可以查看当前场次相对前一场次的新增签到和减少签到嘉宾。
6. 后台“签到记录”入口改为“签到管理”，内部包含“签到场次设置”和“签到记录查看”。
7. 工作人员现有扫码和人工签到流程继续可用，默认写入默认签到场次。

## 不在本次范围内的内容

1. 不修改工作人员端为手动选择签到场次。
2. 不实现签到撤销、补签审批、跨场次批量导入或高级报表。
3. 不修改嘉宾二维码 token 规则。

## 技术决策与待确认项

1. `check_in_sessions` 作为会议级场次表，默认场次由迁移和服务兜底创建。
2. `check_ins` 增加 `session_id`，唯一约束调整为 `session_id + guest_id`。
3. 后台场次对比默认使用当前选中场次与排序上一个场次。
4. 当前工作人员端仍写入默认场次；后续可扩展为工作人员选择当前签到场次。

## 注释要求

新增、补全、重构或修复代码时，必须遵守 `AGENTS.md` 的全局代码注释强制规范：

- 所有代码注释和 docstring 必须使用简体中文。
- 每个函数/方法必须有中文文档注释，说明功能、入参、返回值和异常/报错场景。
- 关键逻辑、判断分支、循环、复杂计算和重要约束必须添加中文注释说明意图。

## 涉及文件

- `backend/app/models/meeting.py`
- `backend/app/models/guest.py`
- `backend/app/models/__init__.py`
- `backend/alembic/versions/20260728_0011_add_check_in_sessions.py`
- `backend/app/schemas/admin_check_in.py`
- `backend/app/schemas/check_in.py`
- `backend/app/services/admin_check_ins.py`
- `backend/app/services/check_ins.py`
- `backend/app/api/routes/admin_check_ins.py`
- `backend/app/api/routes/check_ins.py`
- `frontend/src/types.ts`
- `frontend/src/api/adminCheckIns.ts`
- `frontend/src/api/staffCheckIns.ts`
- `frontend/src/components/AdminWorkspaceLayout.vue`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `docs/architecture/api.md`
- `docs/architecture/database.md`
- `docs/architecture/frontend.md`
- `docs/product/admin-workflow.md`
- `docs/product/check-in-flow.md`

## 分步计划

1. 增加后端模型、迁移和默认场次兜底服务。
2. 改造工作人员签到写入和查询，使其兼容默认场次。
3. 改造管理员签到统计、场次 CRUD（增删改查）和场次对比接口。
4. 改造前端 API 类型与后台“签到管理”页面。
5. 更新产品与架构文档。
6. 增加后端测试并运行后端测试、前端构建和差异检查。

## 验收标准

1. 升级后已有签到记录不会丢失，并归属到默认签到场次。
2. 管理员后台显示“签到管理”，并能看到场次设置、选中场次签到记录和对比结果。
3. 同一嘉宾可以在不同场次各签到一次，同一场次不能重复签到。
4. 现有工作人员扫码和人工签到接口继续可用。
5. 文档同步描述多场次签到和后台展示方式。

## 验证方式

1. 运行后端测试。
2. 运行前端构建。
3. 运行 `git diff --check`。
4. 检查数据库迁移当前版本与关键表结构。

## 风险与注意事项

1. 迁移需要调整唯一约束，必须兼容 SQLite 测试库和 PostgreSQL 本地库。
2. 后续如果要让工作人员端选择场次，需要再设计现场操作入口，避免误签到到错误场次。
3. 场次对比只能反映两个场次的签到名单差异，不等同于真实离场或缺席原因。

## 完成记录

已完成：

1. 增加 `check_in_sessions` 场次表和 `check_ins.session_id`，历史签到记录回填到默认场次。
2. 后端工作人员签到继续写入默认场次，同一场次内保持重复签到保护。
3. 后台新增签到场次列表、创建、更新接口，签到统计支持 `session_id` 并返回相邻场次新增/减少名单。
4. 后台“签到记录”改为“签到管理”，页面包含场次设置、场次记录查看和相邻场次差异。
5. 更新数据库、API、前端、安全、管理员工作流、签到流程和 MVP 文档。
6. 本地 PostgreSQL 已升级到 `20260728_0011`。

验证结果：

- 后端：`.venv/bin/python -m pytest`，65 passed，1 个既有 Starlette/httpx 弃用警告。
- 前端：`npm run build` 通过，保留既有 Rollup PURE 注解和包体积警告。
- 差异检查：`git diff --check` 通过。
