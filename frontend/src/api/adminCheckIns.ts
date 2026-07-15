/** 管理员签到统计与明细 API。 */

import type { AdminCheckInSummary } from '../types'
import { apiClient, authorizationConfig } from './client'

interface AdminCheckInSummaryApiResponse {
  total_guests: number
  checked_in_count: number
  unchecked_count: number
  records: Array<{
    guest_id: number
    guest_name: string
    phone: string
    checked_in_at: string
    method: 'scan' | 'manual'
    staff_name: string | null
  }>
}

/**
 * 获取管理员有权访问会议的签到统计和真实明细。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<AdminCheckInSummary>：转换为驼峰字段的统计与明细。
 * 异常：登录过期、会议未授权或网络失败时抛出异常。
 */
export async function getAdminCheckInSummary(meetingId: string): Promise<AdminCheckInSummary> {
  const { data } = await apiClient.get<AdminCheckInSummaryApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/check-ins`,
    authorizationConfig('admin'),
  )
  return {
    totalGuests: data.total_guests,
    checkedInCount: data.checked_in_count,
    uncheckedCount: data.unchecked_count,
    records: data.records.map((record) => ({
      guestId: String(record.guest_id),
      guestName: record.guest_name,
      phone: record.phone,
      checkedInAt: record.checked_in_at,
      method: record.method,
      staffName: record.staff_name || '人工核验',
    })),
  }
}
