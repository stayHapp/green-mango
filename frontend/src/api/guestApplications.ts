/** 嘉宾公开报名 API。 */

import type { GuestApplicationInput, GuestApplicationResult } from '../types'
import { apiClient } from './client'

interface GuestApplicationApiResponse {
  id: number
  meeting_id: number
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}

/**
 * 向指定会议提交一条公开嘉宾报名申请。
 *
 * 入参：meetingId 为后端数字会议 ID 的字符串形式；input 为姓名、手机号及可选单位和职务，均必填。
 * 返回值：Promise<GuestApplicationResult>：包含申请 ID、会议 ID、审核状态和提交时间。
 * 异常：会议未开放报名、重复待审核申请、字段校验失败或网络异常时抛出异常。
 */
export async function submitGuestApplication(
  meetingId: string,
  input: GuestApplicationInput,
): Promise<GuestApplicationResult> {
  const { data } = await apiClient.post<GuestApplicationApiResponse>(
    `/meetings/${encodeURIComponent(meetingId)}/guest-applications`,
    {
      name: input.name,
      phone: input.phone,
      organization: input.organization || null,
      title: input.title || null,
      values: {},
    },
  )
  return {
    id: String(data.id),
    meetingId: String(data.meeting_id),
    status: data.status,
    createdAt: data.created_at,
  }
}
