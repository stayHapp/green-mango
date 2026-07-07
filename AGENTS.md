# AGENTS.md

本仓库是「知会｜教育会议与研讨活动管理平台」的项目真实上下文来源。AI 辅助开发时，应优先阅读仓库文件和 `docs/`，不要只依赖聊天记录。

## 项目定位

知会面向教育领域会议、研讨、培训、论坛、专家讲座等活动，帮助组织者完成会议创建、报名字段配置、前台报名和后台报名管理。

第一版是最小可用版本，不追求完整大系统。

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Element Plus、Vue Router、Pinia、Axios
- 后端：Python、FastAPI、SQLModel 或 SQLAlchemy、Pydantic、Alembic、pytest
- 数据库：本地早期开发可用 SQLite，正式环境使用 PostgreSQL

## 关键文档

- 文档首页：`docs/index.md`
- 产品概览：`docs/product/overview.md`
- MVP 范围：`docs/product/mvp-scope.md`
- 功能地图：`docs/product/feature-map.md`
- 架构概览：`docs/architecture/overview.md`
- 数据库设计：`docs/architecture/database.md`
- API 设计：`docs/architecture/api.md`
- 技术决策：`docs/decisions/`
- 执行计划模板：`docs/exec-plans/template.md`

## 开发规则

1. 重要设计必须写入 `docs/`。
2. 复杂任务先写执行计划，放入 `docs/exec-plans/active/`。
3. 每次只完成一个明确的小任务。
4. 数据库结构变化必须同步更新 `docs/architecture/database.md`。
5. API 变化必须同步更新 `docs/architecture/api.md`。
6. 修改完成后必须说明验证方式。
7. 不要一次性生成过多业务代码。
8. 不提交 `.env`、密钥、生产凭据或本地私有配置。
9. 未经确认，不引入新的主要框架或基础设施。

## 全局代码注释强制规范（必须严格遵守）
1. 所有代码注释统一使用简体中文，禁止英文注释；保留英文技术名词，首次出现括号标注中文释义。
2. 每一个函数/方法必须添加完整中文文档注释（JSDoc / Docstring风格），包含：
   - 函数整体功能详细说明
   - 入参：每个参数含义、取值范围、是否必填
   - 返回值：返回数据结构、业务含义
   - 异常/报错场景（如有）
   - 使用示例（复杂函数必须附带）
3. 代码内部关键逻辑、判断分支、循环、复杂计算块添加单行中文注释说明逻辑意图。
4. 生成代码、补全代码、重构代码、修复Bug时，同步补齐缺失中文注释，不允许无注释函数。
5. 所有AI对话、代码输出、代码解释全部使用简体中文。