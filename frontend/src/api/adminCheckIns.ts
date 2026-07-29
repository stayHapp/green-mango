/** 管理员签到场次、统计与明细 API。 */

import type {
  AdminCheckInComparison,
  AdminCheckInSummary,
  CheckInSettings,
  CheckInSettingsInput,
  CheckInSession,
  CheckInSessionInput,
} from '../types'
import { apiClient, authorizationConfig } from './client'

interface AdminCheckInSessionApiResponse {
  id: number
  meeting_id: number
  title: string
  description: string | null
  starts_at: string | null
  ends_at: string | null
  is_default: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

interface AdminCheckInComparisonApiItem {
  guest_id: number
  guest_name: string
  phone: string
  checked_in_at: string
  method: 'scan' | 'manual'
  staff_name: string | null
}

interface AdminCheckInComparisonApiResponse {
  previous_session_id: number | null
  previous_session_title: string | null
  added_guests: AdminCheckInComparisonApiItem[]
  removed_guests: AdminCheckInComparisonApiItem[]
}

interface AdminCheckInSummaryApiResponse {
  session_id: number
  session_title: string
  total_guests: number
  checked_in_count: number
  unchecked_count: number
  comparison: AdminCheckInComparisonApiResponse | null
  records: Array<{
    session_id: number
    session_title: string
    guest_id: number
    guest_name: string
    phone: string
    checked_in_at: string
    method: 'scan' | 'manual'
    staff_name: string | null
  }>
}

interface AdminCheckInSettingsApiResponse {
  mode: 'single' | 'date' | 'custom'
  manual_default_session_id: number | null
  effective_session_id: number | null
  effective_session_title: string | null
}

/**
 * 将后端可能缺少时区标识的 UTC 时间补充为标准 ISO 时间。
 *
 * 入参：value 为后端日期时间字符串或空值，必填；带 `Z` 或时区偏移时保持原值。
 * 返回值：string：空值返回空字符串，无时区值追加 `Z`，已有时区值保持不变。
 * 异常：当前函数不主动抛出异常；非法时间文本保持原值，由页面格式化逻辑处理。
 */
function normalizeUtcDateTime(value: string | null): string {
  if (!value) {
    return ''
  }
  if (/Z$|[+-]\d{2}:\d{2}$/.test(value)) {
    return value
  }
  return `${value}Z`
}

/**
 * 将后端签到场次响应转换为前端业务类型。
 *
 * 入参：session 为后端签到场次响应，必填。
 * 返回值：CheckInSession：数字 ID 和下划线字段已转换。
 * 异常：当前函数不主动抛出异常。
 */
function mapCheckInSession(session: AdminCheckInSessionApiResponse): CheckInSession {
  return {
    id: String(session.id),
    meetingId: String(session.meeting_id),
    title: session.title,
    description: session.description || '',
    startsAt: normalizeUtcDateTime(session.starts_at),
    endsAt: normalizeUtcDateTime(session.ends_at),
    isDefault: session.is_default,
    sortOrder: session.sort_order,
    createdAt: normalizeUtcDateTime(session.created_at),
    updatedAt: normalizeUtcDateTime(session.updated_at),
  }
}

/**
 * 将前端签到场次表单转换为后端请求结构。
 *
 * 入参：input 为场次创建或更新数据，必填。
 * 返回值：Record<string, unknown>：符合后端蛇形字段命名的请求体。
 * 异常：当前函数不主动抛出异常。
 */
function buildSessionPayload(input: CheckInSessionInput): Record<string, unknown> {
  return {
    title: input.title,
    description: input.description || null,
    starts_at: input.startsAt || null,
    ends_at: input.endsAt || null,
    is_default: input.isDefault ?? false,
  }
}

/**
 * 将后端签到规则响应转换为前端业务类型。
 *
 * 入参：settings 为后端签到规则响应，必填。
 * 返回值：CheckInSettings：ID 已转换为字符串，空值转换为 undefined。
 * 异常：当前函数不主动抛出异常。
 */
function mapCheckInSettings(settings: AdminCheckInSettingsApiResponse): CheckInSettings {
  return {
    mode: settings.mode,
    manualDefaultSessionId: settings.manual_default_session_id ? String(settings.manual_default_session_id) : undefined,
    effectiveSessionId: settings.effective_session_id ? String(settings.effective_session_id) : undefined,
    effectiveSessionTitle: settings.effective_session_title || undefined,
  }
}

/**
 * 将后端场次差异转换为前端业务类型。
 *
 * 入参：comparison 为后端场次差异，可为空。
 * 返回值：AdminCheckInComparison | undefined：没有前一场次时返回 undefined。
 * 异常：当前函数不主动抛出异常。
 */
function mapComparison(comparison: AdminCheckInComparisonApiResponse | null): AdminCheckInComparison | undefined {
  if (!comparison || comparison.previous_session_id === null) {
    return undefined
  }
  const mapItem = (item: AdminCheckInComparisonApiItem) => ({
    guestId: String(item.guest_id),
    guestName: item.guest_name,
    phone: item.phone,
    checkedInAt: normalizeUtcDateTime(item.checked_in_at),
    method: item.method,
    staffName: item.staff_name || '人工核验',
  })
  return {
    previousSessionId: String(comparison.previous_session_id),
    previousSessionTitle: comparison.previous_session_title || '',
    addedGuests: comparison.added_guests.map(mapItem),
    removedGuests: comparison.removed_guests.map(mapItem),
  }
}

/**
 * 获取管理员有权访问会议的签到场次列表。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<CheckInSession[]>：当前会议的所有签到场次。
 * 异常：登录过期、会议未授权或网络失败时抛出异常。
 */
export async function listAdminCheckInSessions(meetingId: string): Promise<CheckInSession[]> {
  const { data } = await apiClient.get<AdminCheckInSessionApiResponse[]>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/check-in-sessions`,
    authorizationConfig('admin'),
  )
  return data.map(mapCheckInSession)
}

/**
 * 获取管理员有权访问会议的签到规则。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<CheckInSettings>：当前会议签到规则与有效场次。
 * 异常：登录过期、会议未授权或网络失败时抛出异常。
 */
export async function getAdminCheckInSettings(meetingId: string): Promise<CheckInSettings> {
  const { data } = await apiClient.get<AdminCheckInSettingsApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/check-in-settings`,
    authorizationConfig('admin'),
  )
  return mapCheckInSettings(data)
}

