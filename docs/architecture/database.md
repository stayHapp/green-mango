# 数据库设计

本文档记录数据库设计状态。数据库结构变化必须同步更新本文档。

## 当前状态

- Python：3.12
- ORM：SQLAlchemy 2.x
- 迁移工具：Alembic
- 本地默认数据库：SQLite，默认地址 `sqlite:///./dev.db`
- 正式环境数据库：PostgreSQL，通过 `DATABASE_URL` 配置
- 当前迁移版本：`20260715_0002_add_meeting_guest_checkin_models`

数据库保留早期报名相关表作为历史基线，并通过前向迁移新增当前三端 MVP 所需表：

- `users`：管理员和工作人员账号；包含角色、手机号与启用状态。
- `meetings`、`meeting_settings`：会议基础信息与会议级配置。
- `meeting_admins`：会议管理员授权关系。
- `staff_meetings`：工作人员会议授权关系。
- `guest_fields`：会议级嘉宾动态字段配置。
- `guests`：管理员录入或导入的会议嘉宾与二维码凭证。
- `guest_values`：嘉宾动态字段值。
- `check_ins`：工作人员完成的嘉宾签到记录。
- `registration_fields`、`registrations`、`registration_values`：早期报名流程的历史基线，当前不作为主流程使用。

## 三端 MVP 关系

```text
users --< meeting_admins >-- meetings --< guests --< guest_values >-- guest_fields
  |             |
  |             +--< staff_meetings >-- users
  |
  +--< check_ins >-- guests
             |
          meetings
```

## 核心约束

- 一个会议可有多个管理员，且同一管理员只可被授权一次：`uq_meeting_admins_meeting_id_user_id`。
- 一个会议可有多个工作人员，且同一工作人员只可被授权一次：`uq_staff_meetings_meeting_id_user_id`。
- 同一会议内嘉宾字段标识唯一：`uq_guest_fields_meeting_id_key`。
- 嘉宾二维码 token 全局唯一，并只保存随机凭证，不包含姓名或手机号等敏感信息。
- 同一嘉宾在同一会议只能签到一次：`uq_check_ins_meeting_id_guest_id`。
- 同一嘉宾同一动态字段只能保存一个值：`uq_guest_values_guest_id_field_id`。

## 当前边界

当前模型已能表达会议、授权、嘉宾与签到数据，但尚未实现：

- 账号认证、密码哈希策略与会话令牌。
- 会议管理员、工作人员和嘉宾的业务权限校验。
- 嘉宾二维码 token 的签发、过期与校验服务。
- 嘉宾导入、签到、导出等业务 API。

下一步应实现管理员会议与嘉宾管理的最小业务 API，并在服务层校验会议授权、动态字段归属和嘉宾登录规则。
