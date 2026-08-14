# 执行计划 0081：后台批量停用嘉宾与移除登录页默认填充按钮

## 任务名称

管理后台嘉宾列表支持多选批量停用；同时移除嘉宾登录页的「默认填充」按钮功能。

## 背景

嘉宾数量较多时逐个删除效率低，需要批量停用。另外用户评估后认为登录页公开默认手机号存在安全隐患，要求移除「默认填充」按钮；无手机号嘉宾仍由导入时自动填充默认号，登录时由会务告知号码。

## 用户确认状态

已确认：移除默认填充按钮；后台提供批量删除嘉宾功能。

## 执行前必须读取

- `AGENTS.md`
- `docs/architecture/api.md`
- `backend/app/api/routes/admin_resources.py`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`

## 目标

- 新增批量停用接口：按嘉宾 ID 列表一次软停用，保留历史签到数据，与单个删除语义一致。
- 管理后台嘉宾表格支持多选，提供「批量删除」按钮并二次确认，完成后刷新列表。
- 移除嘉宾登录页「默认填充」按钮、常量、函数与相关样式。

## 不在本次范围内的内容

- 不修改导入默认手机号与导出「未提供」逻辑。
- 不提供硬删除；批量删除均为软停用（is_active=false）。
- 不改动嘉宾端登录匹配逻辑。

## 技术决策与待确认项

- 批量接口使用 `POST /api/admin/meetings/{meeting_id}/guests/batch-deactivate`，请求体为嘉宾 ID 列表；任一 ID 不存在或不属于会议时整批拒绝。
- 前端多选仅允许正式嘉宾行（申请行不可选），避免误停用报名申请。

## 注释要求

所有新增、修改代码的注释和 docstring 使用简体中文，遵守 `AGENTS.md` 全局注释规范。

## 涉及文件

新增：

- `docs/exec-plans/active/0081-batch-delete-guests-and-remove-default-phone-button.md`

修改：

- `backend/app/schemas/guest.py`
- `backend/app/services/admin_resources.py`
- `backend/app/api/routes/admin_resources.py`
- `backend/tests/test_admin_meetings.py`（或新增批量停用测试）
- `frontend/src/api/adminGuests.ts`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `frontend/src/views/guest/GuestLoginView.vue`
- `frontend/src/styles.css`
- `docs/architecture/api.md`
- `docs/architecture/frontend.md`
- `CHANGELOG.md`

## 分步计划

1. 后端：批量停用 Schema、服务与路由。
2. 前端：嘉宾列表多选与批量删除操作，API 封装。
3. 前端：移除登录页默认填充按钮及相关代码。
4. 测试与构建：补充批量停用测试，运行 pytest 与前端构建。
5. 文档与归档：更新 API、前端文档与 CHANGELOG，归档执行计划。

## 验收标准

1. 后端测试与前端构建通过。
2. 批量停用接口可一次停用多位嘉宾，重复身份不再占用唯一约束。
3. 管理后台可多选嘉宾并批量删除，申请行不可选，删除前有确认提示。
4. 嘉宾登录页不再出现「默认填充」按钮。
