# 执行计划 0080：无手机号嘉宾使用默认手机号

## 任务名称

支持导入无手机号嘉宾时自动填充默认手机号，导出显示「未提供」，并在嘉宾登录页提供「默认填充」按钮。

## 背景

部分嘉宾不提供手机号，但系统要求手机号非空且登录必须按「姓名 + 手机号」核验。经确认，导入时手机号留空自动使用默认手机号 `13900010001`，导出 Excel 中默认号显示为「未提供」，嘉宾登录页增加一键填充默认手机号的按钮。

## 用户确认状态

已确认：默认手机号 `13900010001`；仅支持导入留空；导出显示「未提供」；登录页增加「默认填充」按钮。

> 后续变更：登录页「默认填充」按钮因安全评估已移除（见执行计划 0081），默认号码改为由会务告知嘉宾；导入默认号与导出「未提供」逻辑保留。

## 执行前必须读取

- `AGENTS.md`
- `docs/architecture/database.md`
- `docs/architecture/frontend.md`
- `backend/app/services/excel_files.py`
- `frontend/src/views/guest/GuestLoginView.vue`

## 目标

- Excel 导入时手机号留空不再报错，自动填充默认手机号；姓名仍必填。
- 导入模板填写说明同步更新。
- 嘉宾状态导出与签到明细导出中，默认手机号显示为「未提供」。
- 嘉宾登录页手机号输入框提供「默认填充」按钮，点击填入默认手机号。
- 默认手机号可配置（后端设置项），前后端默认值保持一致。

## 不在本次范围内的内容

- 不修改登录匹配逻辑与数据库唯一约束。
- 不支持管理员手工新增/编辑嘉宾时手机号留空（保持必填）。
- 不改变嘉宾端个人信息页展示。

## 技术决策与待确认项

- 默认手机号放入后端 `Settings.default_guest_phone`，前端登录页使用同名常量，注释标明需与后端保持一致。
- 判断"是否为默认号"采用值与默认号相等的方式；真实用户恰好使用该号码的概率极低，可接受。

## 注释要求

所有新增、修改代码的注释和 docstring 使用简体中文，遵守 `AGENTS.md` 全局注释规范。

## 涉及文件

新增：

- `docs/exec-plans/active/0080-default-phone-for-guests.md`

修改：

- `backend/app/core/config.py`
- `backend/app/services/excel_files.py`
- `backend/tests/test_excel_import.py`
- `frontend/src/views/guest/GuestLoginView.vue`
- `frontend/src/views/admin/AdminMeetingDetailView.vue`
- `docs/architecture/database.md`
- `docs/architecture/frontend.md`
- `CHANGELOG.md`

## 分步计划

1. 后端：新增默认手机号配置，导入留空填充，导出显示「未提供」。
2. 前端：登录页「默认填充」按钮，后台导入说明文案。
3. 测试与构建：补充导入与导出测试，运行 pytest 与前端构建。
4. 文档与归档：更新数据库、前端文档、CHANGELOG 并归档执行计划。

## 验收标准

1. 后端测试与前端构建通过。
2. 导入手机号留空的嘉宾成功入库并使用默认手机号；姓名留空仍报错。
3. 导出 Excel 中默认手机号显示为「未提供」。
4. 嘉宾登录页点击「默认填充」填入默认手机号。
