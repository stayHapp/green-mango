# 知会

> 知会｜教育会议与研讨活动管理平台

知会是一个面向教育领域的会议、研讨、培训、论坛和专家讲座管理平台。它不是单纯的会议报名表工具，而是希望帮助活动组织者更有秩序地完成会议创建、报名字段配置、报名提交和后台报名管理，并为后续的嘉宾、日程、资料、审核和数据导出等能力留下扩展空间。

## 项目定位

知会主要服务于：

- 教育专家
- 学校领导
- 教研组织者
- 教育培训活动负责人
- 学术会议组织者

第一版聚焦最小可用闭环：管理员创建会议并录入嘉宾，嘉宾登录后查看会议信息和个人二维码，工作人员扫码签到，管理员查看签到情况。

## 当前阶段

当前处于 MVP 前期工程搭建阶段。

已完成：

- 项目基础目录和文档体系初始化
- 后端 FastAPI 最小骨架
- 后端健康检查接口 `GET /api/health`
- 后端 SQLAlchemy 数据库基础设施
- 后端 Alembic 迁移骨架
- 后端核心 SQLAlchemy ORM 模型
- 首个 Alembic 业务迁移
- 后端 pytest 最小测试
- 项目检查脚本 `scripts/check_all.sh`

暂未完成：

- 前端 Vue 项目初始化
- 会议管理业务接口
- 报名字段配置业务接口
- 前台报名页面
- 管理员登录和权限系统

## MVP 范围

第一版要实现：

- 会议管理：创建会议、查看会议列表、查看会议详情、修改会议基本信息
- 嘉宾信息字段配置：每个会议可配置自己的嘉宾信息字段
- 嘉宾管理：管理员提前录入嘉宾，可保留嘉宾报名接口作为补充入口
- 嘉宾端：嘉宾登录后查看会议信息、个人信息和签到二维码
- 工作人员端：工作人员登录后扫码完成签到
- 签到管理：一个嘉宾一个会议只签到一次，管理员查看签到情况

第一版暂不做：微信登录、支付、短信验证码、邮件通知、复杂权限、复杂统计、文件上传、Excel 导入导出、多租户、高级页面装修、多次签到、补签和离线签到。

更完整的范围说明见 [MVP 范围](docs/product/mvp-scope.md)。

## 技术栈

前端计划：

- Vue 3
- Vite
- TypeScript
- Element Plus
- Vue Router
- Pinia
- Axios

后端当前：

- Python 3.12
- FastAPI
- Pydantic
- pydantic-settings
- SQLAlchemy 2.x
- Alembic
- pytest

数据库规划：

- 本地早期开发可使用 SQLite
- 正式环境使用 PostgreSQL

## 项目结构

```text
green-mango/
  AGENTS.md
  README.md
  CHANGELOG.md

  docs/
    product/
    architecture/
    decisions/
    exec-plans/

  backend/
    app/
    tests/
    pyproject.toml
    README.md

  frontend/
    README.md

  scripts/
    check_all.sh
```

## 快速开始

### 后端依赖安装

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"
```

### 运行后端服务

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

健康检查接口：

```text
GET /api/health
```

### 启动前端开发服务

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

启动成功后，按终端输出的本地地址在浏览器中访问前端页面。首次运行或依赖变更后执行 `npm install`。

需要使用两个终端分别保持前后端运行。电脑和手机访问、环境变量、停止服务及故障排查详见[本地手动启动](docs/development/local-startup.md)。

### 运行检查

在仓库根目录运行：

```bash
./scripts/check_all.sh
```

当前检查内容包括后端 pytest 测试。前端初始化后，会逐步加入前端构建、类型检查和格式检查。

## 文档导航

建议从以下顺序阅读：

1. [AGENTS.md](AGENTS.md)：AI 开发地图和协作规则
2. [docs/index.md](docs/index.md)：文档目录说明
3. [产品概览](docs/product/overview.md)：项目背景、目标用户和产品边界
4. [客户端模型](docs/product/client-model.md)：管理员端、嘉宾端、工作人员端
5. [管理员端工作流](docs/product/admin-workflow.md)：会议、嘉宾、工作人员和签到管理
6. [嘉宾端工作流](docs/product/guest-workflow.md)：嘉宾登录、信息查看和二维码展示
7. [工作人员端工作流](docs/product/staff-workflow.md)：扫码签到
8. [签到流程](docs/product/check-in-flow.md)：二维码、单次签到和异常处理
9. [MVP 范围](docs/product/mvp-scope.md)：第一版做什么和暂不做什么
5. [架构概览](docs/architecture/overview.md)：整体技术架构
6. [后端规划](docs/architecture/backend.md)：后端分层和当前骨架
7. [数据库设计](docs/architecture/database.md)：概念性数据库设计
8. [API 设计](docs/architecture/api.md)：概念性 API 设计和已实现接口
9. [技术决策](docs/decisions/)：关键技术选择及原因

## AI 协作规则

本项目长期借助 AI 辅助开发，因此采用 Harness Engineering 思路：

- 仓库文件是项目真实上下文来源。
- 重要设计必须写入 `docs/`。
- 复杂任务必须先写执行计划，放入 `docs/exec-plans/active/`。
- 完成后的执行计划移入 `docs/exec-plans/completed/`。
- 每次只完成一个明确的小任务。
- 数据库结构变化必须同步更新 `docs/architecture/database.md`。
- API 变化必须同步更新 `docs/architecture/api.md`。
- 修改完成后必须说明验证方式。

## 安全原则

- 密码不得明文存储。
- 后台接口必须由后端做权限判断。
- 用户输入必须在后端校验。
- 敏感配置放入环境变量或安全配置系统。
- `.env` 不提交到版本库。

## 下一步建议

当前合理的下一步是创建并执行第二个小任务。推荐二选一：

1. 初始化数据库连接与 Alembic 骨架。
2. 初始化前端 Vue 3 最小项目骨架。

如果优先推进后端闭环，建议先做数据库连接和迁移骨架；如果希望尽早看到页面，则先做前端骨架。
