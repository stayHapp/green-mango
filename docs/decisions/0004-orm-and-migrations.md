# 0004 ORM 与迁移工具选择

## 状态

已接受。

## 决策

后端采用 SQLAlchemy 2.x 作为 ORM 基础，采用 Alembic 作为数据库迁移工具。

配置管理采用 `pydantic-settings`。本地开发默认使用 SQLite，正式环境使用 PostgreSQL。

## 原因

SQLAlchemy 是 Python 生态中成熟、稳定、表达能力强的 ORM 和数据库工具包。Alembic 与 SQLAlchemy 原生配合，适合管理后续从 SQLite 到 PostgreSQL 的数据库结构演进。

项目后续会包含多张关系表、外键关系、动态报名字段和值表。SQLAlchemy 2.x 的显式模型和迁移工作流更适合长期维护，也便于在复杂查询、事务边界和迁移审查上保持清晰。

`pydantic-settings` 用于统一从环境变量和 `.env` 读取配置，避免在代码中手写分散的 `os.getenv`。

## 备选方案

SQLModel 仍然是可接受备选。它在 Pydantic 和 SQLAlchemy 之间提供更高层封装，适合较轻量的数据模型。但本项目预期会逐步扩展报名字段、审核、统计和权限能力，因此当前优先选择更标准、更底层、更可控的 SQLAlchemy。

## 影响

- 后端模型会放在 `backend/app/models/`。
- ORM 基类放在 `backend/app/db/base.py`。
- Session 和 FastAPI 数据库依赖放在 `backend/app/db/session.py`。
- 迁移配置放在 `backend/alembic.ini` 和 `backend/alembic/`。
- 数据库连接通过 `DATABASE_URL` 配置。
- 数据库结构变化必须同步更新 `docs/architecture/database.md`。
