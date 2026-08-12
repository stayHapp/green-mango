# 执行计划 0077：域名根路径改为会议公开首页

## 任务名称

将前端域名根路径 `/` 从管理员登录页改为指定会议的公开首页，并把「后台配置默认入口会议」保留为后续版本优化方向。

## 背景

当前 `frontend/src/router/index.ts` 将 `/` 固定重定向到 `/login`（管理员登录页），导致域名根路径直接暴露后台登录入口。产品模型是会议级访问：公开会议首页为 `/meetings/:id`，嘉宾端 MVP 不提供跨会议列表。经确认采用方案 A：根路径进入指定会议的公开首页，会议 ID 通过前端构建环境变量配置；方案 C（后台配置默认入口会议）记录为后续版本优化内容，本次不实现。

## 用户确认状态

已确认。用户明确选择方案 A 实施，并保留方案 C 作为后续新版本优化内容之一。

## 执行前必须读取

- `AGENTS.md`
- `docs/architecture/frontend.md`
- `frontend/README.md`
- 当前 active 执行计划

## 目标

- 根路径 `/` 根据 `VITE_PUBLIC_DEFAULT_MEETING_ID` 重定向到对应会议公开首页。
- 未配置该环境变量时，根路径保持回退到管理员登录页，不破坏现有部署。
- 管理员登录入口仍可通过 `/login` 访问，不受影响。
- 方案 C 作为后续优化方向记录在架构文档，本次不实现。

## 不在本次范围内的内容

- 不新增公开会议列表接口或会议门户页（方案 B）。
- 不实现后台「默认入口会议」配置（方案 C）。
- 不修改后端代码、数据库或 API。

## 技术决策与待确认项

- 环境变量命名为 `VITE_PUBLIC_DEFAULT_MEETING_ID`，与既有 `VITE_PUBLIC_APP_URL` 的公开场景命名保持一致。
- 根路径在未配置或配置为空时回退到 `/login`，保证存量部署安全。
- 会议 ID 由部署方在构建前端时配置，正式环境写入 `.env.production`。

## 注释要求

新增、补全、重构或修复代码时，必须遵守 `AGENTS.md` 的全局代码注释强制规范，所有注释和文档说明使用简体中文。

## 涉及文件

新增：

- `docs/exec-plans/active/0077-root-path-meeting-home.md`

修改：

- `frontend/src/router/index.ts`
- `frontend/src/vite-env.d.ts`
- `frontend/.env.example`
- `frontend/README.md`
- `docs/architecture/frontend.md`
- `docs/development/new-server-domain-deployment.md`
- `CHANGELOG.md`

本地验证（不提交）：

- `frontend/.env.local`

## 分步计划

1. 修改根路径重定向逻辑，新增环境变量类型声明与示例配置。
2. 更新前端 README 和架构文档，记录根路径行为与方案 C 后续优化方向。
3. 更新正式部署文档，补充构建时必须配置的新环境变量。
4. 更新 CHANGELOG。
5. 构建前端验证类型与产物，并说明本地与正式验证方式。

## 验收标准

1. `npm run build` 成功，无类型错误。
2. 配置 `VITE_PUBLIC_DEFAULT_MEETING_ID` 时，根路径进入 `/meetings/:id` 公开会议首页。
3. 未配置该变量时，根路径仍回退到 `/login`。
4. 架构文档和部署文档已同步，方案 C 已记录为后续优化方向。
