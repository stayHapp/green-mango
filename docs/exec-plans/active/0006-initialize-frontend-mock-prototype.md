# 初始化前端三端 Mock 原型

## 任务名称

初始化 Vue 3 前端项目，并使用 JSON mock 数据实现三端页面交互校验。

## 背景

当前项目已明确转向管理员端、嘉宾端、工作人员端三端客户端。后端业务开发暂停，下一步需要先通过前端页面和 JSON mock 数据校验交互流程，避免过早绑定后端 API 和数据库模型。

## 用户确认状态

用户已下达“开始执行”。

## 执行前必须读取

已读取并遵守：

- `AGENTS.md`
- `docs/exec-plans/template.md`
- `docs/architecture/frontend.md`
- 当前 active 执行计划

## 目标

- 初始化 Vue 3 + Vite + TypeScript 前端结构。
- 接入 Element Plus、Vue Router、Pinia、Axios。
- 使用集中 JSON mock 数据描述会议、管理员、嘉宾、工作人员和签到记录。
- 实现三端基础页面：管理员端、嘉宾端、工作人员端。
- 页面通过 `mockApi` 读取 JSON 数据，不接真实后端业务 API。
- 工作人员端提供模拟扫码签到流程，用于交互校验。
- 更新前端文档、前端架构文档、README、CHANGELOG 和检查脚本。

## 不在本次范围内的内容

- 不实现真实后端 API 对接。
- 不修改后端代码和数据库迁移。
- 不实现真实扫码摄像头能力。
- 不实现真实登录鉴权。
- 不实现复杂视觉设计和移动端深度适配。
- 不提交 Git commit，除非用户后续明确要求。

## 技术决策与待确认项

已确认：

- 前端采用 Vue 3、Vite、TypeScript、Element Plus、Vue Router、Pinia、Axios。
- 当前阶段使用 JSON mock 数据进行页面交互校验。
- Mock 数据第一阶段集中放在一个 `data.json` 中。

待后续确认：

- 真实 API 地址和鉴权方案。
- 嘉宾二维码 token 生成规则。
- 工作人员扫码是否接入真实摄像头库。

## 注释要求

新增代码必须遵守 `AGENTS.md` 的全局代码注释强制规范：

- 所有代码注释和函数文档注释必须使用简体中文。
- 关键函数必须说明功能、入参、返回值和异常场景。
- 不写无信息量注释。

## 涉及文件

预计新增或修改：

- `frontend/package.json`
- `frontend/index.html`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `frontend/src/**`
- `frontend/src/mock/data.json`
- `frontend/src/mock/mockApi.ts`
- `frontend/README.md`
- `docs/architecture/frontend.md`
- `README.md`
- `CHANGELOG.md`
- `scripts/check_all.sh`

## 分步计划

1. 检查 Node.js 和 npm 环境。
2. 创建前端 Vite 项目文件。
3. 创建集中 JSON mock 数据。
4. 创建 TypeScript 类型和 `mockApi`。
5. 创建三端路由、Pinia 会话状态和基础布局。
6. 创建管理员端页面：会议列表、会议详情、嘉宾列表、工作人员、签到情况。
7. 创建嘉宾端页面：登录、我的会议、会议详情、个人信息、二维码展示。
8. 创建工作人员端页面：登录、负责会议、模拟扫码签到、签到结果。
9. 更新文档和检查脚本。
10. 安装依赖，运行构建和检查脚本。
11. 启动开发服务器，提供本地访问地址。
12. 填写完成记录并归档执行计划。

## 验收标准

- 前端项目可安装依赖并构建通过。
- `npm run build` 通过。
- `./scripts/check_all.sh` 通过。
- 管理员端可查看 mock 会议、嘉宾和签到情况。
- 嘉宾端可 mock 登录并查看个人二维码。
- 工作人员端可 mock 登录并模拟扫码签到。
- 页面使用 JSON mock 数据，不依赖真实后端业务 API。
- 未修改后端代码和数据库迁移。

## 验证方式

```bash
cd frontend
npm install
npm run build

cd ..
./scripts/check_all.sh
```

开发服务器：

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

## 风险与注意事项

- 安装前端依赖需要网络访问。
- 当前仓库路径不在工具默认 writable root 内，写入需要提升权限。
- 前端页面用于交互校验，不代表最终 UI 和真实 API 已定稿。
- 由于当前产品交互仍在收敛，组件抽象保持克制。

## 完成记录

待任务完成后填写。
