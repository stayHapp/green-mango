# 数据库设计

本文档记录当前数据库结构。结构变化必须同步更新本文档和 Alembic 迁移。

## 当前状态

- Python：3.12
- ORM：SQLAlchemy 2.x
- 迁移工具：Alembic
- 本地联调数据库：PostgreSQL，通过 `DATABASE_URL` 配置
- 本地临时回退数据库：SQLite，`sqlite:///./dev.db`
- 正式环境数据库：PostgreSQL，通过 `DATABASE_URL` 配置
- 当前迁移头：`20260731_0015`

## 表结构

- `users`：管理员和工作人员账号、scrypt 密码哈希、角色、手机号和启用状态。
- `auth_sessions`：三端统一服务端会话，保存 token 摘要、主体、过期和撤销时间。
- `meetings`、`meeting_settings`：会议基础信息、导航名称与高德坐标、首页时间显示方式、报名开关和会议级 JSON 配置。
- `meeting_admins`：会议与管理员的多对多授权。
- `staff_meetings`：会议与工作人员的多对多授权。
- `meeting_assistant_features`：会议服务五项固定功能的正文、联系人、未发布提醒、仅嘉宾可见提示、发布状态和访问级别。
- `meeting_materials`：会议资料中的多条标题、正文、附件元数据与排序。
- `guest_fields`：会议级动态嘉宾字段，包含报名页可见、必填和启用状态。
- `guests`：正式嘉宾（含同行嘉宾）、固定资料、来源、同行主嘉宾绑定、备注、启用状态和随机二维码凭证。
- `guest_values`：正式嘉宾的动态字段值。
- `check_in_sessions`：会议级签到场次，包含默认场次、时间范围和排序。
- `check_ins`：嘉宾在某个签到场次中的唯一签到记录及执行工作人员。
- `guest_applications`：公开报名申请、动态值快照、审核结果和转化后的嘉宾 ID。
- `registration_fields`、`registrations`、`registration_values`：早期通用报名模型的历史基线，当前不作为三端主流程使用。

`meeting_settings.registration_enabled` 是会议级自主报名开关，新会议默认关闭；关闭时保留公开报名接口和后台审核数据结构，但嘉宾端不展示报名入口，提交报名也不会创建申请。

## 三端 MVP 关系

```text
users --< auth_sessions
  |
  +--< meeting_admins >-- meetings --< guest_fields
  |                           |              |
  +--< staff_meetings >-------+              +--< guest_values >-- guests
  |                           |                                     |
  +--< check_ins >------------+--< check_in_sessions
  |
  +--< guest_applications >--- meetings
                  |
                  +--(批准后)--> guests

meetings --< meeting_materials
```

嘉宾会话通过 `auth_sessions.guest_id` 关联 `guests`；管理员和工作人员会话通过 `user_id` 关联 `users`。约束保证一个会话只对应其中一种主体。

`guests.companion_of_id` 是自引用外键：为空表示主嘉宾本人，非空表示该嘉宾是主嘉宾携带的同行人员。同行人员与普通嘉宾共用签到、二维码和动态字段能力，但来源固定为 `companion_registration`。服务层禁止同行嘉宾再作为主嘉宾登记其他人，保持一层同行关系。

## 核心约束

- 同一会议的同一管理员授权唯一：`uq_meeting_admins_meeting_id_user_id`。
- 同一会议的同一工作人员授权唯一：`uq_staff_meetings_meeting_id_user_id`。
- 同一会议内动态字段 key 唯一：`uq_guest_fields_meeting_id_key`。
- 同一会议内姓名和手机号相同的启用嘉宾唯一：`uq_guests_active_meeting_name_phone`；停用历史记录不占用身份。
- 同一会议内会议助手功能 key 唯一：`uq_meeting_assistant_features_meeting_id_feature_key`。
- 会议服务访问级别只能为 `public` 或 `guest`：`ck_meeting_assistant_features_access_level`。
- 每条会议资料必须至少包含正文或附件：`ck_meeting_materials_content_or_attachment`。
- 嘉宾二维码 token 全局唯一，且只承载随机凭证，不写入姓名和手机号。
- 同一嘉宾的同一动态字段值唯一：`uq_guest_values_guest_id_field_id`。
- 同一会议内签到场次名称唯一：`uq_check_in_sessions_meeting_id_title`。
- 同一嘉宾在同一签到场次只能签到一次：`uq_check_ins_session_id_guest_id`。
- 会话 token 摘要全局唯一：`ix_auth_sessions_token_hash`。
- `auth_sessions` 通过 `ck_auth_sessions_exactly_one_subject` 保证只设置 `user_id` 或 `guest_id` 之一。
- 同行嘉宾 `companion_of_id` 自引用外键使用 `ON DELETE SET NULL`，主嘉宾记录硬删除时同行嘉宾保留但解除绑定；实际流程以软停用为主，不触发级联删除。

