## 任务名称

补齐本地嘉宾服务前端入口与自主报名流程。

## 背景

现有“知会”已经具备嘉宾登录、会议首页、个人签到二维码和五项会议服务，但会议专属入口会直接进入登录表单，尚未形成参考网站所体现的“活动首页—参会登录/自主报名—嘉宾中心”完整前端闭环。本任务在不依赖外部网站、不复制其代码的前提下，复用当前 Vue 3 与 FastAPI 接口完成本地实现。

## 用户确认状态

用户已明确要求在本地生成一套同类前端，可以开始实施。

## 执行前必须读取

执行前已读取并遵守：

- `AGENTS.md`
- `docs/product/guest-workflow.md`
- `docs/product/guest-experience.md`
- `docs/product/meeting-assistant.md`
- `docs/architecture/overview.md`
- `docs/architecture/api.md`
- `docs/architecture/database.md`
- Sites 构建技能及认证参考说明

## 目标

- 增加会议专属活动入口首页，展示会议名称、时间、地点、简介和登录/报名操作。
- 增加公开自主报名页，提交姓名、手机号、单位和职务后展示待审核结果。
- 保留现有嘉宾登录、会议首页、签到二维码和会议服务页面，并串联成完整路由。
- 继续使用当前 FastAPI 接口，不依赖参考网站运行。
- 保持手机端优先、桌面端居中的本地前端视觉。

## 不在本次范围内的内容

- 不复制或反编译参考网站的源代码、品牌与素材。
- 不实现外部网站数据同步。
- 不新增主要框架、短信验证码、文件上传或新数据库结构。
- 不修改管理员端和工作人员端业务流程。
- 不发布到公网。

## 技术决策与待确认项

- 继续使用 Vue 3、Vue Router、Element Plus、Axios 和现有 FastAPI API。
- 会议短链接 `/meetings/:id` 改为活动入口首页；登录页继续使用 `/guest/login?meetingId=...`。
- 报名页首版使用后端已支持的固定字段：姓名、手机号、单位、职务；动态报名字段留待后续单独任务。
- 报名成功后只展示“等待审核”，不自动创建嘉宾会话。
- 当前无待确认项。

## 注释要求

新增和修改的函数必须使用完整简体中文文档注释，说明功能、入参、返回值和异常；关键分支补充中文意图注释。

## 涉及文件

- `frontend/src/router/index.ts`
- `frontend/src/views/guest/GuestEntryView.vue`
- `frontend/src/views/guest/GuestRegisterView.vue`
- `frontend/src/views/guest/GuestLoginView.vue`
- `frontend/src/api/guestApplications.ts`
- `frontend/src/api/sessions.ts`
- `frontend/src/types.ts`
- `frontend/src/styles.css`
- `docs/product/guest-workflow.md`
- `docs/exec-plans/active/0045-local-guest-service-frontend.md`

## 分步计划

1. 扩展公开会议前端类型并新增报名 API 适配层。
2. 实现活动入口首页和自主报名页，串联登录与会议首页路由。
3. 补充移动端视觉、可访问状态和表单校验。
4. 更新产品工作流文档并执行前端构建验证。

## 验收标准

- 打开 `/meetings/:id` 可以查看公开会议概要。
- 已开放报名的会议显示“参会登录”和“申请报名”，未开放报名时隐藏报名操作。
- 登录操作进入现有身份核验页，报名操作进入新报名页。
- 报名必填项缺失时显示字段级中文提示；提交成功后展示待审核说明。
- 现有嘉宾登录、个人二维码和五项会议服务路由不受影响。
- 前端 TypeScript 构建通过。

## 验证方式

- 在 `frontend/` 运行 `npm run build`。
- 检查构建产物生成且无 TypeScript 或 Vue 编译错误。

## 风险与注意事项

- 当前工作区已有未提交修改，本任务只在其基础上增量实现，不覆盖或回退现有内容。
- 报名接口会创建真实待审核记录；本次自动验证只执行构建，不自动提交测试报名。
- 当前公开会议接口仅返回报名开关，不返回动态字段配置，因此首版报名表不渲染动态字段。

## 完成记录

- 已新增会议专属活动入口首页，展示会议概要、活动介绍、参会登录、自主报名和会议服务预览。
- 已新增公开自主报名页，支持姓名、手机号、单位、职务、字段级校验、服务端错误和待审核成功状态。
- 已将 `/meetings/:id` 调整为活动入口，并新增 `/meetings/:id/register`；现有登录、嘉宾中心、二维码和服务详情路由保持不变。
- 已补充公开会议报名开关映射、报名 API 适配层、共享类型和移动端视觉样式。
- 已更新嘉宾工作流文档中的活动入口与自主报名规则。
- 已在 `frontend/` 运行 `npm run build`，TypeScript 与 Vite 构建通过；仅保留既有依赖注释和大包体积提示，无编译错误。
- 已运行 `git diff --check`，未发现空白错误。
