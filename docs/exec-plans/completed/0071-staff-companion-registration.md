# 执行计划 0071：工作人员端同行人员登记

## 任务名称

工作人员端同行人员登记（同行嘉宾绑定主嘉宾，导出签到表可见）。

## 背景

嘉宾可能携带家属、助理、司机等同行人员参会，但平台不宜让已报名嘉宾自行补充同行人员信息。经用户确认，由工作人员端在签到现场登记：为已报名嘉宾添加同行人员，同行人员以正式嘉宾记录保存并绑定主嘉宾，导出签到表和嘉宾状态表时可查看「嘉宾类型」与「陪同嘉宾」。

## 用户确认状态

用户已明确「可以开始实现」，交互细节已确认：

- 工作人员端工作台新增「同行登记」页签，页面为嘉宾列表：已签到嘉宾按签到时间倒序在上，未签到嘉宾在下，顶部搜索框常驻。
- 每张嘉宾卡片提供「添加同行」按钮。
- 点击按钮弹出居中弹窗（不是底部抽屉），主嘉宾由卡片自动带出并锁定，不重复选择。
- 弹窗填写同行人员姓名、手机号（必填）、单位（选填）和备注（自由文本，默认留空，由工作人员自行填写）。

## 执行前必须读取

- `AGENTS.md`
- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `docs/product/staff-workflow.md`
- `docs/exec-plans/template.md`

## 目标

- 数据库支持同行嘉宾与主嘉宾的绑定关系。
- 工作人员端可登记同行人员、查询某主嘉宾的同行人员列表。
- 工作人员端工作台新增「同行登记」交互（列表 + 居中弹窗）。
- 签到明细和嘉宾状态导出包含「嘉宾类型」「陪同嘉宾」列；来源标签支持「同行登记」。
- 后端测试覆盖核心规则并通过；前端构建通过。

## 不在本次范围内的内容

- 嘉宾端登录限制（同行嘉宾是否允许登录嘉宾端）默认不调整，保持与普通嘉宾一致。
- 同行嘉宾的删除接口（沿用现有嘉宾软停用能力）。
- 多级同行（同行嘉宾再携带同行人员）不做，服务层禁止链式绑定。
- 同行嘉宾的独立二维码展示与嘉宾端体验优化。

## 技术决策与待确认项

- 同行人员复用 `guests` 表：新增 `companion_of_id`（自引用外键，可空）与 `companion_note`（自由文本备注）。
- 新增嘉宾来源值 `companion_registration`，导出与后台列表可区分。
- 复用现有 `create_guest` 的二维码生成、身份唯一校验和动态字段保存逻辑。
- 排序由前端基于接口返回的签到时间完成：已签到按时间倒序在前，未签到在后。
- 无待确认项；上述决策已获用户确认或属于合理默认。

## 注释要求

新增、补全、重构或修复代码时，必须遵守 `AGENTS.md` 的全局代码注释强制规范：所有注释与 docstring 使用简体中文，每个函数/方法带完整中文文档注释，关键逻辑添加单行中文注释。

## 涉及文件

新增：

- `docs/exec-plans/active/0071-staff-companion-registration.md`
- `backend/alembic/versions/20260731_0015_add_guest_companions.py`
- `backend/app/services/companions.py`
- `backend/tests/test_companions.py`

修改：

- `backend/app/models/guest.py`
- `backend/app/schemas/check_in.py`
- `backend/app/schemas/guest.py`
- `backend/app/api/routes/check_ins.py`
- `backend/app/services/admin_guests.py`
- `backend/app/services/excel_files.py`
- `frontend/src/api/staffCheckIns.ts`
- `frontend/src/views/staff/StaffCheckInView.vue`
- `docs/architecture/database.md`
- `docs/architecture/api.md`

## 分步计划

