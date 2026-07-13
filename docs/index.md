# 文档首页

本目录保存「知会」项目的重要设计、范围、架构和执行计划。项目长期借助 AI 辅助开发，因此关键上下文必须沉淀到文档中。

## 目录说明

- `product/`：产品背景、客户端模型、MVP 范围、用户角色、功能地图和三端工作流。
- `architecture/`：整体架构、前端规划、后端规划、数据库设计、API 设计和安全原则。
- `decisions/`：技术和工程决策记录，说明为什么这样选择。
- `exec-plans/`：复杂任务的执行计划。进行中的计划放在 `active/`，完成后移到 `completed/`。

## 推荐阅读顺序

开发者或 AI 开始任务前，建议先读：

1. `../AGENTS.md`
2. `product/overview.md`
3. `product/client-model.md`
4. `product/admin-workflow.md`
5. `product/guest-workflow.md`
6. `product/staff-workflow.md`
7. `product/check-in-flow.md`
8. `product/mvp-scope.md`
9. `architecture/overview.md`
10. 与任务相关的具体架构文档

如果任务涉及数据库结构，请同步阅读并更新 `architecture/database.md`。

如果任务涉及 API 行为，请同步阅读并更新 `architecture/api.md`。
