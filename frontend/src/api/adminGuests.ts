/** 管理员嘉宾、动态字段和二维码相关 API。 */

import type { Guest, GuestField, GuestImportInput } from '../types'
import { apiClient, authorizationConfig } from './client'

interface GuestApiResponse {
  id: number
  meeting_id: number
  name: string
  phone: string
  organization: string | null
  title: string | null
  tag: string | null
  seat: string | null
  source: 'admin_entry' | 'admin_import' | 'self_registration'
  qr_token: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface GuestProfileApiResponse extends GuestApiResponse {
  values: Record<string, string | null>
}

interface GuestFieldApiResponse {
  id: number
  meeting_id: number
  label: string
  key: string
  field_type: string
  required: boolean
  visible_to_guest: boolean
  is_enabled: boolean
  sort_order: number
  options_json: Array<Record<string, unknown>>
  created_at: string
  updated_at: string
}

interface GuestLoginFieldsApiResponse {
  fields: string[]
}

interface GuestDisplayFieldsApiResponse {
  fields: string[]
}

interface GuestRegistrationFieldsApiResponse {
  fields: string[]
  required_fields: string[]
  enabled_fields: string[]
}

export interface AdminGuestDetail extends Guest {
  values: Record<string, string | null>
}

export interface AdminGuestFieldInput {
  label: string
  key: string
  type: GuestField['type']
  visibleToGuest: boolean
  required: boolean
  isEnabled: boolean
}

export interface AdminGuestRegistrationSettings {
  fields: string[]
  requiredFields: string[]
  enabledFields: string[]
}

/**
 * 将后端嘉宾响应转换为现有页面使用的嘉宾类型。
 *
 * 入参：guest 为 FastAPI 返回的嘉宾对象，必填。
 * 返回值：Guest：ID 已转为字符串，后端空值已转为空字符串。
 * 异常：当前函数不主动抛出异常；响应缺少必填字段时由页面运行错误暴露。
 */
function mapGuest(guest: GuestApiResponse): Guest {
  return {
    id: String(guest.id),
    meetingId: String(guest.meeting_id),
    name: guest.name,
    phone: guest.phone,
    organization: guest.organization || '',
    title: guest.title || '',
    tag: guest.tag || '',
    seat: guest.seat || '',
    qrToken: guest.qr_token,
    source: guest.source,
  }
}

/**
 * 将后端动态字段类型映射为当前页面支持的展示类型。
 *
 * 入参：fieldType 为后端字段类型字符串，必填。
 * 返回值：GuestField['type']：保留已支持类型，未知类型降级为普通文本。
 * 异常：当前函数不主动抛出异常。
 */
function mapGuestFieldType(fieldType: string): GuestField['type'] {
  if (fieldType === 'phone' || fieldType === 'tag' || fieldType === 'seat') {
    return fieldType
  }
  return 'text'
}

/**
 * 将后端动态字段响应转换为页面字段配置。
 *
 * 入参：field 为后端字段对象；loginFields 为当前会议登录字段集合，均必填。
 * 返回值：GuestField：字段命名和登录验证标记已适配页面。
 * 异常：当前函数不主动抛出异常。
 */
function mapGuestField(field: GuestFieldApiResponse, loginFields: Set<string>): GuestField {
  return {
    id: String(field.id),
    meetingId: String(field.meeting_id),
    label: field.label,
    key: field.key,
    type: mapGuestFieldType(field.field_type),
    required: field.required,
    visibleToGuest: field.visible_to_guest,
    usedForLogin: loginFields.has(field.key),
    sortOrder: field.sort_order,
    isEnabled: field.is_enabled,
  }
}

/**
 * 将新增嘉宾表单转换为后端请求结构。
 *
 * 入参：input 为页面新增嘉宾表单，必填；可选字段允许为空。
 * 返回值：对象：固定字段已去除首尾空白，动态字段值初始化为空对象。
 * 异常：当前函数不主动抛出异常；必填和长度规则由页面及后端共同校验。
 */
function guestPayload(input: GuestImportInput) {
  const dynamicValues = Object.fromEntries(
    Object.entries(input.values ?? {}).map(([key, value]) => [key, value?.trim() || null]),
  )
  return {
    name: input.name.trim(),
    phone: input.phone.trim(),
    organization: input.organization?.trim() || null,
    title: input.title?.trim() || null,
    tag: input.tag?.trim() || null,
    seat: input.seat?.trim() || null,
    values: dynamicValues,
  }
}

/**
 * 查询管理员有权限访问的会议嘉宾列表。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<Guest[]>：转换后的会议嘉宾列表。
 * 异常：登录失效、无权限、会议不存在或网络失败时抛出异常，由页面处理。
 */
export async function listAdminGuests(meetingId: string): Promise<Guest[]> {
  const { data } = await apiClient.get<GuestApiResponse[]>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guests`,
    authorizationConfig('admin'),
  )
  return data.map(mapGuest)
}

/**
 * 在指定会议中新增一名嘉宾。
 *
 * 入参：meetingId 为会议 ID；input 为姓名、手机号及可选固定资料，均必填。
 * 返回值：Promise<Guest>：后端创建并自动分配二维码 token 的嘉宾。
 * 异常：字段无效、登录失效、会议无权限或网络失败时抛出异常，由页面展示。
 */
export async function createAdminGuest(meetingId: string, input: GuestImportInput): Promise<Guest> {
  const { data } = await apiClient.post<GuestApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guests`,
    guestPayload(input),
    authorizationConfig('admin'),
  )
  return mapGuest(data)
}

