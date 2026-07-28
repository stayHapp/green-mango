# 会议服务访问权限配置

## 任务名称

执行计划 0058：会议服务访问权限配置。

## 背景

当前会议公开首页会展示五项会议服务入口，但未登录嘉宾点击任一服务时，前端统一弹出“请先完成身份核验”，然后引导到嘉宾登录页。后端会议服务详情接口也要求嘉宾 Bearer token，并校验嘉宾属于当前会议。

这个规则保证了内容只面向已核验嘉宾，但不适合所有服务项。例如会议日程、路线导航、天气提醒通常可以公开展示；会议资料或联系会务可能需要只对已登录嘉宾可见。因此需要把会议服务访问权限从固定规则改为会议级、服务项级配置。

本计划独立于 0059 多天签到模型。0058 只处理会议服务访问权限，不修改签到数据模型。

## 用户确认状态

用户已明确要求执行后续系统优化计划，本轮按仓库“一次只完成一个明确小任务”的规则先执行 0058。计划中的四项待确认内容均采用文档推荐方案。

## 执行前必须读取

执行前必须读取并遵守：

- `AGENTS.md`
- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `docs/architecture/frontend.md`
- `docs/product/meeting-assistant.md`
- `docs/product/guest-experience.md`
- `docs/product/guest-workflow.md`
- `docs/exec-plans/active/0058-meeting-service-access-control.md`

如果计划执行过程中发现 0059 多天签到计划同时在 active 目录中，先确认两个任务的修改边界。原则上 0058 不修改签到模型，0059 不修改会议服务权限。

## 目标

- 为每个会议服务增加访问级别配置：`公开可见` 或 `仅登录嘉宾可见`。
- 管理员端可以设置每个会议服务的访问级别。
- 公开首页点击公开服务时，未登录用户可以直接查看已发布内容。
- 公开首页点击仅登录服务时，提示用户先登录。
- 后端按访问级别同时控制公开接口和嘉宾接口，避免只靠前端判断。
- 未发布服务无论配置为公开还是仅登录，都不泄露草稿正文。
- 已登录嘉宾可以查看自己所属会议中所有已发布的会议服务。
- 产品文档、API 文档、数据库文档和前端架构文档同步更新。

## 不在本次范围内的内容

- 不修改会议服务五个固定入口类型，不新增、不删除、不排序入口。
- 不实现基于具体嘉宾身份、嘉宾字段、工作人员或管理员角色的细粒度内容权限。
- 不实现密码访问码、短信验证码、微信授权或外部分享权限。
- 不实现会议资料附件上传、文件预览或下载权限。
- 不修改会议服务正文结构；正文仍为纯文本，联系人仍使用现有 JSON 结构。
- 不修改签到、多天签到、工作人员签到或二维码签到逻辑。
- 不引入新的主要框架或基础设施。

## 技术决策与待确认项

### 已确认的技术方向

1. 每个 `meeting_assistant_features` 记录增加访问级别字段，建议命名为 `access_level`。
2. `access_level` 建议取值：
   - `public`：公开可见。
   - `guest`：仅登录嘉宾可见。
3. 历史数据迁移默认设置为 `guest`，保证当前权限行为不被升级为公开。
4. 管理员接口返回并保存 `access_level`。
5. 新增公开读取接口，供未登录用户读取公开且已发布的会议服务内容。
6. 现有嘉宾接口保留，已登录嘉宾仍可读取自己所属会议的已发布服务。
7. 未发布服务响应必须继续隐藏 `content`，公开接口尤其不能泄露草稿正文。

### 已采用的推荐方案

1. 历史会议服务默认权限：
   - 建议：全部默认为“仅登录嘉宾可见”，避免历史内容意外公开。
2. 管理员端权限控件位置：
   - 建议：放在每项会议服务编辑区的发布开关旁边，使用单选项“公开可见 / 仅登录嘉宾可见”。
3. 未登录用户访问“仅登录嘉宾可见”的服务时的处理方式：
   - 建议：前端弹窗提示登录；公开接口返回 401 或 403，文案为“该服务需要登录后查看。”。
4. 未发布但公开可见的服务，未登录用户是否看到未发布提醒：
   - 建议：可以看到 `unpublished_message`，但 `content` 必须为 `null`。这样与现有嘉宾端未发布体验一致。

## 注释要求

新增、补全、重构或修复代码时，必须遵守 `AGENTS.md` 的全局代码注释强制规范：

- 所有代码注释和 docstring 必须使用简体中文。
- 保留必要英文技术名词时，首次出现应括号标注中文释义。
- 每个函数/方法必须有中文文档注释，说明功能、入参、返回值和异常/报错场景。
- 关键逻辑、判断分支、循环、复杂计算和重要约束必须添加中文注释说明意图。
- 不写无信息量注释，不重复代码字面含义。

