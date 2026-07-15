/** 工作人员负责会议、嘉宾搜索和签到 API。 */

import type { CheckInRecord, Meeting } from '../types'
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
}

interface CheckInApiResponse {
  id: number
  meeting_id: number
  guest_id: number
  staff_id: number | null
  method: 'scan' | 'manual'
  checked_in_at: string
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
    startTime: meeting.start_time || '',
    endTime: meeting.end_time || '',
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
    guestId: String(record.guest_id),
    staffId: record.staff_id ? String(record.staff_id) : '',
    checkedInAt: record.checked_in_at,
    method: record.method,
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
    organization: guest.organization || '',
    title: guest.title || '',
    tag: guest.tag || '嘉宾',
    seat: guest.seat || '',
    isActive: guest.is_active,
    checkedIn: guest.checked_in,
    checkedInAt: guest.checked_in_at || '',
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
