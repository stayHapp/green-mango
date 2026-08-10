# 知会

> 知会｜教育会议与研讨活动管理平台

知会是一个面向教育领域的会议、研讨、培训、论坛和专家讲座管理平台。它不是单纯的会议报名表工具，而是帮助活动组织者完成会议创建、嘉宾字段配置、嘉宾录入与导入、会议服务维护和现场签到管理，并为后续的结构化日程、文件资料和数据分析等能力留下扩展空间。

## 项目定位

知会主要服务于：

- 教育专家
- 学校领导
- 教研组织者
- 教育培训活动负责人
- 学术会议组织者

第一版聚焦最小可用闭环：管理员创建会议并录入嘉宾，嘉宾登录后查看会议信息和个人二维码，工作人员扫码签到，管理员查看签到情况。

## 当前阶段

当前处于 MVP 主体功能完成后的联调验收与试运行整理阶段。三端核心闭环已经具备可运行实现，当前重点是按真实会议数据做手工验收、部署前配置检查、文档归档和体验打磨。

已完成：

- 项目基础目录、产品文档、架构文档、执行计划和部署说明。
- 后端 FastAPI、SQLAlchemy、Alembic、认证会话、权限校验和业务测试体系。
- 前端 Vue 3、Vite、TypeScript、Element Plus、Vue Router、Pinia 和 Axios 应用骨架及三端页面。
- 管理员端会议管理、嘉宾字段配置、嘉宾录入、Excel 导入导出、工作人员管理和签到管理。
- 嘉宾端会议入口、姓名手机号身份核验、会议信息、个人资料、签到二维码和会议服务查看。
- 工作人员端登录、会议工作台、扫码签到、手工签到、当前场次提示、连续扫码和同行人员登记。
- 会议服务五项固定能力：日程、资料、天气、路线和联系会务，并支持发布状态与公开/登录访问级别。
- 多签到场次、按场次统计、相邻场次差异、签到明细和嘉宾状态导出。
- PostgreSQL 本地联调和部署文档，SQLite 作为临时回退数据库。
- 项目检查脚本 `scripts/check_all.sh`，当前覆盖后端测试和前端生产构建。

后续重点：

- 使用真实会议数据完成管理员端、嘉宾端和工作人员端手工验收。
- 核对生产环境变量、PostgreSQL、Nginx、服务进程和附件存储路径。
- 持续补齐 README、CHANGELOG 和执行计划归档，确保文档与实现一致。
- 针对前端构建体积较大的提示评估路由级拆包优化。

## MVP 范围

第一版要实现：

- 会议管理：创建会议、查看会议列表、查看会议详情、修改会议基本信息
- 嘉宾信息字段配置：每个会议可配置自己的嘉宾信息字段
- 嘉宾管理：管理员提前录入或通过 Excel 导入嘉宾，并可按会议开关启用嘉宾补充报名审核
- 会议服务：管理员维护日程、资料、天气、路线和联系会务，嘉宾查看已发布内容
- 嘉宾端：嘉宾核验会议级身份后查看当前会议、个人信息、签到二维码和签到状态
- 工作人员端：工作人员登录后通过扫码或手工方式完成签到
- 签到管理：支持单场、按日期和自定义签到场次，同一嘉宾在同一场次内只签到一次，管理员按场次查看和导出签到情况

第一版暂不做：微信登录、支付、短信验证码、邮件通知、复杂权限、复杂统计、通用文件库、资料在线预览、资料版本管理、多租户、高级页面装修、补签、撤销签到和离线签到。

更完整的范围说明见 [MVP 范围](docs/product/mvp-scope.md)。

## 技术栈

前端当前：

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

数据库当前：

- 本地联调和正式环境使用 PostgreSQL
- SQLite 可作为本地临时回退数据库

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
新服务器和新域名部署见[新服务器与新域名部署文档](docs/development/new-server-domain-deployment.md)。当前无 Git 服务器同步并使用 PostgreSQL 部署，见[无 Git 服务器同步部署文档](docs/development/server-sync-postgresql.md)。旧测试环境部署见[测试环境部署文档](docs/development/test-deployment.md)；使用 Docker 部署到腾讯云 OpenCloudOS 见[腾讯云 Docker 部署文档](docs/development/tencent-cloud-deployment.md)。

### 运行检查

在仓库根目录运行：

```bash
./scripts/check_all.sh
```

当前检查内容包括后端 pytest 测试和前端生产构建。

## 文档导航

建议从以下顺序阅读：

1. [AGENTS.md](AGENTS.md)：AI 开发地图和协作规则
2. [docs/index.md](docs/index.md)：文档目录说明
3. [产品概览](docs/product/overview.md)：项目背景、目标用户和产品边界
4. [客户端模型](docs/product/client-model.md)：管理员端、嘉宾端、工作人员端
5. [管理员端工作流](docs/product/admin-workflow.md)：会议、嘉宾、工作人员和签到管理
6. [嘉宾端工作流](docs/product/guest-workflow.md)：嘉宾登录、信息查看和二维码展示
7. [嘉宾端产品规范](docs/product/guest-experience.md)：嘉宾首页、会议服务、状态和交互规范
8. [会议服务](docs/product/meeting-assistant.md)：固定五项服务的发布与实现边界
9. [工作人员端工作流](docs/product/staff-workflow.md)：扫码与手工签到
10. [签到流程](docs/product/check-in-flow.md)：二维码、单次签到和异常处理
11. [MVP 范围](docs/product/mvp-scope.md)：第一版做什么和暂不做什么
12. [架构概览](docs/architecture/overview.md)：整体技术架构
13. [后端规划](docs/architecture/backend.md)：后端分层和当前骨架
14. [数据库设计](docs/architecture/database.md)：概念性数据库设计
15. [API 设计](docs/architecture/api.md)：概念性 API 设计和已实现接口
16. [技术决策](docs/decisions/)：关键技术选择及原因

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

当前合理的下一步是做部署前验收整理。推荐按以下顺序推进：

1. 按 `docs/development/colleague-test-checklist.md` 和三端测试清单走一轮真实会议数据验收。
2. 核对部署环境的 `DATABASE_URL`、会话密钥、天气/地图配置、附件目录、Nginx 和 systemd/Docker 配置。
3. 整理最近完成的执行计划、README 和 CHANGELOG，确保入口文档不落后于实现。
4. 评估前端按路由拆包，降低生产构建的主包体积警告。

如果只做一个最小收尾任务，优先完成真实数据三端验收并记录问题清单。