/**
 * 更新管理员有权维护的签到规则。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式；input 为规则更新数据，均必填。
 * 返回值：Promise<CheckInSettings>：保存后的签到规则与有效场次。
 * 异常：登录过期、会议未授权、手动默认场次不存在或网络失败时抛出异常。
 */
export async function updateAdminCheckInSettings(
  meetingId: string,
  input: CheckInSettingsInput,
): Promise<CheckInSettings> {
  const { data } = await apiClient.patch<AdminCheckInSettingsApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/check-in-settings`,
    {
      mode: input.mode,
      manual_default_session_id: input.manualDefaultSessionId ? Number(input.manualDefaultSessionId) : null,
    },
    authorizationConfig('admin'),
  )
  return mapCheckInSettings(data)
}

/**
 * 创建管理员有权维护的签到场次。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式；input 为场次表单，均必填。
 * 返回值：Promise<CheckInSession>：创建后的签到场次。
 * 异常：登录过期、会议未授权、名称重复或网络失败时抛出异常。
 */
export async function createAdminCheckInSession(
  meetingId: string,
  input: CheckInSessionInput,
): Promise<CheckInSession> {
  const { data } = await apiClient.post<AdminCheckInSessionApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/check-in-sessions`,
    buildSessionPayload(input),
    authorizationConfig('admin'),
  )
  return mapCheckInSession(data)
}

/**
 * 更新管理员有权维护的签到场次。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式；sessionId 为签到场次 ID；input 为更新表单，均必填。
 * 返回值：Promise<CheckInSession>：更新后的签到场次。
 * 异常：登录过期、会议未授权、场次不存在、名称重复或网络失败时抛出异常。
 */
export async function updateAdminCheckInSession(
  meetingId: string,
  sessionId: string,
  input: CheckInSessionInput,
): Promise<CheckInSession> {
  const { data } = await apiClient.patch<AdminCheckInSessionApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/check-in-sessions/${encodeURIComponent(sessionId)}`,
    buildSessionPayload(input),
    authorizationConfig('admin'),
  )
  return mapCheckInSession(data)
}

/**
 * 删除管理员有权维护的签到场次。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式；sessionId 为签到场次 ID，均必填。
 * 返回值：Promise<void>：删除成功后返回空结果。
 * 异常：登录过期、会议未授权、场次不存在或网络失败时抛出异常。
 */
export async function deleteAdminCheckInSession(meetingId: string, sessionId: string): Promise<void> {
  await apiClient.delete(
    `/admin/meetings/${encodeURIComponent(meetingId)}/check-in-sessions/${encodeURIComponent(sessionId)}`,
    authorizationConfig('admin'),
  )
}

/**
 * 获取管理员有权访问会议的签到统计和真实明细。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式；sessionId 为可选签到场次 ID。
 * 返回值：Promise<AdminCheckInSummary>：转换为驼峰字段的统计与明细。
 * 异常：登录过期、会议未授权或网络失败时抛出异常。
 */
export async function getAdminCheckInSummary(meetingId: string, sessionId?: string): Promise<AdminCheckInSummary> {
  const { data } = await apiClient.get<AdminCheckInSummaryApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/check-ins`,
    authorizationConfig('admin', { params: sessionId ? { session_id: Number(sessionId) } : undefined }),
  )
  return {
    sessionId: String(data.session_id),
    sessionTitle: data.session_title,
    totalGuests: data.total_guests,
    checkedInCount: data.checked_in_count,
    uncheckedCount: data.unchecked_count,
    comparison: mapComparison(data.comparison),
    records: data.records.map((record) => ({
      sessionId: String(record.session_id),
      sessionTitle: record.session_title,
      guestId: String(record.guest_id),
      guestName: record.guest_name,
      phone: record.phone,
      checkedInAt: normalizeUtcDateTime(record.checked_in_at),
      method: record.method,
      staffName: record.staff_name || '人工核验',
    })),
  }
}
