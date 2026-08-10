# 执行计划 0072：签到记录展示同行绑定关系

## 任务名称

工作人员端「签到记录」展示同行人员与所属嘉宾的绑定情况。

## 背景

同行登记功能上线后，同行人员登记成功即自动签到，会进入工作人员端「签到记录」列表。当前列表每条记录只展示姓名、电话、场次时间与签到方式，工作人员无法区分普通嘉宾与同行人员，也看不到同行人员跟随哪位主嘉宾。

经用户确认的呈现方案：

- 主嘉宾记录行显示「已带 N 人」徽标，点击主嘉宾行可展开 / 收起其同行人员子列表（默认收起）。
- 同行人员记录行显示「同行 · 随某嘉宾」标签，副文案带随行备注（如家属、司机）。
- 普通嘉宾记录行保持不变。
- 签到记录接口补齐嘉宾姓名、电话与同行绑定字段，前端不再依赖嘉宾列表反查。

## 执行前必须读取

- `AGENTS.md`
- `docs/architecture/api.md`
- `docs/product/staff-workflow.md`

## 目标

- 后端签到记录接口返回 `guest_name`、`guest_phone`、`is_companion`、`companion_of_id`、`companion_of_name`、`companion_note`。
- 工作人员端「签到记录」页面展示主嘉宾徽标、同行标签与展开子列表。
- 后端测试与前端构建通过，文档同步更新。

## 不在本次范围内的内容

- 「同行登记」页签、导出列、管理端均不调整。
- 不改变签到记录的时间倒序口径，不做分组视图开关。

## 技术决策

- 后端 `CheckInResponse` 扩展绑定字段；`build_check_in_response` 通过 `check_in.guest` 与自关联关系填充。
- `list_check_ins` 增加 `selectinload` 预加载嘉宾与主嘉宾，避免列表接口 N+1 查询。
- 前端「签到记录」只平铺展示非同行记录；同行记录归属到主嘉宾行下的展开区，避免重复展示。
- 主嘉宾未签到但同行已签到时，该同行记录作为独立行保留在列表（带同行标签），保证记录不丢失。
- 展开状态默认收起，点击可展开，用户展开状态在本次会话内保持。

## 涉及文件

新增：

- `docs/exec-plans/active/0072-staff-check-in-records-companion-bindings.md`

修改：

- `backend/app/schemas/check_in.py`
- `backend/app/api/routes/check_ins.py`
- `backend/app/services/check_ins.py`
- `backend/tests/test_staff_checkin.py`
- `backend/tests/test_companions.py`
- `frontend/src/types.ts`
- `frontend/src/api/staffCheckIns.ts`
- `frontend/src/views/staff/StaffCheckInView.vue`
- `frontend/src/styles.css`
- `docs/architecture/api.md`

## 分步计划

1. 编写本执行计划。
2. 后端：扩展 `CheckInResponse` 字段，`build_check_in_response` 填充绑定字段，`list_check_ins` 预加载关系。
3. 后端测试：签到记录列表断言绑定字段；同行登记后签到记录返回绑定信息。
4. 前端：类型与 API 映射新增字段；`StaffCheckInView.vue` 签到记录区实现徽标、标签、展开子列表；`styles.css` 新增样式。
5. 更新 `docs/architecture/api.md`。
6. 整体验证：后端 `pytest` 全绿、前端 `npm run build` 通过。

## 完成记录

实现完成，验证结果：

- 后端：`CheckInResponse` 新增 `guest_name`、`guest_phone`、`is_companion`、`companion_of_id`、`companion_of_name`、`companion_note`；`build_check_in_response` 通过嘉宾自关联填充绑定字段；`list_check_ins` 使用 `selectinload` 预加载嘉宾、主嘉宾与场次，避免列表 N+1 查询。
- 测试：`test_staff_checkin.py` 的签到记录列表用例补充绑定字段断言；`test_companions.py` 新增「签到记录包含同行绑定信息」用例，验证主嘉宾与同行两条记录均返回正确字段；全量 `pytest` 85 通过。
- 前端：`CheckInRecord` 与 `staffCheckIns.ts` 映射补充绑定字段；「签到记录」页主嘉宾行显示「已带 N 人」徽标（带展开箭头），点击可展开 / 收起同行子列表（默认收起）；同行记录行显示「同行 · 随某嘉宾」标签与随行备注；主嘉宾未签到但同行已签到时同行记录作为独立行保留；`npm run build` 通过。
- 文档：`docs/architecture/api.md` 补充签到记录响应绑定字段说明。
