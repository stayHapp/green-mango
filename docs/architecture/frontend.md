# 前端架构

本文档记录三端前端当前结构与逐步联调边界。

## 页面结构

当前页面按三个客户端组织：

- 管理员端：统一登录、会议列表和会议详情。
- 工作人员端：统一登录、负责会议和签到工作台。
- 嘉宾端：会议入口登录、参会会议、个人资料和二维码。

## 组件规划

可逐步抽取以下组件：

- 会议基础信息表单
- 报名字段配置表格
- 报名字段编辑器
- 动态报名表渲染组件
- 报名记录表格
- 字段值展示组件

## API 请求封装

`frontend/src/api/` 已提供：

- `client.ts`：从 `VITE_API_BASE_URL` 读取基础地址，默认使用 `http://127.0.0.1:8000/api`。
- `authStorage.ts`：按管理员、工作人员、嘉宾分别保存用户展示数据、Bearer token 和过期时间。
- `sessions.ts`：三端登录、公开会议入口、嘉宾个人资料和统一退出请求。
- `adminMeetings.ts`：管理员会议列表、创建、详情和修改。
- `adminGuests.ts`：管理员嘉宾列表、新增、完整资料、动态字段读取和二维码批量生成。
- `adminExcel.ts`：管理员嘉宾导入模板、XLSX 名单上传和全量签到表下载。

授权业务 API 使用 `authorizationConfig(role)` 注入相应客户端 token；FastAPI 的 `detail` 和网络错误由统一函数转换为页面中文提示。

## 路由规划

当前主要路由：

- `/login`
- `/admin/meetings`
- `/admin/meetings/:id`
- `/meetings/:id`
- `/guest/login?meetingId=:id`
- `/guest/meetings`
- `/guest/meetings/:id`
- `/staff/meetings`
- `/staff/meetings/:id/check-in`

管理员与工作人员共用 `/login`，嘉宾必须从独立会议入口进入。

## 状态管理规划

Pinia 当前只保存三端用户和访问会话。登录成功后同步到 localStorage，页面刷新可恢复未过期会话；已过期或结构无效的存储会被自动删除。

退出登录先调用后端撤销 token，再清除 Pinia 与 localStorage。即使后端暂时不可用，本地状态也会清理；嘉宾返回原会议登录入口并清空姓名、手机号。

管理员会议列表、创建、详情和修改已通过 `frontend/src/api/adminMeetings.ts` 使用真实 API。管理员会议详情中的嘉宾列表、新增嘉宾、完整资料、动态字段和二维码生成已通过 `frontend/src/api/adminGuests.ts` 使用真实 API，并在页面内处理加载与错误状态。

管理员端 Excel 模板、名单导入和签到表导出已改用后端生成与校验。工作人员和签到资源，以及工作人员端页面仍保留 Mock，后续按执行计划逐页切换，避免把全部 API 数据放入全局状态。当前真实嘉宾在管理员会议详情中的签到状态会暂时显示为未签到，待签到统计接口联调后统一替换。
