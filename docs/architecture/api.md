# API 设计

本文档记录三端 MVP 当前已实现的 HTTP API。统一前缀为 `/api`，交互式文档由 FastAPI 提供在 `/docs`。

## 认证约定

- 管理员、工作人员使用账号和密码分别调用登录接口。
- 嘉宾使用会议 ID、姓名和手机号登录。
- 登录成功返回 `access_token`、`token_type= bearer`、主体信息和过期时间。
- 受保护接口统一携带 `Authorization: Bearer <access_token>`。
- token 只在签发响应中返回；数据库仅保存 SHA-256 摘要，支持过期和主动撤销。
- 三端共用 `POST /api/sessions/logout` 退出当前会话。
- 旧的 `X-Admin-Id`、`X-Staff-Id`、`X-Guest-Id` 开发期请求头已删除。

## 通用与会话接口

| 方法 | 路径 | 权限 | 用途 |
| --- | --- | --- | --- |
| GET | `/api/health` | 公开 | 健康检查 |
| GET | `/api/meetings/{meeting_id}` | 公开 | 嘉宾入口登录前读取已发布会议基础信息 |
| POST | `/api/admin/sessions` | 公开 | 管理员账号密码登录 |
| POST | `/api/staff/sessions` | 公开 | 工作人员账号密码登录 |
| POST | `/api/guest/sessions` | 公开 | 嘉宾按会议、姓名、手机号登录 |
| POST | `/api/sessions/logout` | 已登录 | 撤销当前服务端会话 |

## 管理员会议接口

以下接口要求管理员 Bearer token。会议级资源还会校验 `meeting_admins` 授权，不存在和越权统一返回 404，避免泄露资源是否存在。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/admin/meetings` | 查询当前管理员可管理的会议 |
| POST | `/api/admin/meetings` | 创建会议、默认设置和创建人授权 |
| GET | `/api/admin/meetings/{meeting_id}` | 获取会议详情 |
| PATCH | `/api/admin/meetings/{meeting_id}` | 修改会议基础信息与状态 |
| GET | `/api/admin/meetings/{meeting_id}/location-options?query={keyword}` | 通过后端高德代理搜索导航地点候选项 |
| GET | `/api/admin/meetings/{meeting_id}/admins` | 查询会议管理员 |
| POST | `/api/admin/meetings/{meeting_id}/admins` | 按账号添加已有管理员 |
| DELETE | `/api/admin/meetings/{meeting_id}/admins/{user_id}` | 移除非创建人管理员授权 |

会议结束时间必须晚于开始时间。创建人不能从自己的会议中移除。

## 管理员嘉宾接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET / PUT | `/api/admin/meetings/{meeting_id}/guest-fields` | 获取或按稳定 key 增量保存动态字段配置 |
| GET / PUT | `/api/admin/meetings/{meeting_id}/guest-display-fields` | 获取或全量保存嘉宾端呈现字段，支持固定字段与动态字段 |
| GET / PUT | `/api/admin/meetings/{meeting_id}/guest-registration-fields` | 获取或保存固定字段在自主报名表单中的呈现、必填和启用配置 |
| GET / PUT | `/api/admin/meetings/{meeting_id}/guest-login-fields` | 获取或确认登录字段，MVP 固定为 `name + phone` |
| GET / POST | `/api/admin/meetings/{meeting_id}/guests` | 查询或录入单个嘉宾 |
| GET / PATCH / DELETE | `/api/admin/meetings/{meeting_id}/guests/{guest_id}` | 查询完整资料、修改或软停用嘉宾 |
| GET | `/api/admin/meetings/{meeting_id}/guests/import-template` | 下载当前会议 XLSX 导入模板 |
| POST | `/api/admin/meetings/{meeting_id}/guests/import` | 上传 XLSX 并返回成功数和逐行错误 |

嘉宾固定字段为姓名、手机号、单位、职务、身份和座位号。动态值通过 `values` 对象传递，后台单个新增、编辑、详情和 Excel 导入导出均支持当前启用的动态字段。呈现字段接口使用有序字段 key 数组；固定 key 为 `name`、`phone`、`organization`、`title`、`tag`、`seat`，动态 key 必须属于当前会议。固定字段报名配置接口返回 `fields`、`required_fields` 和 `enabled_fields` 三个数组；姓名和手机号不可关闭。导入模板只包含当前启用的动态字段；姓名、手机号和启用的动态必填字段必须填写，文件最大 10MB、单次最多 10,000 行。合法行会导入，错误行不会阻断其他合法行。

动态字段 PUT 接口接收完整目标集合，但会按稳定 `key` 增量对账：已有字段原位更新并保留 ID 与嘉宾值，新字段新增，无非空填写内容的字段可删除。已有非空嘉宾值的字段不能删除或修改字段类型；名称、排序、必填、报名展示、个人信息展示和启用状态可以安全修改。

`GET /api/admin/meetings/{meeting_id}/guests` 的正式嘉宾响应新增 `source`：`admin_entry`（后台录入）、`admin_import`（后台导入）或 `self_registration`（自主报名审核通过）。

嘉宾在后台新增、Excel 导入或自主报名审核通过时自动生成全局唯一的随机 `qr_token`，其中不包含个人信息。`qr_token` 是正式嘉宾的必填数据，不提供管理员手动或批量补生成入口。同一会议内姓名和手机号相同的启用嘉宾不能重复创建。删除操作为软停用并保留历史签到记录；停用嘉宾不再进入当前嘉宾列表、签到统计、工作人员搜索和当前名单导出，停用后允许重新录入相同身份。

## 管理员工作人员接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET / POST | `/api/admin/meetings/{meeting_id}/staff` | 查询工作人员，或创建账号并授权会议 |
| PATCH | `/api/admin/meetings/{meeting_id}/staff/{staff_id}` | 修改资料、启用状态或密码 |
| DELETE | `/api/admin/meetings/{meeting_id}/staff/{staff_id}` | 解除当前会议授权 |

创建工作人员时必须提供唯一账号和至少 8 位初始密码。已有同名工作人员再次加入会议时只补充授权，不创建重复账号。

## 管理员签到接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/admin/meetings/{meeting_id}/check-ins` | 获取总数、已签到数、未签到数和明细 |
| GET | `/api/admin/meetings/{meeting_id}/check-ins/export` | 导出全量嘉宾签到 XLSX |
| GET | `/api/admin/meetings/{meeting_id}/guests/export` | 导出嘉宾信息、来源、管理状态和签到状态 XLSX |