/**
 * 修改指定会议中的嘉宾固定资料。
 *
 * 入参：meetingId 为会议 ID；guestId 为嘉宾 ID；input 为姓名、手机号及可选固定资料，均必填。
 * 返回值：Promise<Guest>：后端保存后返回的最新嘉宾资料。
 * 异常：字段无效、嘉宾不存在、登录失效、会议无权限或网络失败时抛出异常，由页面展示。
 */
export async function updateAdminGuest(
  meetingId: string,
  guestId: string,
  input: GuestImportInput,
): Promise<Guest> {
  const { data } = await apiClient.patch<GuestProfileApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guests/${encodeURIComponent(guestId)}`,
    guestPayload(input),
    authorizationConfig('admin'),
  )
  return mapGuest(data)
}

/**
 * 软删除指定会议中的嘉宾并保留历史签到数据。
 *
 * 入参：meetingId 为会议 ID；guestId 为嘉宾 ID，均必填。
 * 返回值：Promise<void>：服务端确认嘉宾停用后结束，不返回业务数据。
 * 异常：嘉宾不存在、登录失效、会议无权限或网络失败时抛出异常，由页面展示。
 */
export async function deleteAdminGuest(meetingId: string, guestId: string): Promise<void> {
  await apiClient.delete(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guests/${encodeURIComponent(guestId)}`,
    authorizationConfig('admin'),
  )
}

/**
 * 获取管理员有权限查看的嘉宾完整资料。
 *
 * 入参：meetingId 为会议 ID；guestId 为嘉宾 ID，均必填。
 * 返回值：Promise<AdminGuestDetail>：固定资料、二维码 token 与动态字段值。
 * 异常：嘉宾不存在、无会议权限、登录失效或网络失败时抛出异常。
 */
