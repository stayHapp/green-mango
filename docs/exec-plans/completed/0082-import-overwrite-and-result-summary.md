# 执行计划 0082：导入已存在嘉宾覆盖更新与导入结果统计

## 任务名称

Excel 导入时，同会议同名同手机号的启用嘉宾由「报错跳过」改为「覆盖更新」，并在前端展示导入结果统计（新增、覆盖、使用默认手机号数量）。

## 背景

当前导入遇到同会议同名同手机号嘉宾会整行报错，重复导入同一名单时错误行多、体验差。用户希望已存在嘉宾被覆盖更新，并明确展示导入结果。

## 用户确认状态

已确认：已存在嘉宾覆盖；前端展示导入统计。

## 执行前必须读取

- `AGENTS.md`
- `docs/architecture/api.md`
- `backend/app/services/excel_files.py`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`

## 目标

- 导入时同会议同名同手机号的启用嘉宾更新固定字段与动态字段值，保留签到记录。
- 导入响应新增「覆盖数量」和「使用默认手机号数量」，前端导入结果摘要展示新增、覆盖、默认号与错误行。

## 不在本次范围内的内容

- 不修改手机号、姓名身份本身；覆盖仅更新其他字段。
- 不覆盖停用嘉宾（停用记录可重新导入为新增）。
- 不改变单行错误校验（姓名必填等）。

## 技术决策与待确认项

- 覆盖判定：同一会议内 `name + phone` 且启用状态的嘉宾视为已存在。
- 覆盖复用 `update_guest` 与 `save_guest_values`，与后台编辑行为保持一致。

## 注释要求

所有新增、修改代码的注释和 docstring 使用简体中文，遵守 `AGENTS.md` 全局注释规范。

## 涉及文件

新增：

- `docs/exec-plans/active/0082-import-overwrite-and-result-summary.md`

修改：

- `backend/app/schemas/admin_resources.py`
- `backend/app/services/excel_files.py`
- `backend/tests/test_excel_import.py`
- `frontend/src/api/adminExcel.ts`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `docs/architecture/api.md`
- `CHANGELOG.md`

## 分步计划

1. 后端：导入覆盖逻辑与响应统计字段。
2. 前端：导入摘要类型与结果文案。
3. 测试与构建：补充覆盖与统计测试，运行 pytest 与前端构建。
4. 文档与归档：更新 API 文档与 CHANGELOG，归档执行计划。

## 验收标准

1. 后端测试与前端构建通过。
2. 重复导入同名同手机号嘉宾时其他字段被更新，签到记录保留。
3. 导入摘要正确显示新增、覆盖、默认手机号与错误行数量。
