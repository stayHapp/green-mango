/** 嘉宾会议列表与详情 API。 */

import type { Meeting, MeetingStatus } from '../types'
import { apiClient, authorizationConfig } from './client'

interface GuestMeetingApiResponse {
  id: number
  title: string
  description: string | null
  location: string | null
  navigation_name: string | null
  navigation_address: string | null
  navigation_longitude: number | null
  navigation_latitude: number | null
  start_time: string | null
  end_time: string | null
  status: MeetingStatus
}

/**
 * 将后端嘉宾会议响应转换为页面共享会议类型。
 *
 * 入参：meeting 为 FastAPI 返回的嘉宾会议对象，必填。
 * 返回值：Meeting：空值已转换为空字符串，管理与工作人员授权字段为空数组。
 * 异常：当前函数不主动抛出异常；响应结构异常由请求调用方处理。
 */
function mapGuestMeeting(meeting: GuestMeetingApiResponse): Meeting {
  return {
    id: String(meeting.id),
    title: meeting.title,
    description: meeting.description || '',
    location: meeting.location || '',
    navigationName: meeting.navigation_name || '',
    navigationAddress: meeting.navigation_address || '',
    navigationLongitude: meeting.navigation_longitude ?? undefined,
    navigationLatitude: meeting.navigation_latitude ?? undefined,
    startTime: meeting.start_time || '',
    endTime: meeting.end_time || '',
    status: meeting.status,
    adminIds: [],
    staffIds: [],
  }
}

/**
 * 查询当前已登录嘉宾可访问的会议。
 *
 * 入参：无；嘉宾 token 从本地 API 会话读取。
 * 返回值：Promise<Meeting[]>：按后端顺序返回转换后的会议列表。
 * 异常：未登录、会话失效或网络失败时抛出异常，由页面展示。
 */
export async function listGuestMeetings(): Promise<Meeting[]> {
  const { data } = await apiClient.get<GuestMeetingApiResponse[]>('/guest/meetings', authorizationConfig('guest'))
  return data.map(mapGuestMeeting)
}

/**
 * 查询当前嘉宾所属会议详情。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<Meeting>：转换后的会议详情。
 * 异常：跨会议访问、会话失效、会议不存在或网络失败时抛出异常。
 */
export async function getGuestMeeting(meetingId: string): Promise<Meeting> {
  const { data } = await apiClient.get<GuestMeetingApiResponse>(
    `/guest/meetings/${encodeURIComponent(meetingId)}`,
    authorizationConfig('guest'),
  )
  return mapGuestMeeting(data)
}
