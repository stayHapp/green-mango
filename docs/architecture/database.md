# 数据库设计

本文档记录当前数据库结构。结构变化必须同步更新本文档和 Alembic 迁移。

## 当前状态

- Python：3.12
- ORM：SQLAlchemy 2.x
- 迁移工具：Alembic
- 本地默认数据库：SQLite，`sqlite:///./dev.db`
- 正式环境数据库：PostgreSQL，通过 `DATABASE_URL` 配置
- 当前迁移头：`20260716_0005`

## 表结构

- `users`：管理员和工作人员账号、scrypt 密码哈希、角色、手机号和启用状态。
- `auth_sessions`：三端统一服务端会话，保存 token 摘要、主体、过期和撤销时间。
- `meetings`、`meeting_settings`：会议基础信息、导航名称与高德坐标、报名开关和会议级 JSON 配置。
- `meeting_admins`：会议与管理员的多对多授权。
- `staff_meetings`：会议与工作人员的多对多授权。
- `meeting_assistant_features`：会议助手五项固定功能的正文、未发布提醒和发布状态。
- `guest_fields`：会议级动态嘉宾字段。
- `guests`：正式嘉宾、固定资料、启用状态和随机二维码凭证。
- `guest_values`：正式嘉宾的动态字段值。
- `check_ins`：嘉宾唯一签到记录及执行工作人员。
- `guest_applications`：公开报名申请、动态值快照、审核结果和转化后的嘉宾 ID。
- `registration_fields`、`registrations`、`registration_values`：早期通用报名模型的历史基线，当前不作为三端主流程使用。

## 三端 MVP 关系

```text
users --< auth_sessions
  |
  +--< meeting_admins >-- meetings --< guest_fields
  |                           |              |
  +--< staff_meetings >-------+              +--< guest_values >-- guests
  |                           |                                     |
  +--< check_ins >------------+-------------------------------------+
  |
  +--< guest_applications >--- meetings
                  |
                  +--(批准后)--> guests
```

嘉宾会话通过 `auth_sessions.guest_id` 关联 `guests`；管理员和工作人员会话通过 `user_id` 关联 `users`。约束保证一个会话只对应其中一种主体。

## 核心约束

- 同一会议的同一管理员授权唯一：`uq_meeting_admins_meeting_id_user_id`。
- 同一会议的同一工作人员授权唯一：`uq_staff_meetings_meeting_id_user_id`。
- 同一会议内动态字段 key 唯一：`uq_guest_fields_meeting_id_key`。
- 同一会议内会议助手功能 key 唯一：`uq_meeting_assistant_features_meeting_id_feature_key`。
- 嘉宾二维码 token 全局唯一，且只承载随机凭证，不写入姓名和手机号。
- 同一嘉宾的同一动态字段值唯一：`uq_guest_values_guest_id_field_id`。
- 同一嘉宾在同一会议只能签到一次：`uq_check_ins_meeting_id_guest_id`。
- 会话 token 摘要全局唯一：`ix_auth_sessions_token_hash`。
- `auth_sessions` 通过 `ck_auth_sessions_exactly_one_subject` 保证只设置 `user_id` 或 `guest_id` 之一。

公开报名的“同会议、同手机号只能有一条待审核申请”由服务层执行，因为已审核申请需要保留且允许之后重新提交。

## 迁移历史

1. `20260707_0001`：早期会议和通用报名基线。
2. `20260715_0002`：三端会议授权、嘉宾、动态字段和签到结构。
3. `20260715_0003`：安全认证会话表。
4. `20260715_0004`：嘉宾自主报名申请和审核字段。
5. `20260716_0005`：会议助手五项固定功能配置、发布状态和唯一约束。

## 会议助手结构

`meeting_assistant_features` 采用以下字段：

| 字段 | 类型 | 约束与含义 |
| --- | --- | --- |
| `id` | bigint / integer | 主键 |
| `meeting_id` | bigint / integer | 外键关联 `meetings.id`，会议删除时级联删除 |
| `feature_key` | varchar(32) | 固定为 `agenda`、`manual`、`weather`、`route`、`contact` 之一 |
| `content` | text | 管理员维护的纯文本草稿，默认空字符串 |
| `unpublished_message` | varchar(500) | 未发布时向嘉宾展示的提醒 |
| `is_published` | boolean | 当前功能是否向嘉宾发布，默认 `false` |
| `created_at` | datetime with timezone | 创建时间 |
| `updated_at` | datetime with timezone | 最后修改时间 |

数据库唯一约束保证同一会议同一功能只有一条记录；应用服务负责为新会议创建五条默认配置，并在读取历史会议时补齐缺失配置。数据库不保存天气接口响应。

会议表使用 `navigation_name`、`navigation_address`、`navigation_longitude` 和 `navigation_latitude` 保存管理员确认的高德地点。路线页使用坐标生成导航链接，天气服务使用同一坐标查询和风天气；历史会议字段为空时继续按 `location` 文字匹配。

使用唯一约束 `uq_meeting_assistant_features_meeting_id_feature_key` 保证同一会议内功能标识唯一。
