# 0001 技术栈选择

## 状态

已接受。

## 决策

知会第一版采用：

- 前端：Vue 3、Vite、TypeScript、Element Plus、Vue Router、Pinia、Axios
- 后端：Python、FastAPI、SQLModel 或 SQLAlchemy、Pydantic、Alembic、pytest
- 数据库：本地早期开发可用 SQLite，正式环境使用 PostgreSQL

## 原因

Vue 3 和 Vite 适合快速构建管理后台和前台表单体验。TypeScript 有助于在动态字段、API 响应和表单状态中保持类型约束。Element Plus 能快速支持管理后台常见组件。

FastAPI 适合构建清晰的 HTTP API，Pydantic 对请求响应校验友好，pytest 便于建立后端测试基础。

SQLModel 或 SQLAlchemy 都适合表达关系模型。Alembic 用于数据库迁移，便于后续多人协作和环境部署。

## 影响

项目会以清晰的前后端边界推进。第一阶段先建立骨架和文档，再分别初始化前端和后端工程。

