# 架构概览

知会第一版采用前后端分离架构。

```text
浏览器 -> Vue 前端 -> HTTP API -> FastAPI 后端 -> ORM -> 数据库
```

## 前端

前端使用 Vue 3、Vite、TypeScript、Element Plus、Vue Router、Pinia 和 Axios。

前端负责：

- 页面展示
- 表单交互
- 动态报名表渲染
- 基础前端校验
- 调用后端 API

## 后端

后端使用 Python、FastAPI、Pydantic、SQLModel 或 SQLAlchemy、Alembic 和 pytest。

后端负责：

- API 接口
- 权限判断
- 数据校验
- 业务规则
- 数据持久化

## 数据库

本地早期开发可以使用 SQLite，正式环境使用 PostgreSQL。

数据库负责保存：

- 用户和管理员信息
- 会议信息
- 会议设置
- 报名字段配置
- 报名记录
- 动态字段值

