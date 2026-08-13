# 执行计划 0078：仅嘉宾可见服务的未登录提示支持后台自定义

## 任务名称

将嘉宾端未登录点击「仅登录嘉宾可见」会议服务时的弹窗提示改为后台可自定义，默认文案更新为「此项服务仅对已登录参会人员开放」。

## 背景

当前未登录嘉宾在公开会议首页点击受限服务时，弹窗标题与内容写死在前端（`GuestEntryView.vue`）。管理员希望按会议自定义该提示，并修改默认文案。会议助手表已有「未发布提醒」的自定义机制（`unpublished_message`），本次按同样模式为受限访问提示新增独立字段，避免复用未发布提醒造成语义混淆。

## 用户确认状态

已确认。用户指定默认文案为「此项服务仅对已登录参会人员开放」，并要求现在实现后台自定义能力。

## 执行前必须读取

- `AGENTS.md`
- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `docs/architecture/frontend.md`
- 当前 active 执行计划

## 目标

- `meeting_assistant_features` 新增 `guest_only_message` 字段，默认文案为「此项服务仅对已登录参会人员开放」。
- 管理员可在会议详情「会议助手」编辑弹窗中按会议配置该提示，保存后立即生效。
- 嘉宾端公开首页点击受限服务时展示后台配置的提示，未配置或读取失败时使用默认文案兜底。
- 数据库与 API 文档同步更新，提供 Alembic 迁移与后端测试。

## 不在本次范围内的内容

- 不改变「未发布提醒」的现有行为。
- 不修改已发布服务正文、联系人等配置的存取逻辑。
- 不提供按功能、按嘉宾类型之外的其他精细化提示配置。

## 技术决策与待确认项

- 字段命名 `guest_only_message`，与访问级别 `guest` 语义对应；长度与未发布提醒一致（500）。
- 管理员更新接口中该字段可选（兼容旧客户端），仅在传入时更新；公开读取通过新增公开接口返回五项服务的提示映射，不暴露正文。
- 旧数据通过迁移 `server_default` 回填默认文案。

## 注释要求

所有新增、修改代码的注释和 docstring 使用简体中文，遵守 `AGENTS.md` 全局注释规范。

## 涉及文件

新增：

- `backend/alembic/versions/20260812_0016_add_guest_only_message.py`
- `docs/exec-plans/active/0078-customizable-guest-only-message.md`

修改：

- `backend/app/models/meeting.py`
- `backend/app/schemas/meeting_assistant.py`
- `backend/app/services/meeting_assistant.py`
- `backend/app/api/routes/meeting_assistant.py`
- `backend/tests/test_meeting_assistant.py`
- `frontend/src/types.ts`
- `frontend/src/api/meetingAssistant.ts`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `frontend/src/views/guest/GuestEntryView.vue`
- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `CHANGELOG.md`

## 分步计划

1. 后端：模型新增字段、Schema、服务更新与公开提示接口。
2. 迁移：新增 Alembic 迁移并回填默认文案。
3. 前端：类型与 API 封装、后台编辑表单、嘉宾端弹窗读取配置。
4. 测试与构建：补充后端测试，运行 pytest 与前端构建。
5. 文档：更新数据库、API、CHANGELOG 并归档执行计划。

## 验收标准

1. 后端测试全部通过，前端构建成功。
2. 管理员在会议助手编辑弹窗可填写并保存「仅嘉宾可见提示」，再次打开仍保留。
3. 未登录嘉宾点击受限服务时弹窗展示后台配置的提示；未配置时展示默认文案。
4. 数据库与 API 文档已同步，迁移可正常升级与回退。
