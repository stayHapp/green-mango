/** 管理员审核嘉宾自主报名申请 API。 */

import { apiClient, authorizationConfig } from './client'

export interface AdminGuestApplication {
  id: string
  meetingId: string
  name: string
  phone: string
  organization: string
  title: string
  tag: string
  seat: string
  status: 'pending' | 'approved' | 'rejected'
  guestId: string
  createdAt: string
}

interface GuestApplicationApiResponse {
  id: number
  meeting_id: number
  name: string
  phone: string
  organization: string | null
  title: string | null
  tag: string | null
  seat: string | null
  status: 'pending' | 'approved' | 'rejected'
  guest_id: number | null
  created_at: string
}

/**
 * 将报名申请接口响应转换为后台嘉宾管理页使用的对象。
 *
 * 入参：application 为后端返回的报名申请对象，必填。
 * 返回值：AdminGuestApplication：ID 已转换为字符串，空资料已转换为空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function mapGuestApplication(application: GuestApplicationApiResponse): AdminGuestApplication {
  return {
    id: String(application.id),
    meetingId: String(application.meeting_id),
    name: application.name,
    phone: application.phone,
    organization: application.organization || '',
    title: application.title || '',
    tag: application.tag || '',
    seat: application.seat || '',
    status: application.status,
    guestId: application.guest_id ? String(application.guest_id) : '',
    createdAt: application.created_at,
  }
}

/**
 * 查询当前会议全部自主报名申请。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<AdminGuestApplication[]>：按后端提交时间倒序排列的申请列表。
 * 异常：登录失效、会议无权限或网络失败时抛出异常。
 */
export async function listAdminGuestApplications(meetingId: string): Promise<AdminGuestApplication[]> {
  const { data } = await apiClient.get<GuestApplicationApiResponse[]>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guest-applications`,
    authorizationConfig('admin'),
  )
  return data.map(mapGuestApplication)
}

/**
 * 审核一条待处理的嘉宾自主报名申请。
 *
 * 入参：meetingId 为会议 ID；applicationId 为报名申请 ID；status 为 approved 或 rejected。
 * 返回值：Promise<AdminGuestApplication>：审核后的申请，批准时包含正式嘉宾 ID。
 * 异常：申请已审核、登录失效、会议无权限或网络失败时抛出异常。
 */
export async function reviewAdminGuestApplication(
  meetingId: string,
  applicationId: string,
  status: 'approved' | 'rejected',
): Promise<AdminGuestApplication> {
  const { data } = await apiClient.patch<GuestApplicationApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/guest-applications/${encodeURIComponent(applicationId)}`,
    { status },
    authorizationConfig('admin'),
  )
  return mapGuestApplication(data)
}
