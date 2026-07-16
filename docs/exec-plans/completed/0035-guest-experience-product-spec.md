# 嘉宾端产品规范

## 任务名称

新增嘉宾端产品规范，并统一会议服务相关产品术语。

## 背景

嘉宾端已经实现会议详情、个人信息、签到二维码，以及日程、手册、天气、路线和联系等会议助手入口，但现有文档主要分别描述业务流程、后端配置和单项功能，没有统一定义嘉宾首页的信息层级、跨页面交互、通用状态和会前会中会后体验。需要新增一份可直接作为后续前端实现与验收依据的产品规范。

## 用户确认状态

用户已明确要求在当前仓库中新增该规范，并允许按现有文档体系更新必要导航。

## 执行前必须读取

- `AGENTS.md`
- `README.md`
- `docs/index.md`
- `docs/product/overview.md`
- `docs/product/client-model.md`
- `docs/product/guest-workflow.md`
- `docs/product/meeting-assistant.md`
- `docs/product/check-in-flow.md`
- `docs/product/mvp-scope.md`
- `docs/architecture/overview.md`
- `docs/architecture/frontend.md`
- `docs/architecture/api.md`
- `docs/architecture/database.md`
- 用户提供的 `docs.zip` 和 `backend/app/models.zip`

## 目标

1. 新增 `docs/product/guest-experience.md`，定义嘉宾端完整体验与页面规范。
2. 明确会前、会中、会后的体验目标，以及嘉宾首页、会议服务和签到区域的信息层级。
3. 将面向嘉宾的“会议手册”概念调整为“会议资料”，同时保留现有内部 `manual` 标识兼容关系。
4. 定义会议日程、会议资料、天气、路线和联系会务的内容、交互及异常状态。
5. 明确 MVP 已实现能力、当前产品规范目标和后续扩展边界。
6. 更新必要的文档导航及相关产品文档术语，避免新旧文档互相矛盾。

## 不在本次范围内的内容

- 不修改前端页面、样式或路由。
- 不修改后端模型、数据库迁移、API 或固定功能标识。
- 不新增文件上传、结构化日程、实时签到推送、地图内嵌导航或通知能力。
- 不把后续设想写成 MVP 已实现能力。

## 技术决策与待确认项

- 产品展示名称使用“会议服务”，现有代码和数据中的“会议助手”可继续作为内部模块名称。
- 面向嘉宾的 `manual` 功能展示为“会议资料”；`manual` 仍是内部兼容标识，不在本任务中改名。
- 新规范通过“当前实现约束”“目标体验规范”“后续扩展”区分事实与规划。
- 当前无待用户确认项。

## 注释要求

本任务只修改 Markdown 文档，不新增或修改代码注释。

## 涉及文件

- 新增 `docs/product/guest-experience.md`
- 修改 `docs/product/guest-workflow.md`
- 修改 `docs/product/meeting-assistant.md`
- 修改 `docs/index.md`
- 修改 `README.md`
- 完成后将本计划移入 `docs/exec-plans/completed/`

## 分步计划

1. 核对现有产品、架构、代码与压缩包中的真实实现边界。
2. 编写嘉宾端产品规范，覆盖信息架构、页面顺序、功能规范、状态规范和范围边界。
3. 更新相关文档术语与导航，保留内部标识兼容说明。
4. 检查 Markdown 相对链接、关键词一致性和 Git 差异。

## 验收标准

1. 新文档覆盖用户要求的十二项内容。
2. 新文档明确“会议服务 / 会议资料”产品术语与 `meeting assistant / manual` 内部标识的关系。
3. 文档不要求本次修改数据库、API 或业务代码。
4. README 与文档首页可以导航到新规范。
5. 相关产品文档不再把“会议手册”作为唯一面向嘉宾的产品名称。
6. 相对链接存在且 `git diff --check` 通过。

## 验证方式

- 使用脚本检查新文档中的相对 Markdown 链接目标是否存在。
- 使用 `rg` 检查“会议手册”“会议资料”“会议服务”“manual”等术语的使用是否符合兼容约定。
- 运行 `git diff --check`。
- 人工对照用户要求逐项核验章节覆盖情况。

## 风险与注意事项

- README 的“当前阶段”与代码真实进展存在滞后，本任务不顺带重写整个项目进度，避免扩大范围。
- 产品名称调整不能直接推导出内部标识调整，否则会引入数据库、API 和迁移工作。
- 天气与路线已有真实集成，规范必须以当前架构文档为准，不能沿用早期“仅文本”描述。

## 完成记录

- 新增 `docs/product/guest-experience.md`，覆盖嘉宾用户、典型场景、会前会中会后目标、页面树、首页层级、五项会议服务、通用状态、签到状态和范围边界。
- 面向嘉宾统一使用“会议服务”“会议资料”“天气提醒”“路线导航”和“联系会务”。
- 保留内部 `meeting assistant`、`assistant-features` 和 `manual` 标识，明确本任务不触发数据库、API 或历史数据迁移。
- 更新 `guest-workflow.md`、`meeting-assistant.md`、`docs/index.md` 和 `README.md`，补齐文档关系与导航。
- 明确当前前端仍存在历史文案，本文是下一轮嘉宾端优化的实现依据，不把文档更新描述成页面已完成。
- Markdown 相对链接检查通过，共检查 5 个本次涉及导航或链接的文件。
- `git diff --check` 通过。
