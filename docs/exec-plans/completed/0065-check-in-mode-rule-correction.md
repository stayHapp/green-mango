# 签到场次模式规则修正

## 任务名称

修正签到场次模式与当前有效场次规则。

## 背景

当前后台“单场签到 / 按日期签到 / 自定义场次”主要是前端展示状态，后端仍只按 `check_in_sessions.is_default` 查找默认场次。管理员生成日期场次后，系统不会在第二天自动切换当前签到场次，导致工作人员端和嘉宾端仍可能读取旧默认场次。

## 用户确认状态

用户已确认按新的设计模型继续执行：默认一个签到场次，提供生成日期场次按钮；手动新增场次进入自定义场次；日期场次应由系统按当前日期自动选择当前有效签到场次。

## 执行前必须读取

- `AGENTS.md`
- `docs/product/check-in-flow.md`
- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `backend/app/services/check_in_sessions.py`
- `backend/app/services/check_ins.py`
- `backend/app/services/admin_check_ins.py`
- `backend/app/api/routes/admin_check_ins.py`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`

## 目标

1. 后端持久化会议级签到规则：单场、日期、自定义。
2. 后端提供统一的当前有效签到场次计算逻辑。
3. 工作人员端签到、嘉宾端签到状态、后台默认统计使用同一套当前有效场次逻辑。
4. 后台移除纯前端模式切换按钮，改为“生成日期场次”和“新增自定义场次”驱动规则变化。
5. 日期场次默认按当前日期自动切换；必要时允许管理员手动设置默认场次作为覆盖。

## 不在本次范围内的内容

- 不实现按小时段自动切换上午、下午等复杂场次。
- 不新增数据库迁移，优先复用 `meeting_settings.settings_json`。
- 不实现撤销签到、补签或离线签到。
- 不修改签到导出结构。

## 技术决策与待确认项

- 签到规则保存在 `meeting_settings.settings_json.check_in_mode`。
- 日期场次的手动覆盖保存在 `meeting_settings.settings_json.check_in_manual_default_session_id`。
- 当前有效场次由后端服务统一计算，并同步 `is_default`，保证后台展示、工作人员端和嘉宾端口径一致。
- 自定义场次不自动按日期切换，由管理员手动选择默认场次。

## 注释要求

新增、补全、重构或修复代码时，必须遵守 `AGENTS.md` 的全局代码注释强制规范：

- 所有代码注释和 docstring 必须使用简体中文。
- 保留必要英文技术名词时，首次出现应括号标注中文释义。
- 每个函数/方法必须有中文文档注释，说明功能、入参、返回值和异常/报错场景。
- 关键逻辑、判断分支、循环、复杂计算和重要约束必须添加中文注释说明意图。

## 涉及文件

- `backend/app/services/check_in_sessions.py`
- `backend/app/services/check_ins.py`
- `backend/app/services/admin_check_ins.py`
- `backend/app/api/routes/admin_check_ins.py`
- `backend/app/api/routes/guest_sessions.py`
- `backend/app/schemas/admin_check_in.py`
- `backend/tests/test_staff_checkin.py`
- `backend/tests/test_admin_meetings.py`
- `frontend/src/api/adminCheckIns.ts`
- `frontend/src/types.ts`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `frontend/src/styles.css`
- `docs/product/check-in-flow.md`
- `docs/architecture/database.md`
- `docs/architecture/api.md`

## 分步计划

1. 增加签到规则读写与当前有效场次服务。
2. 调整工作人员、嘉宾和管理员统计接口读取当前有效场次。
3. 增加管理员签到规则 API。
4. 调整后台签到管理界面，将模式切换改为规则驱动操作。
5. 补充日期自动切换测试和文档。
6. 运行后端测试、前端构建与差异检查。

## 验收标准

- 生成日期场次后，后端记录会议处于日期签到规则。
- 日期规则下，无手动覆盖时，当前日期落入某个日期场次即自动选中该场次。
- 工作人员签到写入当前有效场次。
- 嘉宾端签到状态查询读取当前有效场次。
- 后台默认统计默认展示当前有效场次。
- 手动新增场次后，会议进入自定义场次规则。

## 验证方式

- 运行相关后端测试。
- 运行前端构建。
- 运行 `git diff --check`。
- 本地浏览器验收受既有安全策略限制，不尝试绕过。

## 风险与注意事项

- `settings_json` 是 JSON 字段，更新时必须整体复制后重新赋值，避免 ORM 不追踪原地修改。
- SQLite 会丢失部分时区信息，签到场次时间按会议本地时间处理。
- 日期自动切换必须以后端时间为准，不能依赖前端浏览器时间。

## 完成记录

1. 已在后端增加会议级签到规则读写能力，规则保存在 `meeting_settings.settings_json.check_in_mode`。
2. 已增加当前有效签到场次统一解析逻辑，日期规则下无手动覆盖时按服务端当前日期匹配日期场次。
3. 工作人员扫码/手工签到、工作人员签到记录、嘉宾二维码签到状态、管理员默认统计均已改为读取当前有效场次。
4. 已新增管理员签到规则接口：读取和更新规则、手动覆盖场次、当前有效场次。
5. 后台签到管理已移除纯前端三模式切换，改为展示当前规则，并通过“生成日期场次”“新增自定义场次”“恢复按日期自动切换”驱动规则变化。
6. 已补充产品、数据库和 API 文档，明确单场、日期和自定义场次的数量关系与默认场次规则。
7. 已补充测试覆盖日期规则自动解析、工作人员签到写入当天场次、管理员规则接口。
8. 验证结果：`./.venv/bin/pytest -q` 通过 68 项；`npm run build` 通过；`git diff --check` 通过。
9. 浏览器本地验收未执行：此前浏览器安全策略已拒绝访问 `http://127.0.0.1:5173`，不能重复尝试或绕过。