签到导出文件同时包含当前启用的已签到和未签到嘉宾，以及签到时间、方式和执行工作人员。嘉宾状态表同时包含当前启用正式嘉宾、待审核和已拒绝报名申请；已通过报名以正式嘉宾记录呈现，避免重复。软停用嘉宾及其历史签到仍保留在数据库中，但不进入当前名单导出。

## 管理员会议助手接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/admin/meetings/{meeting_id}/assistant-features` | 获取会议固定五项会议助手配置 |
| PATCH | `/api/admin/meetings/{meeting_id}/assistant-features/{feature_key}` | 修改单项正文、未发布提醒和发布状态 |

`feature_key` 只接受 `agenda`、`manual`、`weather`、`route`、`contact`。正文为纯文本且最长 20,000 字符，未发布提醒为纯文本且最长 500 字符。管理员必须拥有当前会议授权；不受支持的功能标识返回 422。

## 嘉宾端接口

以下接口除登录外均要求嘉宾 Bearer token，并校验嘉宾属于路径中的会议且处于启用状态。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/guest/meetings` | 查询当前嘉宾的会议列表 |
| GET | `/api/guest/meetings/{meeting_id}` | 查询会议和个人参会概要 |
| GET | `/api/guest/meetings/{meeting_id}/profile` | 查询固定资料、动态字段值、呈现字段 `visible_fields` 与动态标签 `field_labels` |
| GET | `/api/guest/meetings/{meeting_id}/check-in-qr` | 获取个人签到二维码 token 与过期时间 |
| GET | `/api/guest/meetings/{meeting_id}/assistant-features/{feature_key}` | 获取单项会议助手公开内容或未发布提醒 |
| GET | `/api/guest/meetings/{meeting_id}/weather` | 获取已发布天气功能的和风天气实况与七日预报；优先使用管理员确认的导航坐标 |

二维码图像由前端把 `qr_token` 编码为二维码；工作人员扫码后只把 token 交给后端校验。二维码在会议结束后失效。

会议助手功能已发布时返回 `content`；未发布时只返回 `unpublished_message` 和发布状态，响应中的 `content` 必须为 `null`，避免草稿泄露。嘉宾只能访问自己所属会议的会议助手内容。

二维码响应包含 `is_checked_in` 和可空的 `checked_in_at`，两个字段从 `check_ins` 读取，不改变二维码 token 与过期规则。SQLite 读取出的无时区签到时间在响应前按 UTC 恢复，前端按嘉宾本地时区展示。

## 工作人员端接口

以下接口要求工作人员 Bearer token，并校验 `staff_meetings` 会议授权。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/staff/meetings` | 查询负责会议 |
| GET | `/api/staff/meetings/{meeting_id}/guests?query={keyword}` | 按姓名、手机号、单位或座位搜索嘉宾 |
| POST | `/api/staff/meetings/{meeting_id}/check-ins/scan` | 提交 `qr_token` 扫码签到 |
| POST | `/api/staff/meetings/{meeting_id}/check-ins/manual` | 提交 `guest_id` 人工签到 |
| GET | `/api/staff/meetings/{meeting_id}/check-ins` | 查询会议签到记录 |

签到由后端判断工作人员授权、嘉宾归属、嘉宾启用状态、会议结束时间和重复签到。重复签到返回 409；无效、跨会议或过期二维码不会创建记录。

## 嘉宾补充报名接口

| 方法 | 路径 | 权限 | 用途 |
| --- | --- | --- | --- |
| POST | `/api/meetings/{meeting_id}/guest-applications` | 公开 | 向已发布、未结束且开放报名的会议提交申请 |
| GET | `/api/admin/meetings/{meeting_id}/guest-applications?status=pending` | 会议管理员 | 查询并按状态筛选申请 |
| PATCH | `/api/admin/meetings/{meeting_id}/guest-applications/{application_id}` | 会议管理员 | 批准或拒绝待审核申请 |

同一会议和手机号只能存在一条待审核申请。批准后系统创建正式嘉宾、动态字段值和随机二维码 token，并将正式嘉宾 ID 写回申请；申请不能重复审核。

`GET /api/meetings/{meeting_id}` 的公开响应包含 `registration_fields`，由固定字段报名配置和已启用的动态字段共同组成。嘉宾端应按此字段集合渲染报名表单并提交动态值，确保后台字段配置能够直接作用于自主报名链路。

## 状态码和设计原则

- `200/201`：请求成功或资源创建成功。
- `401`：缺少、错误、过期或已撤销的登录凭证。
- `403`：会话主体角色错误或账号已停用。
- `404`：资源不存在、会议未开放，或当前主体没有会议授权。
- `409`：重复签到等资源状态冲突。
- `422`：请求字段或业务规则校验失败。

前端校验只改善体验，后端始终执行最终权限、字段归属、时间范围和数据一致性判断。
