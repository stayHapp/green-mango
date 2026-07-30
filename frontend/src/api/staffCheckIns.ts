/** 工作人员负责会议、嘉宾搜索和签到 API。 */

import axios from 'axios'

import type { AlreadyCheckedInInfo, CheckInRecord, Meeting, StaffCheckInSession } from '../types'
import { apiClient, authorizationConfig } from './client'

interface StaffMeetingApiResponse {
  id: number
  title: string
  description: string | null
  location: string | null
  start_time: string | null
  end_time: string | null
  status: Meeting['status']
}

interface StaffGuestApiResponse {
  id: number
  name: string
  phone: string
  organization: string | null
  title: string | null
  tag: string | null
  seat: string | null
  is_active: boolean
  checked_in: boolean
  checked_in_at: string | null
  visible_fields: string[]
}

interface CheckInApiResponse {
  id: number
  meeting_id: number
  session_id: number
  session_title: string
  guest_id: number
  staff_id: number | null
  method: 'scan' | 'manual'
  checked_in_at: string
}

interface StaffCheckInSessionApiResponse {
  id: number
  title: string
  starts_at: string | null
  ends_at: string | null
  is_default: boolean
}

interface AlreadyCheckedInApiDetail {
  code: 'already_checked_in'
  message: string
  guest_id: number
  guest_name: string
  phone: string
  checked_in_at: string
  method: 'scan' | 'manual'
  staff_id: number | null
  staff_name: string | null
}

export interface StaffGuest {
  id: string
  name: string
  phone: string
  organization: string
  title: string
  tag: string
  seat: string
  isActive: boolean
  checkedIn: boolean
  checkedInAt: string
  visibleFields: string[]
}

/**
 * 将后端可能缺少时区标识的 UTC 时间补充为标准 ISO 时间。
 *
 * 入参：value 为后端日期时间字符串或空值，必填；带 `Z` 或时区偏移时保持原值。
 * 返回值：string：空值返回空字符串，无时区值追加 `Z`，已有时区值保持不变。
 * 异常：当前函数不主动抛出异常；非法时间文本保持原值，由页面日期格式化逻辑处理。
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
 * 将工作人员会议响应转换为共享会议类型。
 *
 * 入参：meeting 为后端会议响应，必填。
 * 返回值：Meeting：空值和字段名已适配页面。
 * 异常：当前函数不主动抛出异常。
 */
function mapMeeting(meeting: StaffMeetingApiResponse): Meeting {
  return {
    id: String(meeting.id),
    title: meeting.title,
    description: meeting.description || '',
    location: meeting.location || '',
    navigationName: '',
    navigationAddress: '',
    navigationLongitude: undefined,
    navigationLatitude: undefined,
    startTime: meeting.start_time || '',
    endTime: meeting.end_time || '',
    timeDisplayMode: 'day_period',
    status: meeting.status,
    adminIds: [],
    staffIds: [],
  }
}

/**
 * 将签到响应转换为共享签到记录。
 *
 * 入参：record 为后端签到响应，必填。
 * 返回值：CheckInRecord：数字 ID 和字段名已转换。
 * 异常：当前函数不主动抛出异常。
 */
function mapCheckIn(record: CheckInApiResponse): CheckInRecord {
  return {
    id: String(record.id),
    meetingId: String(record.meeting_id),
    sessionId: String(record.session_id),
    sessionTitle: record.session_title,
    guestId: String(record.guest_id),
    staffId: record.staff_id ? String(record.staff_id) : '',
    checkedInAt: normalizeUtcDateTime(record.checked_in_at),
    method: record.method,
  }
}

/**
 * 将工作人员端当前签到场次响应转换为前端业务类型。
 *
 * 入参：session 为后端当前场次响应，必填。
 * 返回值：StaffCheckInSession：数字 ID 和下划线字段已转换。
 * 异常：当前函数不主动抛出异常。
 */
function mapStaffCheckInSession(session: StaffCheckInSessionApiResponse): StaffCheckInSession {
  return {
    id: String(session.id),
    title: session.title,
    startsAt: normalizeUtcDateTime(session.starts_at),
    endsAt: normalizeUtcDateTime(session.ends_at),
    isDefault: session.is_default,
  }
}

/**
 * 判断后端错误明细是否为重复签到结构化数据。
 *
 * 入参：detail 为后端 HTTP 错误 detail 字段，可为任意类型。
 * 返回值：boolean：字段满足重复签到明细格式时返回 true。
 * 异常：当前函数不主动抛出异常。
 */
function isAlreadyCheckedInApiDetail(detail: unknown): detail is AlreadyCheckedInApiDetail {
  if (!detail || typeof detail !== 'object') {
    return false
  }
  const payload = detail as Partial<AlreadyCheckedInApiDetail>
  return payload.code === 'already_checked_in' && typeof payload.guest_id === 'number'
}

/**
 * 将重复签到错误明细转换为前端展示结构。
 *
 * 入参：detail 为后端重复签到明细，必填。
 * 返回值：AlreadyCheckedInInfo：字段名已转换，时间补齐 UTC 时区。
 * 异常：当前函数不主动抛出异常。
 */
