# 执行计划 0075：会议二维码下载标题断行与时间格式对齐

## 任务名称

会议入口二维码下载图片的标题按括号位置断行，时间显示与会议设置的「上午/下午 / 具体时间」模式保持一致。

## 背景

二维码下载图片已支持标题自动换行，但换行按字符宽度自动截断，例如标题「2026年第二届标准学术能力测试（CSSAT）学术研讨会」会断开在随机位置。用户希望「（CSSAT）学术研讨会」整体放到第二行。另外下载图片中的会议时间目前固定按具体时间显示，与会议设置的时间显示格式（上午/下午或具体时间）不一致。

## 执行前必须读取

- `AGENTS.md`
- `docs/product/guest-experience.md`（时间显示模式语义）

## 目标

- 下载二维码图片的标题优先在括号（中文或英文括号）前断行，括号内容整体移到第二行；仍超宽时继续按字符自动换行。
- 下载图片中的会议时间显示与会议 `timeDisplayMode` 一致：`day_period` 显示「上午 / 下午」，`time` 显示具体时间。
- 嘉宾端时间显示逻辑提取为公共工具并复用，保证各端行为一致。

## 不在本次范围内的内容

- 不改变页面内二维码预览与嘉宾端页面布局。
- 不新增后端字段。

## 涉及文件

新增：

- `frontend/src/utils/meetingTime.ts`
- `docs/exec-plans/active/0075-meeting-qr-download-title-break-and-time-mode.md`

修改：

- `frontend/src/components/GuestMeetingSummary.vue`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `CHANGELOG.md`

## 分步计划

1. 编写本执行计划。
2. 新增 `meetingTime.ts` 公共工具：`formatMeetingRange` 与 `formatMeetingTime`，从 `GuestMeetingSummary.vue` 迁移并保持行为一致。
3. `GuestMeetingSummary.vue` 改为导入公共工具，删除内部重复实现。
4. `AdminMeetingDetailView.vue`：标题绘制前先按括号断行再自动换行；下载图片时间改用 `formatMeetingRange`，跟随会议时间显示模式。
5. 验证：前端 `npm run build` 通过；手工核对下载图片标题两行与时间格式。

## 验收标准

- 标题「2026年第二届标准学术能力测试（CSSAT）学术研讨会」下载时第一行为前半句，第二行为「（CSSAT）学术研讨会」。
- 会议设置「显示到上午/下午」时下载图片时间显示「X月X日 上午 — X月X日 下午」；设置具体时间时显示具体时分。
- 嘉宾端首页时间显示行为与改动前一致。

## 完成记录

实现完成，验证结果：

- 标题断行：新增 `splitQrTitleSegments`，下载绘制前优先在中文 / 英文括号前断行；标题「2026年第二届标准学术能力测试（CSSAT）学术研讨会」验证结果为第一行前半句、第二行「（CSSAT）学术研讨会」，仍超宽时继续自动换行兜底。
- 时间格式：新增公共工具 `frontend/src/utils/meetingTime.ts`（`formatMeetingRange` / `formatMeetingTime`），从 `GuestMeetingSummary.vue` 迁移并复用；下载图片时间跟随会议 `timeDisplayMode`，上下午模式显示「上午 / 下午」，具体时间模式显示时分。
- 兼容：`GuestMeetingSummary.vue` 改为导入公共工具，嘉宾端行为不变；页面内签到时间等既有 `formatDate` 用法未改动。
- 构建：`npm run build` 通过。
