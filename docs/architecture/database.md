# 数据库设计

本文档记录第一版数据库设计。数据库结构变化必须同步更新本文档。

## 当前数据库状态

当前已建立数据库连接、ORM 模型和首个业务迁移：

- Python：3.12
- ORM：SQLAlchemy 2.x
- 迁移工具：Alembic
- 本地默认数据库：SQLite，默认地址 `sqlite:///./dev.db`
- 正式环境数据库：PostgreSQL，通过 `DATABASE_URL` 配置
- 配置管理：`pydantic-settings`
- 当前迁移版本：`20260707_0001_create_core_tables`

已实现核心表：

- `users`
- `meetings`
- `meeting_settings`
- `registration_fields`
- `registrations`
- `registration_values`

当前尚未实现业务 API、认证权限和数据写入流程。

## 设计约定

- 主键使用整数自增主键。
- 时间字段使用 timezone-aware `DateTime`。
- JSON 配置字段使用 SQLAlchemy `JSON` 类型。
- `meeting_settings.meeting_id` 唯一，表示一个会议只有一条设置记录。
- `registration_fields` 中 `(meeting_id, key)` 唯一，表示同一会议内字段标识不可重复。
- `registration_values.field_key` 保存提交时字段标识快照，便于字段配置变化后仍能阅读历史数据。

## users

用途：保存管理员或后续登录用户信息。

主要字段：

- `id`：主键
- `username`：用户名，唯一索引
- `password_hash`：密码哈希
- `display_name`：显示名称
- `created_at`：创建时间
- `updated_at`：更新时间

关系：

- 一个用户可以创建多个会议。

说明：

- 当前仅创建字段，不代表认证功能已完成。
- 密码不得明文存储，后续认证任务必须写入哈希值。

## meetings

用途：保存会议基础信息。

主要字段：

- `id`：主键
- `title`：会议标题
- `description`：会议说明
- `location`：会议地点
- `start_time`：开始时间
- `end_time`：结束时间
- `status`：会议状态
- `created_by`：创建人，外键关联 `users.id`
- `created_at`：创建时间
- `updated_at`：更新时间

关系：

- 一个会议属于一个创建用户。
- 一个会议有一条会议设置。
- 一个会议有多个报名字段。
- 一个会议有多条报名记录。

## meeting_settings

用途：保存会议级配置，支持后续扩展页面配置和报名规则。

主要字段：

- `id`：主键
- `meeting_id`：外键关联 `meetings.id`，唯一
- `registration_enabled`：是否开放报名
- `settings_json`：扩展配置 JSON
- `created_at`：创建时间
- `updated_at`：更新时间

关系：

- 一条会议设置属于一个会议。

## registration_fields

用途：保存某个会议的动态报名字段配置。

主要字段：

- `id`：主键
- `meeting_id`：外键关联 `meetings.id`
- `label`：字段名称
- `key`：字段标识
- `field_type`：字段类型，第一版支持 `text`、`number`、`select`
- `required`：是否必填
- `sort_order`：排序
- `options_json`：选项配置 JSON，主要用于 `select`
- `created_at`：创建时间
- `updated_at`：更新时间

约束：

- `(meeting_id, key)` 唯一。

关系：

- 一个报名字段属于一个会议。
- 报名字段的值保存在 `registration_values`。

## registrations

用途：保存报名记录主表。

主要字段：

- `id`：主键
- `meeting_id`：外键关联 `meetings.id`
- `submitted_at`：提交时间
- `created_at`：创建时间
- `updated_at`：更新时间

关系：

- 一条报名记录属于一个会议。
- 一条报名记录有多个字段值。

## registration_values

用途：保存报名记录中每个动态字段的提交值。

主要字段：

- `id`：主键
- `registration_id`：外键关联 `registrations.id`
- `field_id`：外键关联 `registration_fields.id`
- `field_key`：提交时的字段标识快照
- `value_text`：字段值文本
- `created_at`：创建时间

关系：

- 一条字段值属于一条报名记录。
- 一条字段值对应一个报名字段。

## 设计说明

动态报名数据采用 `registrations` 主表加 `registration_values` 明细表的方式保存，便于支持不同会议的不同字段配置，也便于后续做字段级查询、导出和统计。
