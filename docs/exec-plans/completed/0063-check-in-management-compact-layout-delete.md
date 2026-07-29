# 0063 签到管理紧凑布局与删除场次

## 任务名称

按确认效果图优化签到管理布局，并支持删除签到场次。

## 背景

用户确认新版紧凑布局效果图，并补充要求：

1. 删除“按会议日期自动生成场次”说明块。
2. 去掉底部“工作人员端显示：”区域。
3. 场次列表支持删除操作。
4. 场次列表操作列去掉“设为默认”，默认场次只通过左侧圆点设置。
5. 尽量让核心内容在一个屏幕内呈现。

## 目标

1. 后台签到管理首屏保留签到模式、当前默认场次摘要、签到场次列表、签到记录概览和场次对比。
2. 删除场次列表操作列中的“设为默认”按钮，仅保留“编辑”“删除”。
3. 点击左侧圆点切换默认场次。
4. 支持管理员删除签到场次，并提供二次确认。
5. 删除默认场次时由后端保证仍有一个可用默认场次。

## 不在本次范围内

1. 不新增签到模式持久化字段。
2. 不引入新的主要前端组件库或后端基础设施。
3. 不做拖拽排序。

## 涉及文件

- `backend/app/api/routes/admin_check_ins.py`
- `backend/app/services/check_in_sessions.py`
- `backend/tests/test_admin_meetings.py`
- `frontend/src/api/adminCheckIns.ts`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `frontend/src/styles.css`
- `docs/architecture/api.md`
- `docs/exec-plans/completed/0063-check-in-management-compact-layout-delete.md`

## 验证方式

1. `.venv/bin/python -m pytest`
2. `npm run build`
3. `git diff --check`
4. 浏览器访问 `/admin/meetings/1?tab=checkins` 验收布局、圆点切换、删除入口和控制台日志。

## 完成记录

1. 已删除签到管理页中的“按会议日期自动生成场次”说明块。
2. 已删除底部“工作人员端显示：”区域。
3. 已将场次列表、签到记录概览和场次对比调整为紧凑双栏布局，减少首屏滚动。
4. 已移除场次列表操作列中的“设为默认”，默认场次仅通过左侧圆点切换。
5. 已新增管理员删除签到场次接口 `DELETE /api/admin/meetings/{meeting_id}/check-in-sessions/{session_id}`。
6. 已新增前端删除操作和二次确认；删除默认场次时后端会把剩余第一条场次设为默认。
7. 已更新 API 文档。
8. 已通过 `.venv/bin/python -m pytest`、`npm run build` 和 `git diff --check`。
9. 浏览器验收未执行成功：当前浏览器安全策略拒绝访问 `http://127.0.0.1:5173`，且明确禁止使用替代浏览器路径绕过。
