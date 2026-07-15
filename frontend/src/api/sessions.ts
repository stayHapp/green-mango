/** 三端登录、嘉宾入口资料和统一退出 API。 */

import type { AdminUser, ClientRole, Guest, Meeting, StaffUser } from '../types'
import type { AccessSession } from './authStorage'
import { apiClient, authorizationConfig } from './client'

interface SessionApiResponse {
  access_token: string
  token_type: string
  expires_at: string
  subject_id: number
  subject_type: 'admin' | 'staff'
}

interface GuestSessionApiResponse {
  access_token: string
  token_type: string
  expires_at: string
  guest_id: number
  meeting_id: number
  name: string
}

interface PublicMeetingApiResponse {
  id: number
  title: string
  description: string | null
  location: string | null
  start_time: string | null
  end_time: string | null
  status: 'draft' | 'published' | 'ended'
  registration_enabled: boolean
  guest_login_fields: string[]
}

interface GuestProfileApiResponse {
  id: number
  meeting_id: number
  name: string
  phone: string
  organization: string | null
  title: string | null
  tag: string | null
  seat: string | null
  qr_token: string
}

export interface LoginResult<T> {
  user: T
  access: AccessSession
}

/**
 * 把管理员或工作人员登录响应转换为前端会话结构。
 *
 * 入参：response 为后端会话响应；role 为目标角色；username 为登录账号，均必填。
 * 返回值：LoginResult<AdminUser | StaffUser>：兼容现有页面展示的数据和访问会话。
 * 异常：后端角色与请求角色不一致时抛出 Error。
 */
function mapUserSession(
  response: SessionApiResponse,
  role: 'admin' | 'staff',
  username: string,
): LoginResult<AdminUser | StaffUser> {
  if (response.subject_type !== role) {
    throw new Error('后端返回的登录角色不匹配。')
  }
  const access: AccessSession = {
    accessToken: response.access_token,
    tokenType: response.token_type,
    expiresAt: response.expires_at,
    subjectId: response.subject_id,
    subjectType: role,
  }
  if (role === 'admin') {
    return { user: { id: String(response.subject_id), name: username, phone: '' }, access }
  }
  return {
    user: { id: String(response.subject_id), name: username, phone: '', account: username, meetingIds: [] },
    access,
  }
}

/**
 * 使用账号和密码创建管理员会话。
 *
 * 入参：username 为管理员账号；password 为 8 至 128 位密码，均必填。
 * 返回值：Promise<LoginResult<AdminUser>>：管理员展示数据和 Bearer 会话。
 * 异常：凭据错误、网络失败或响应角色异常时抛出异常，由页面转换为提示。
 */
export async function loginAdmin(username: string, password: string): Promise<LoginResult<AdminUser>> {
  const { data } = await apiClient.post<SessionApiResponse>('/admin/sessions', { username, password })
  return mapUserSession(data, 'admin', username) as LoginResult<AdminUser>
}

/**
 * 使用账号和密码创建工作人员会话。
 *
 * 入参：username 为工作人员账号；password 为 8 至 128 位密码，均必填。
 * 返回值：Promise<LoginResult<StaffUser>>：工作人员展示数据和 Bearer 会话。
 * 异常：凭据错误、网络失败或响应角色异常时抛出异常，由页面转换为提示。
 */
export async function loginStaff(username: string, password: string): Promise<LoginResult<StaffUser>> {
  const { data } = await apiClient.post<SessionApiResponse>('/staff/sessions', { username, password })
  return mapUserSession(data, 'staff', username) as LoginResult<StaffUser>
}

/**
 * 获取嘉宾登录前可见的会议入口信息。
 *
 * 入参：meetingId 为后端数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<Meeting>：转换为现有页面兼容格式的会议数据。
 * 异常：会议不存在、尚未发布或网络失败时抛出异常。
 */
export async function getPublicMeeting(meetingId: string): Promise<Meeting> {
  const { data } = await apiClient.get<PublicMeetingApiResponse>(`/meetings/${encodeURIComponent(meetingId)}`)
  return {
    id: String(data.id),
    title: data.title,
    description: data.description || '',
    location: data.location || '',
    startTime: data.start_time || '',
    endTime: data.end_time || '',
    status: data.status,
    adminIds: [],
    staffIds: [],
  }
}

/**
 * 按会议、姓名和手机号登录嘉宾端，并读取完整个人资料。
 *
 * 入参：meetingId 为数字会议 ID 字符串；name 和 phone 为嘉宾身份信息，均必填。
 * 返回值：Promise<LoginResult<Guest>>：完整嘉宾展示数据和 Bearer 会话。
 * 异常：身份不匹配、会议无效、资料读取失败或网络异常时抛出异常。
 */
export async function loginGuest(
  meetingId: string,
  name: string,
  phone: string,
): Promise<LoginResult<Guest>> {
  const { data: session } = await apiClient.post<GuestSessionApiResponse>('/guest/sessions', {
    meeting_id: Number(meetingId),
    name,
    phone,
  })
  const access: AccessSession = {
    accessToken: session.access_token,
    tokenType: session.token_type,
    expiresAt: session.expires_at,
    subjectId: session.guest_id,
    subjectType: 'guest',
  }
  // 个人资料接口需要刚签发的 token，此时会话尚未写入 localStorage，因此直接设置请求头。
  const { data: profile } = await apiClient.get<GuestProfileApiResponse>(
    `/guest/meetings/${session.meeting_id}/profile`,
    { headers: { Authorization: `Bearer ${access.accessToken}` } },
  )
  return {
    access,
    user: {
      id: String(profile.id),
      meetingId: String(profile.meeting_id),
      name: profile.name,
      phone: profile.phone,
      organization: profile.organization || '',
      title: profile.title || '',
      tag: profile.tag || '嘉宾',
      seat: profile.seat || '',
      qrToken: profile.qr_token,
    },
  }
}

/**
 * 撤销指定客户端当前服务端会话。
 *
 * 入参：role 为当前退出的 admin、staff 或 guest，必填。
 * 返回值：Promise<void>：后端确认撤销后结束。
 * 异常：本地 token 缺失、已失效或网络异常时抛出异常；调用方仍应清理本地状态。
 */
export async function logoutClientSession(role: ClientRole): Promise<void> {
  await apiClient.post('/sessions/logout', undefined, authorizationConfig(role))
}
