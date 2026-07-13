# 梳理三端客户端与会议签到交互

## 任务名称

梳理管理员端、嘉宾端、工作人员端的功能交互，并同步更新相关产品与架构文档。

## 背景

项目初始文档以会议报名系统为主，角色定义为访问者、报名用户、管理员。用户已明确当前产品应转向三类客户端：管理员端、嘉宾端、工作人员端。系统核心闭环也从“动态报名表提交”调整为“管理员提前录入嘉宾、嘉宾登录查看会议信息和二维码、工作人员扫码签到、管理员查看签到情况”。

## 用户确认状态

用户已明确要求生成建议文档，并进行相关文档更新。

## 执行前必须读取

已读取并遵守：

- `AGENTS.md`
- `docs/exec-plans/template.md`
- `docs/product/overview.md`
- `docs/product/mvp-scope.md`
- `docs/product/user-roles.md`
- `docs/product/feature-map.md`
- `docs/architecture/database.md`
- `docs/architecture/api.md`

## 目标

- 新增三端客户端模型文档。
- 新增管理员端、嘉宾端、工作人员端工作流文档。
- 新增签到流程文档。
- 将 MVP 范围从“报名字段配置优先”调整为“嘉宾信息字段配置与签到优先”。
- 更新用户角色、功能地图、产品概览、数据库设计和 API 设计文档。
- 明确当前是产品交互梳理，不继续后端构建。

## 不在本次范围内的内容

- 不修改后端代码。
- 不修改数据库迁移。
- 不初始化前端。
- 不实现 API。
- 不提交新的 Git commit，除非用户后续明确要求。

## 技术决策与待确认项

已确认：

- 嘉宾由管理员提前录入。
- 可以保留嘉宾报名接口作为补充入口。
- 嘉宾需要登录，登录字段由管理员按已录入嘉宾信息指定。
- 工作人员需要登录，账户由管理员创建。
- 一个会议可以有多个管理员。
- 签到只签一次。
- 嘉宾二维码按会议结束日期过期。
- MVP 转向嘉宾信息字段配置。

待后续确认：

- 嘉宾登录是否需要短信验证码，或只做字段匹配登录。
- 工作人员登录方式。
- 嘉宾二维码是否需要加签、防伪和刷新机制。
- 多管理员之间是否需要细分权限。

## 注释要求

本任务只修改 Markdown 文档，不涉及代码注释。

## 涉及文件

预计新增：

- `docs/product/client-model.md`
- `docs/product/admin-workflow.md`
- `docs/product/guest-workflow.md`
- `docs/product/staff-workflow.md`
- `docs/product/check-in-flow.md`

预计修改：

- `docs/product/overview.md`
- `docs/product/mvp-scope.md`
- `docs/product/user-roles.md`
- `docs/product/feature-map.md`
- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `docs/index.md`
- `README.md`
- `CHANGELOG.md`

## 分步计划

1. 创建三端客户端模型文档。
2. 创建管理员端、嘉宾端、工作人员端工作流文档。
3. 创建签到流程文档。
4. 更新产品概览、MVP 范围、用户角色和功能地图。
5. 更新数据库和 API 概念设计，标记现有模型需要重评估。
6. 更新文档首页、README 和 CHANGELOG。
7. 检查文档文件列表和 Git 状态。
8. 填写完成记录并归档执行计划。

## 验收标准

- 产品文档明确三端客户端：管理员端、嘉宾端、工作人员端。
- MVP 范围明确转向嘉宾信息字段配置和单次签到。
- 签到流程明确二维码过期边界为会议结束日期。
- 数据库/API 文档明确当前已实现模型与新产品方向存在差异，需要后续重评估。
- 未修改后端代码和迁移。

## 验证方式

```bash
rg --files docs/product docs/architecture docs/exec-plans | sort
git status --short
```

## 风险与注意事项

- 当前后端数据模型仍基于早期报名系统思路，本次只通过文档标记差异，不直接重写模型。
- 后续继续开发前，应先基于新三端模型重新制定数据模型和 API 执行计划。

## 完成记录

完成日期：2026-07-07

实际完成内容：

- 新增 `docs/product/client-model.md`，明确管理员端、嘉宾端、工作人员端三类客户端。
- 新增 `docs/product/admin-workflow.md`，梳理管理员端会议、嘉宾、工作人员和签到管理流程。
- 新增 `docs/product/guest-workflow.md`，梳理嘉宾登录、会议信息查看、个人信息展示和二维码展示流程。
- 新增 `docs/product/staff-workflow.md`，梳理工作人员登录和扫码签到流程。
- 新增 `docs/product/check-in-flow.md`，明确二维码有效期、单次签到、签到记录和异常场景。
- 更新 `docs/product/overview.md`、`mvp-scope.md`、`user-roles.md`、`feature-map.md`，将产品方向调整为三端客户端和扫码签到闭环。
- 更新 `docs/architecture/api.md`，按管理员端、嘉宾端、工作人员端重新梳理概念 API。
- 更新 `docs/architecture/database.md`，标记当前早期数据模型与新方向存在差异，后续需要重新评估。
- 更新 `docs/index.md` 和 `README.md`，补充新文档导航。
- 更新 `CHANGELOG.md`。
- 未修改后端代码、数据库迁移和前端代码。

验证结果：

```bash
rg --files docs/product docs/architecture docs/exec-plans | sort
rg -n "管理员端|嘉宾端|工作人员端|签到|嘉宾信息字段|二维码" docs/product docs/architecture/api.md docs/architecture/database.md README.md
git status --short
```

结果：新增和更新文档均已出现，关键词覆盖三端客户端和签到流程；Git 状态显示本次只有文档相关变更。

后续建议：

- 在继续开发前，先基于三端模型制定新的数据库调整执行计划。
- 重点重评估 `registration_fields`、`registrations`、`registration_values` 是否应迁移为 `guest_fields`、`guests`、`guest_values` 和 `check_ins`。
