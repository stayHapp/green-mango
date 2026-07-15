# 收尾前端未使用 Mock API

## 背景

管理员、工作人员和嘉宾三端业务页面已经完成真实 API 联调，`frontend/src/mock/mockApi.ts` 不再被任何运行时代码引用。原始 JSON 数据仍具有界面演示和字段设计参考价值，需要按要求保留。

## 本次范围

- 删除不再被调用的 Mock API 运行时代码。
- 删除只服务于 Mock API 的聚合类型。
- 修正业务页面和共享类型中的过期 Mock 阶段说明。
- 保留 `frontend/src/mock/data.json`，并明确其只读样例用途。

## 不在本次范围

- 不删除、改写或迁移样例 JSON 数据。
- 不删除后端种子脚本、数据库测试数据或演示账号。
- 不处理会议助手天气测试数据。

## 验证方式

- 确认 `frontend/src` 无 `mockApi` 导入。
- `cd frontend && npm run build`
- `./scripts/check_all.sh`
- `git diff --check`

## 完成记录

- 已删除无运行时引用的 `mockApi.ts` 和仅供其使用的 `MockData` 聚合类型。
- 已确认 `frontend/src` 不再引用 `mockApi`。
- `frontend/src/mock/data.json` 内容未修改，并通过同目录说明文档明确保留用途。
- 前端生产构建、后端 27 项测试及差异格式检查均通过。
