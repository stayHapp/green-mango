# 文档首页

本目录保存「知会」项目的重要设计、范围、架构和执行计划。项目长期借助 AI 辅助开发，因此关键上下文必须沉淀到文档中。

## 目录说明

- `product/`：产品背景、客户端模型、MVP 范围、用户角色、功能地图、三端工作流和嘉宾端体验规范。
- `architecture/`：整体架构、前端规划、后端规划、数据库设计、API 设计和安全原则。
- `decisions/`：技术和工程决策记录，说明为什么这样选择。
- `exec-plans/`：复杂任务的执行计划。进行中的计划放在 `active/`，完成后移到 `completed/`。
- `development/`：本地启动、联调和开发环境操作说明。
## 推荐阅读顺序

开发者或 AI 开始任务前，建议先读：

1. `../AGENTS.md`
2. `product/overview.md`
3. `product/client-model.md`
4. `product/admin-workflow.md`
5. `product/guest-workflow.md`
6. `product/guest-experience.md`
7. `product/meeting-assistant.md`
8. `product/staff-workflow.md`
9. `product/check-in-flow.md`
10. `product/mvp-scope.md`
11. `architecture/overview.md`
12. 与任务相关的具体架构文档
13. `development/local-startup.md`：手动启动前后端和手机访问
14. `development/test-deployment.md`：测试环境部署（Nginx + systemd）
15. `development/tencent-cloud-deployment.md`：腾讯云 OpenCloudOS + Docker 部署

如果任务涉及数据库结构，请同步阅读并更新 `architecture/database.md`。

如果任务涉及 API 行为，请同步阅读并更新 `architecture/api.md`。
