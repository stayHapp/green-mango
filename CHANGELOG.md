# CHANGELOG

## Unreleased

- 修正后端既有代码注释和 docstring 为简体中文，并更新执行计划模板的注释规范。
- 新增第一版核心 SQLAlchemy ORM 模型。
- 新增首个 Alembic 业务迁移，创建 6 张核心表。
- 新增核心模型 metadata 和约束测试。
- 更新数据库和后端架构文档，记录模型与迁移状态。
- 将后端运行环境调整为 Python 3.12。
- 初始化 SQLAlchemy 数据库基础设施。
- 初始化 Alembic 迁移骨架。
- 引入 `pydantic-settings` 管理后端配置。
- 新增数据库基础设施测试。
- 初始化后端 FastAPI 最小骨架。
- 新增 `GET /api/health` 健康检查接口和 pytest 测试。
- 更新项目检查脚本，纳入后端测试。
- 添加 `.gitignore`，忽略环境文件、虚拟环境和缓存文件。
- 初始化项目骨架。
- 建立产品、架构、技术决策和执行计划文档目录。
- 添加占位检查脚本。