公开报名的“同会议、同手机号只能有一条待审核申请”由服务层执行，因为已审核申请需要保留且允许之后重新提交。

## 迁移历史

1. `20260707_0001`：早期会议和通用报名基线。
2. `20260715_0002`：三端会议授权、嘉宾、动态字段和签到结构。
3. `20260715_0003`：安全认证会话表。
4. `20260715_0004`：嘉宾自主报名申请和审核字段。
5. `20260716_0005`：会议助手五项固定功能配置、发布状态和唯一约束。
6. `20260716_0006`：会议导航名称、地址和高德经纬度。
7. `20260720_0007`：嘉宾来源与动态嘉宾字段启用状态。
8. `20260721_0008`：启用嘉宾会议内姓名与手机号身份部分唯一索引。
9. `20260721_0009`：会议助手功能增加联系人 JSON 字段。
10. `20260728_0010`：会议服务增加公开或仅登录嘉宾可见的访问级别。
11. `20260728_0011`：增加会议签到场次，历史签到记录回填到默认场次，签到唯一约束调整为场次级。
12. `20260729_0012`：增加多条会议资料、附件元数据和会议外键索引，并将历史 `manual` 正文回填为首条资料。
13. `20260730_0013`：会议增加首页时间显示方式 `time_display_mode`，支持按会议选择显示到上午/下午或具体时间。
14. `20260731_0014`：会议服务增加联系会务二维码标题和图片元数据。
15. `20260731_0015`：嘉宾表增加同行人员自引用外键 `companion_of_id` 与备注 `companion_note`，支持工作人员端登记同行嘉宾。

## 会议助手结构

`meeting_assistant_features` 采用以下字段：

| 字段 | 类型 | 约束与含义 |
| --- | --- | --- |
| `id` | bigint / integer | 主键 |
| `meeting_id` | bigint / integer | 外键关联 `meetings.id`，会议删除时级联删除 |
| `feature_key` | varchar(32) | 固定为 `agenda`、`manual`、`weather`、`route`、`contact` 之一 |
| `content` | text | 管理员维护的纯文本草稿，默认空字符串 |
| `contacts` | json / jsonb | 联系会务功能的联系人列表，默认空数组 |
| `unpublished_message` | varchar(500) | 未发布时向嘉宾展示的提醒 |
| `guest_only_message` | varchar(500) | 仅登录嘉宾可见服务的未登录提示，默认“此项服务仅对已登录参会人员开放” |
| `is_published` | boolean | 当前功能是否向嘉宾发布，默认 `false` |
| `access_level` | varchar(32) | `public` 表示公开可见，`guest` 表示仅登录嘉宾可见；默认 `guest` |
| `contact_qr_title` | varchar(100) | 联系会务二维码上方文字，默认“会务二维码” |
| `contact_qr_original_filename` | varchar(255) | 联系会务二维码原始文件名，仅 `contact` 功能使用 |
| `contact_qr_storage_key` | varchar(255) | 联系会务二维码服务端存储键，不进入前端响应 |
| `contact_qr_content_type` | varchar(150) | 联系会务二维码图片媒体类型 |
| `contact_qr_size_bytes` | integer | 联系会务二维码图片大小 |
| `created_at` | datetime with timezone | 创建时间 |
| `updated_at` | datetime with timezone | 最后修改时间 |

数据库唯一约束保证同一会议同一功能只有一条记录；检查约束保证访问级别只能为 `public` 或 `guest`。应用服务负责为新会议创建五条默认配置，并在读取历史会议时补齐缺失配置。历史配置和新增配置默认使用 `guest`，避免升级或补齐时意外公开既有内容。数据库不保存天气接口响应。

## 会议资料结构

`meeting_materials` 采用以下字段：

| 字段 | 类型 | 约束与含义 |
| --- | --- | --- |
| `id` | bigint / integer | 主键 |
| `meeting_id` | bigint / integer | 外键关联 `meetings.id`，会议删除时级联删除并建立查询索引 |
| `title` | varchar(200) | 资料标题，必填 |
| `content` | text | 资料正文，默认空字符串；兼容历史普通文本与 `material-rich:` 前缀的受限文档编码，最长 20,000 字符由服务层校验 |
| `original_filename` | varchar(255) | 嘉宾下载时使用的原始文件名，可空 |
| `storage_key` | varchar(255) | 服务端生成的随机相对存储键，可空且不直接返回前端 |
| `content_type` | varchar(150) | 附件媒体类型，可空 |
| `size_bytes` | integer | 附件大小，可空 |
| `sort_order` | integer | 会议内稳定排序，默认按新增顺序递增 |
| `created_at` | datetime with timezone | 创建时间 |
| `updated_at` | datetime with timezone | 最后修改时间 |

