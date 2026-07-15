# 分离登录入口并展示嘉宾二维码

## 背景

当前前端 Mock 原型将管理员、工作人员、嘉宾统一放在同一登录页，且嘉宾端直接展示二维码 token，容易造成入口与身份职责混淆，不利于验证会议入口流程。

## 用户确认状态

用户已明确要求执行本次前端交互优化。

## 执行前必须读取

- `AGENTS.md`
- `docs/product/client-model.md`
- `docs/product/guest-workflow.md`
- `docs/product/admin-workflow.md`
- `docs/product/staff-workflow.md`
- 当前 active 执行计划

## 目标

- 管理员和工作人员共用管理/签到登录入口，嘉宾使用独立会议登录入口。
- 三端已登录状态均可通过顶部导航安全退出并返回相应登录入口。
- 嘉宾端将个人 token 渲染为可供工作人员扫描的二维码图像。

## 不在本次范围内的内容

- 不接入真实鉴权、真实扫码硬件或后端 API。
- 不调整二维码 token 的生成与有效期规则。

## 技术决策与待确认项

- 保留既有 `qrcode` 依赖，使用其 Data URL（数据地址）能力在浏览器内生成二维码。
- 管理员与工作人员入口路径使用 `/login`，嘉宾入口路径使用 `/guest/login`；会议入口 `/meetings/:id` 跳转至嘉宾入口。

## 涉及文件

- `frontend/src/App.vue`
- `frontend/src/router/index.ts`
- `frontend/src/views/HomeView.vue`
- `frontend/src/views/LoginView.vue`
- `frontend/src/views/guest/GuestLoginView.vue`
- `frontend/src/views/guest/GuestMeetingDetailView.vue`
- `frontend/src/stores/session.ts`
- `frontend/src/styles.css`
- `docs/product/client-model.md`
- `docs/product/guest-workflow.md`
- `docs/product/staff-workflow.md`

## 分步计划

1. 调整路由和首页入口，拆分管理/签到与嘉宾登录路径。
2. 在会话状态中补充退出能力，并在全局顶部导航提供当前端对应的退出操作。
3. 在两个嘉宾页面生成并展示二维码图像，保留 token 仅作开发期辅助说明。
4. 更新产品工作流文档并执行前端构建验证。

## 验收标准

- 首页和顶部导航可进入两个清晰区分的登录入口。
- 管理员、工作人员可在同一入口登录，嘉宾无法由该入口进入嘉宾端。
- 嘉宾会议入口及嘉宾端未登录跳转使用嘉宾登录路径。
- 各端登录后均可退出，退出后本地会话被清除。
- 嘉宾个人信息卡展示可扫描的二维码图像。

## 验证方式

- 运行 `npm run build`。
- 人工检查路由跳转、退出逻辑和二维码生成错误提示。

## 风险与注意事项

- 二维码图像仅承载现有 mock token，不代表正式环境的安全凭证方案。

## 完成记录

- 已将管理员和工作人员收敛至 `/login` 管理与签到入口，并以页签区分两类凭证；嘉宾登录入口独立为 `/guest/login`。
- 已将会议入口 `/meetings/:id` 调整为跳转嘉宾专属登录页，并更新首页、未登录页和产品工作流文档中的入口说明。
- 已在全局顶部导航按当前客户端显示退出登录按钮；退出时清除对应 Mock 会话及本地存储并返回相应登录入口。
- 已新增可复用嘉宾二维码组件，使用现有 `qrcode` 依赖将嘉宾 token 渲染为二维码图像，两个嘉宾页面均已接入。
- 已将嘉宾身份调整为姓名右侧的标签样式；会议服务统一收纳至嘉宾信息旁的入口，点击后从页面右侧展开功能面板。
- 已运行 `npm run build`，构建通过；仅出现第三方依赖注释处理提示和产物体积提示，未影响构建结果。