1. 编写本执行计划。
2. 新增 Alembic 迁移 `0015`：`guests` 增加 `companion_of_id`（自引用外键、索引、`ondelete=SET NULL`）与 `companion_note`；同步更新 `Guest` 模型与自关联关系。
3. 后端服务与接口：
   - `create_guest` 支持可选 `companion_of_id` 与 `companion_note`；
   - 新增 `companions.py` 服务：校验主嘉宾、创建同行嘉宾、查询同行列表、统计各主嘉宾同行人数；
   - `check_ins.py` 新增 `POST /staff/meetings/{meeting_id}/companions` 与 `GET /staff/meetings/{meeting_id}/companions`；
   - 工作人员嘉宾搜索响应增加同行人数、是否同行、主嘉宾姓名；
   - 管理端嘉宾响应增加同行字段。
4. 导出调整：签到明细与嘉宾状态表增加「嘉宾类型」「陪同嘉宾」列，来源标签增加「同行登记」。
5. 新增 `tests/test_companions.py` 覆盖登记、校验、查询、导出。
6. 前端：`staffCheckIns.ts` 增加同行接口与字段；`StaffCheckInView.vue` 增加「同行登记」模式（分组列表、添加按钮、居中弹窗表单）。
7. 更新 `docs/architecture/database.md` 与 `docs/architecture/api.md`。
8. 整体验证：后端 pytest 全绿、前端 `npm run build` 通过。

## 验收标准

- 工作人员可搜索嘉宾并为其登记同行人员，同行记录正确关联主嘉宾。
- 同行登记页已签到嘉宾按时间倒序在上、未签到在下。
- 弹窗居中，主嘉宾锁定只读，备注为自由文本且默认留空。
- 已登记同行的嘉宾卡片显示人数徽标，可展开查看同行人员。
- 签到明细与嘉宾状态导出包含「嘉宾类型」「陪同嘉宾」列，同行人员来源显示「同行登记」。
- 链式同行、跨会议绑定、身份重复均被拒绝并返回中文错误。
- 后端测试与前端构建通过。

## 验证方式

- 后端：`.venv/bin/python -m pytest -q`，新增同行登记用例全部通过。
- 前端：`cd frontend && npm run build` 通过。
- 手工：工作人员登录 → 同行登记页 → 为嘉宾添加同行 → 后台导出签到表核对两列内容。

## 风险与注意事项

- 自引用外键删除语义：主嘉宾被硬删除时同行嘉宾的 `companion_of_id` 置空；实际流程以软停用为主。
- 现有「同会议姓名+手机号唯一」索引覆盖同行嘉宾，重复登记由该约束兜底。
- 前端 `StaffCheckInView.vue` 模式较多，新增模式需避免影响扫码与手动签到逻辑。
- 导出列顺序变化属于兼容性增强，不破坏已有列含义。

## 完成记录

实现完成，验证结果：

- 数据库：Alembic 迁移 `20260731_0015` 在全新 SQLite 库上从 `0014` 升级成功；`Guest` 模型增加 `companion_of_id`、`companion_note` 与自关联关系。
- 后端：新增 `services/companions.py`，工作人员端新增 `POST /staff/meetings/{id}/companions` 与 `GET /staff/meetings/{id}/companions`；嘉宾搜索响应携带 `companion_count`、`is_companion`、`companion_of_name`；签到明细与嘉宾状态导出新增「嘉宾类型」「陪同嘉宾」列，来源标签支持「同行登记」。
- 追加确认：登记同行人员成功后自动为该同行嘉宾写入当前有效场次手动签到，执行工作人员为登记人；会议已结束时拒绝登记。成功提示文案同步更新。
- 测试：`tests/test_companions.py` 新增 8 个用例，覆盖登记成功（含自动签到断言）、无效/跨会主嘉宾、链式同行、身份重复、列表筛选、导出字段、越权拒绝与会议结束拒绝；全量 `pytest` 83 通过。
- 前端：`StaffCheckInView.vue` 新增「同行登记」模式（已签到按时间倒序在上、未签到在下、搜索框常驻、嘉宾卡片添加按钮、居中弹窗登记）；备注为自由文本默认留空；`npm run build` 通过。
- 文档：`docs/architecture/database.md` 与 `docs/architecture/api.md` 已同步更新。

后续建议：管理端嘉宾列表展示同行标记与陪同嘉宾列；评估同行嘉宾是否允许登录嘉宾端。