function mapAlreadyCheckedInDetail(detail: AlreadyCheckedInApiDetail): AlreadyCheckedInInfo {
  return {
    message: detail.message,
    guestId: String(detail.guest_id),
    guestName: detail.guest_name,
    phone: detail.phone,
    checkedInAt: normalizeUtcDateTime(detail.checked_in_at),
    method: detail.method,
    staffId: detail.staff_id ? String(detail.staff_id) : '',
    staffName: detail.staff_name || '未知工作人员',
  }
}

/**
 * 查询当前工作人员负责的真实会议列表。
 *
 * 入参：无；工作人员 token 从本地会话读取。
 * 返回值：Promise<Meeting[]>：后端授权的会议列表。
 * 异常：登录过期、账号停用或网络失败时抛出异常。
 */
export async function listStaffMeetings(): Promise<Meeting[]> {
  const { data } = await apiClient.get<StaffMeetingApiResponse[]>('/staff/meetings', authorizationConfig('staff'))
  return data.map(mapMeeting)
}

/**
 * 按关键词查询会议嘉宾及其签到状态。
 *
 * 入参：meetingId 为会议 ID；query 为姓名、手机号、单位或座位关键词，均必填，关键词可为空。
 * 返回值：Promise<StaffGuest[]>：真实嘉宾搜索结果和签到状态。
 * 异常：会议未授权、登录过期或网络失败时抛出异常。
 */
export async function searchStaffGuests(meetingId: string, query: string): Promise<StaffGuest[]> {
  const { data } = await apiClient.get<StaffGuestApiResponse[]>(
    `/staff/meetings/${encodeURIComponent(meetingId)}/guests`,
    authorizationConfig('staff', { params: { query } }),
  )
  return data.map((guest) => ({
    id: String(guest.id),
    name: guest.name,
    phone: guest.phone,
    organization: guest.visible_fields.includes('organization') ? guest.organization || '' : '',
    title: guest.visible_fields.includes('title') ? guest.title || '' : '',
    tag: guest.visible_fields.includes('tag') ? guest.tag || '嘉宾' : '',
    seat: guest.visible_fields.includes('seat') ? guest.seat || '' : '',
    isActive: guest.is_active,
    checkedIn: guest.checked_in,
    checkedInAt: normalizeUtcDateTime(guest.checked_in_at),
    visibleFields: guest.visible_fields,
  }))
}

/**
 * 查询工作人员有权查看的会议签到记录。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<CheckInRecord[]>：按后端时间倒序返回的记录。
 * 异常：会议未授权、登录过期或网络失败时抛出异常。
 */
export async function listStaffCheckIns(meetingId: string): Promise<CheckInRecord[]> {
  const { data } = await apiClient.get<CheckInApiResponse[]>(
    `/staff/meetings/${encodeURIComponent(meetingId)}/check-ins`,
    authorizationConfig('staff'),
  )
  return data.map(mapCheckIn)
}

/**
 * 查询工作人员端当前有效签到场次。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<StaffCheckInSession>：当前扫码和手工签到实际写入的场次。
 * 异常：会议未授权、登录过期或网络失败时抛出异常。
 */
export async function getStaffCheckInSession(meetingId: string): Promise<StaffCheckInSession> {
  const { data } = await apiClient.get<StaffCheckInSessionApiResponse>(
    `/staff/meetings/${encodeURIComponent(meetingId)}/check-in-session`,
    authorizationConfig('staff'),
  )
  return mapStaffCheckInSession(data)
}

/**
 * 提交二维码 token 完成真实扫码签到。
 *
 * 入参：meetingId 为会议 ID；qrToken 为二维码随机凭证，均必填。
 * 返回值：Promise<CheckInRecord>：新建的签到记录。
 * 异常：无权限、二维码无效、会议结束、嘉宾停用或重复签到时抛出后端错误。
 */
export async function scanStaffCheckIn(meetingId: string, qrToken: string): Promise<CheckInRecord> {
  const { data } = await apiClient.post<CheckInApiResponse>(
    `/staff/meetings/${encodeURIComponent(meetingId)}/check-ins/scan`,
    { qr_token: qrToken },
    authorizationConfig('staff'),
  )
  return mapCheckIn(data)
}

/**
 * 按嘉宾 ID 完成真实人工签到。
 *
 * 入参：meetingId 为会议 ID；guestId 为嘉宾 ID，均必填。
 * 返回值：Promise<CheckInRecord>：新建的签到记录。
 * 异常：无权限、会议结束、嘉宾失效或重复签到时抛出后端错误。
 */
export async function manualStaffCheckIn(meetingId: string, guestId: string): Promise<CheckInRecord> {
  const { data } = await apiClient.post<CheckInApiResponse>(
    `/staff/meetings/${encodeURIComponent(meetingId)}/check-ins/manual`,
    { guest_id: Number(guestId) },
    authorizationConfig('staff'),
  )
  return mapCheckIn(data)
}

/**
 * 从签到接口异常中提取重复签到明细。
 *
 * 入参：error 为扫码或人工签到接口抛出的异常，必填。
 * 返回值：AlreadyCheckedInInfo | undefined：重复签到时返回结构化展示数据，其他错误返回 undefined。
 * 异常：当前函数不主动抛出异常。
 */
export function getAlreadyCheckedInDetail(error: unknown): AlreadyCheckedInInfo | undefined {
  if (!axios.isAxiosError(error)) {
    return undefined
  }
  const detail = error.response?.data?.detail
  return isAlreadyCheckedInApiDetail(detail) ? mapAlreadyCheckedInDetail(detail) : undefined
}