## 涉及文件

预计新增或修改：

- `backend/app/models/meeting.py`
- `backend/app/models/__init__.py`
- `backend/alembic/versions/202607xx_0010_add_meeting_assistant_access_level.py`
- `backend/app/schemas/meeting_assistant.py`
- `backend/app/services/meeting_assistant.py`
- `backend/app/api/routes/meeting_assistant.py`
- `backend/tests/test_admin_meetings.py`
- `backend/tests/test_guest_sessions.py`
- `frontend/src/types.ts`
- `frontend/src/api/meetingAssistant.ts`
- `frontend/src/api/sessions.ts`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `frontend/src/views/guest/GuestEntryView.vue`
- `frontend/src/views/guest/GuestAssistantFeatureView.vue`
- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `docs/architecture/frontend.md`
- `docs/product/meeting-assistant.md`
- `docs/product/guest-experience.md`
- `docs/product/guest-workflow.md`

## 建议数据模型

在 `meeting_assistant_features` 表增加：

| 字段 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `access_level` | varchar(32) | `guest` | 会议服务访问级别 |

建议约束：

- `access_level IN ('public', 'guest')`。
- 历史数据迁移时全部回填为 `guest`。
- 服务层创建默认五项服务时，默认 `access_level='guest'`。

不建议把访问权限放入 `meeting_settings.settings_json`，原因是权限属于每个服务项自身配置，放在 `meeting_assistant_features` 可避免跨表 JSON 读写和权限配置不同步。

## 建议 API 设计

### 管理员接口

保留现有路径：

```text
GET /api/admin/meetings/{meeting_id}/assistant-features
PATCH /api/admin/meetings/{meeting_id}/assistant-features/{feature_key}
```

调整内容：

- 响应增加 `access_level`。
- 更新请求增加可选 `access_level`。
- 后端校验 `access_level` 只能为 `public` 或 `guest`。

### 嘉宾接口

保留现有路径：

```text
GET /api/guest/meetings/{meeting_id}/assistant-features/{feature_key}
```

规则：

- 仍要求嘉宾登录。
- 已登录嘉宾属于当前会议时，可以查看该会议所有已发布服务。
- 未发布服务继续只返回未发布提醒，不返回正文。

### 公开接口

新增公开路径，供会议公开首页使用：

```text
GET /api/meetings/{meeting_id}/assistant-features/{feature_key}
```

规则：

- 会议必须已发布。
- 服务 `access_level='public'` 时，未登录用户可读取。
- 服务 `access_level='guest'` 时，返回需要登录的错误。
- 服务未发布时，返回未发布提醒，但 `content=null`。
- 草稿会议、无效会议、无效功能标识不得泄露服务正文。

## 分步计划

1. 梳理现有会议服务链路
   - 确认管理员编辑接口、嘉宾详情接口、公开首页入口和前端详情页路由。
   - 确认天气提醒、路线导航、联系会务是否存在独立接口或特殊渲染逻辑。

2. 新增数据库字段和迁移
   - 为 `meeting_assistant_features` 增加 `access_level`。
   - 历史数据默认回填为 `guest`。
   - 增加数据库检查约束。
   - 更新 ORM 模型和默认服务创建逻辑。

3. 更新后端 Schema 和服务
   - 管理员响应、更新请求增加 `access_level`。
   - 嘉宾响应可按需要增加 `access_level`，便于前端显示权限状态。
   - 新增公开读取服务方法，统一处理公开权限、发布状态和正文隔离。

4. 更新后端路由
   - 管理员接口支持读取和更新访问级别。
   - 嘉宾接口保持登录校验，但响应包含权限信息。
   - 新增公开会议服务详情接口。
   - 天气公开访问如涉及真实天气接口，应与天气服务发布状态和访问级别保持一致。

5. 补充后端测试
   - 管理员可保存 `public` 和 `guest`。
   - 非法 `access_level` 返回 422。
   - 历史默认权限为 `guest`。
   - 公开服务未登录可查看已发布正文。
   - 仅登录服务未登录不可查看正文。
   - 已登录嘉宾可查看仅登录服务。
   - 未发布服务无论权限如何都不返回正文。

6. 更新前端 API 类型
   - 增加 `accessLevel` 或 `access_level` 映射。
   - 增加公开会议服务读取方法。
   - 统一处理“需要登录后查看”的错误。

7. 更新管理员端页面
   - 在每项会议服务编辑区增加访问级别配置。
   - 默认显示“仅登录嘉宾可见”。
   - 保存时与正文、未发布提醒、发布状态一起提交。
   - 权限文案避免让管理员误以为未发布内容也会公开。