检查约束保证正文和附件至少存在一项。资料文档不保存原始任意 HTML：前端先按标签白名单清洗，再使用 `material-rich:` 前缀和 URI 编码写入 `content`；首行缩进只保留固定 `material-first-line-indent` 类并在两端解释为 `2em`，其他属性和类名全部移除。历史普通文本在编辑与展示时安全转换为段落。附件文件使用随机存储键写入 `MATERIAL_STORAGE_DIR`，数据库只保存元数据；下载必须经过管理员会议授权、嘉宾会议归属或公开服务权限校验。单个附件默认上限 20MB，可通过 `MATERIAL_MAX_FILE_BYTES` 配置。当前文件系统存储适合单实例 MVP，多实例部署前应迁移到共享对象存储。

会议表使用 `navigation_name`、`navigation_address`、`navigation_longitude` 和 `navigation_latitude` 保存管理员确认的高德地点。路线页使用坐标生成导航链接，天气服务使用同一坐标查询和风天气；历史会议字段为空时继续按 `location` 文字匹配。

会议表使用 `time_display_mode` 控制嘉宾会议首页时间范围的展示精度。`day_period` 表示显示到上午/下午，`time` 表示显示到具体时分；历史会议和新建会议默认使用 `day_period`，管理员可在会议基础信息中切换。

嘉宾端呈现字段保存在 `meeting_settings.settings_json.guest_visible_fields`，值为固定字段与当前会议动态字段 key 组成的有序数组。该配置复用既有 JSON 字段，不新增数据库迁移；历史会议缺少该键时，服务层默认呈现全部固定字段和原先标记为嘉宾可见的动态字段。

会议级签到规则保存在同一 JSON 字段：`check_in_mode` 支持 `single`、`date`、`custom`。`single` 表示只使用一个默认签到场次；`date` 表示按日期场次自动解析当前有效场次；`custom` 表示由管理员手动维护当前默认场次。`check_in_manual_default_session_id` 只在 `date` 规则下表示管理员手动覆盖的默认场次，清空后恢复按服务端当前日期自动选择。

固定嘉宾字段在公开报名页中的配置保存在同一 JSON 字段：`guest_registration_fields` 为报名表单字段、`guest_registration_required_fields` 为必填字段、`guest_enabled_fixed_fields` 为启用字段。姓名和手机号始终启用、展示并必填，保证嘉宾登录凭证稳定。动态字段使用 `guest_fields.required`、`guest_fields.visible_to_guest` 和 `guest_fields.is_enabled` 分别表达必填、报名页呈现与启用状态。

`guest_fields.key` 是会议内稳定的动态字段业务标识。字段配置保存时按 `key` 原位更新，保留 `guest_fields.id` 以及 `guest_values.field_id` 关联；含非空嘉宾值的字段禁止删除或修改类型，没有非空填写内容的字段可以安全删除。

`guests.source` 保存正式嘉宾进入系统的方式：`admin_entry` 为后台录入、`admin_import` 为 Excel 后台导入、`self_registration` 为自主报名审核通过后生成。该字段让后台列表能够区分名单来源，不影响嘉宾登录和签到规则。

`guests.is_active=false` 表示嘉宾已软停用。停用记录及历史签到继续保存在数据库中，但不进入当前嘉宾列表、签到统计、工作人员搜索和当前名单导出。启用嘉宾使用部分唯一索引限制同一会议内 `name + phone` 身份重复；停用后允许重新录入相同身份。

`check_in_sessions` 保存会议级签到场次。每个会议通过迁移或服务兜底拥有一条“默认签到”场次；工作人员端当前扫码和人工签到写入后端计算出的当前有效场次。管理员可以新增和更新场次，用于多天、多段或返场签到统计。

`check_ins.session_id` 关联 `check_in_sessions.id`。数据库使用 `uq_check_ins_session_id_guest_id` 保证同一嘉宾在同一场次只能签到一次，但允许同一嘉宾在不同场次分别签到。管理员统计接口按选中场次计算已签到和待签到，并可比较当前场次与前一场次的新增签到和减少签到名单。

使用唯一约束 `uq_meeting_assistant_features_meeting_id_feature_key` 保证同一会议内功能标识唯一。