export async function getAdminGuest(meetingId: string, guestId: string): Promise<AdminGuestDetail> {
  const { data } = await apiClient.get<GuestProfileApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guests/${encodeURIComponent(guestId)}`,
    authorizationConfig('admin'),
  )
  return { ...mapGuest(data), values: data.values }
}

/**
 * 同时读取会议动态字段与登录字段配置。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<GuestField[]>：按后端顺序返回并标记登录验证用途的动态字段。
 * 异常：会议无权限、登录失效或任一请求网络失败时抛出异常，由页面处理。
 */
export async function listAdminGuestFields(meetingId: string): Promise<GuestField[]> {
  const encodedMeetingId = encodeURIComponent(meetingId)
  const [fieldResponse, loginFieldResponse] = await Promise.all([
    apiClient.get<GuestFieldApiResponse[]>(
      `/admin/meetings/${encodedMeetingId}/guest-fields`,
      authorizationConfig('admin'),
    ),
    apiClient.get<GuestLoginFieldsApiResponse>(
      `/admin/meetings/${encodedMeetingId}/guest-login-fields`,
      authorizationConfig('admin'),
    ),
  ])
  const loginFields = new Set(loginFieldResponse.data.fields)
  return fieldResponse.data.map((field) => mapGuestField(field, loginFields))
}

/**
 * 按完整目标集合增量保存指定会议的动态嘉宾字段。
 *
 * 入参：meetingId 为会议 ID；fields 为已按页面顺序排列的字段配置，均必填。
 * 返回值：Promise<GuestField[]>：后端原位更新、新增或安全删除后重新排序的完整字段列表。
 * 异常：字段标识重复、删除含值字段、修改含值字段类型、登录失效、无权限或网络失败时抛出异常，由页面展示。
 * 使用示例：`await replaceAdminGuestFields('1', [{ label: '饮食偏好', key: 'diet', type: 'text', visibleToGuest: true }])`。
 */
export async function replaceAdminGuestFields(
  meetingId: string,
  fields: AdminGuestFieldInput[],
): Promise<GuestField[]> {
  const { data } = await apiClient.put<GuestFieldApiResponse[]>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guest-fields`,
    {
      fields: fields.map((field, index) => ({
        label: field.label.trim(),
        key: field.key.trim(),
        field_type: field.type,
        required: field.required,
        visible_to_guest: field.visibleToGuest,
        is_enabled: field.isEnabled,
        sort_order: index,
        options_json: [],
      })),
    },
    authorizationConfig('admin'),
  )
  return data.map((field) => mapGuestField(field, new Set(['name', 'phone'])))
}

/**
 * 获取会议嘉宾端当前呈现的固定与动态字段 key。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<string[]>：按管理员配置顺序返回呈现字段 key。
 * 异常：登录失效、会议无权限或网络失败时抛出异常，由页面展示。
 */
export async function getAdminGuestDisplayFields(meetingId: string): Promise<string[]> {
  const { data } = await apiClient.get<GuestDisplayFieldsApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guest-display-fields`,
    authorizationConfig('admin'),
  )
  return data.fields
}

/**
 * 保存会议嘉宾端需要呈现的固定与动态字段 key。
 *
 * 入参：meetingId 为会议 ID；fields 为按呈现顺序排列的字段 key，均必填。
 * 返回值：Promise<string[]>：服务端规范化并保存后的字段 key。
 * 异常：字段不属于当前会议、登录失效、无权限或网络失败时抛出异常，由页面展示。
 * 使用示例：`await replaceAdminGuestDisplayFields('1', ['name', 'organization', 'seat'])`。
 */
export async function replaceAdminGuestDisplayFields(meetingId: string, fields: string[]): Promise<string[]> {
  const { data } = await apiClient.put<GuestDisplayFieldsApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guest-display-fields`,
    { fields },
    authorizationConfig('admin'),
  )
  return data.fields
}

/**
 * 读取固定嘉宾字段在公开报名表单中的呈现、必填和启用配置。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<AdminGuestRegistrationSettings>：已转换为前端命名的固定字段配置。
 * 异常：登录失效、会议无权限或网络失败时抛出异常。
 */
export async function getAdminGuestRegistrationSettings(meetingId: string): Promise<AdminGuestRegistrationSettings> {
  const { data } = await apiClient.get<GuestRegistrationFieldsApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guest-registration-fields`,
    authorizationConfig('admin'),
  )
  return {
    fields: data.fields,
    requiredFields: data.required_fields,
    enabledFields: data.enabled_fields,
  }
}

/**
 * 保存固定嘉宾字段在公开报名表单中的呈现、必填和启用配置。
 *
 * 入参：meetingId 为会议 ID；settings 为固定字段配置，均必填。
 * 返回值：Promise<AdminGuestRegistrationSettings>：后端规范化后的配置。
 * 异常：字段规则不合法、登录失效、会议无权限或网络失败时抛出异常。
 */
export async function replaceAdminGuestRegistrationSettings(
  meetingId: string,
  settings: AdminGuestRegistrationSettings,
): Promise<AdminGuestRegistrationSettings> {
  const { data } = await apiClient.put<GuestRegistrationFieldsApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guest-registration-fields`,
    {
      fields: settings.fields,
      required_fields: settings.requiredFields,
      enabled_fields: settings.enabledFields,
    },
    authorizationConfig('admin'),
  )
  return {
    fields: data.fields,
    requiredFields: data.required_fields,
    enabledFields: data.enabled_fields,
  }
}