8. 更新公开首页与详情页
   - 公开首页点击公开服务时直接进入公开详情页或复用详情页公开模式。
   - 点击仅登录服务时继续提示登录。
   - 公开详情页调用公开接口。
   - 已登录嘉宾访问时可继续走嘉宾接口，避免公开接口权限影响已登录体验。

9. 同步文档
   - 更新数据库设计，记录 `access_level` 字段和约束。
   - 更新 API 文档，补充公开会议服务接口。
   - 更新前端架构文档，说明公开模式和嘉宾登录模式。
   - 更新会议服务产品文档，明确公开可见、仅登录嘉宾可见和未发布状态的关系。

10. 验证并整理状态
    - 运行后端测试。
    - 运行前端构建。
    - 执行 `git diff --check`。
    - 浏览器验证公开服务、仅登录服务、已登录嘉宾和未发布服务四类场景。

## 验收标准

- 管理员端每个会议服务都可以设置为“公开可见”或“仅登录嘉宾可见”。
- 公开服务未登录可查看已发布正文。
- 仅登录服务未登录时提示登录，且后端不返回正文。
- 已登录嘉宾可查看自己所属会议中所有已发布且有权限的服务。
- 未发布服务无论是否公开，都只返回未发布提醒，不泄露草稿正文。
- 草稿会议或无效会议的公开访问不泄露会议服务正文。
- 天气、路线、联系会务等特殊服务与访问级别规则一致。
- API、数据库、产品和前端架构文档完成同步。

## 验证方式

后端验证：

```bash
cd /Users/wenguang/project/dm/green-mango
backend/.venv/bin/alembic upgrade head
backend/.venv/bin/pytest -q
```

前端验证：

```bash
cd /Users/wenguang/project/dm/green-mango/frontend
npm run build
```

代码检查：

```bash
cd /Users/wenguang/project/dm/green-mango
git diff --check
```

浏览器人工验证：

1. 管理员进入会议详情，打开会议服务配置。
2. 将会议日程设为“公开可见”并发布。
3. 将会议资料设为“仅登录嘉宾可见”并发布。
4. 退出嘉宾登录状态，在会议公开首页点击会议日程，确认可直接查看正文。
5. 未登录状态点击会议资料，确认提示先登录。
6. 登录嘉宾后点击会议资料，确认可查看正文。
7. 将天气提醒设为未发布且公开可见，确认未登录状态只看到未发布提醒，不看到草稿正文。

## 风险与注意事项

- 历史数据默认必须是 `guest`，否则可能把原本只给嘉宾看的资料公开。
- 前端不能只靠按钮判断权限；公开接口必须由后端最终控制。
- 未发布状态优先级高于公开权限，任何接口都不能返回未发布正文。
- 天气提醒存在独立天气接口，需要确认公开访问是否也允许读取天气数据；如果天气正文公开但实时天气接口仍要求登录，会造成体验不一致。
- 管理员端文案必须说明“公开可见”只影响已发布内容，未发布草稿不会公开。
- 与 0059 同时实施时，迁移版本号需要避免冲突。

## 完成记录

已完成。

- 数据库迁移 `20260728_0010` 为五项会议服务增加 `access_level` 字段和检查约束，历史及新增配置默认使用 `guest`。
- 管理员接口和页面支持逐项配置“公开可见”或“仅登录嘉宾可见”，并在列表展示当前权限。
- 新增公开会议服务详情与公开天气接口；草稿会议和仅登录服务由后端拦截。
- 公开会议首页会先检查单项服务权限：公开服务直接进入复用详情页，受限服务提示完成当前会议身份核验。
- 已登录嘉宾继续通过嘉宾接口查看所属会议服务，不受公开访问级别限制。
- 未发布响应同时隐藏 `content` 和 `contacts`，修复联系人草稿可能泄露的问题。
- 浏览器验证时发现日程页遗漏导入 `Clock` 图标，已同步修复运行时警告。
- 已同步数据库、API、前端架构、MVP 范围、功能地图、会议服务及嘉宾体验与工作流文档。
- 本地 PostgreSQL 已执行迁移并确认当前版本为 `20260728_0010 (head)`。
- 后端测试结果：`64 passed`，仅保留第三方 `httpx`/Starlette 弃用警告。
- 前端生产构建通过，仅保留第三方 PURE 注释和既有大包体积提示。
- `git diff --check` 通过。
- 浏览器在隔离验收环境验证通过：管理员保存访问权限、未登录访问公开日程、受限会议资料登录提示、390×844 移动端日程展示和控制台无相关错误。
- 0059 多天签到计划保持 active，未在本轮修改签到模型。
