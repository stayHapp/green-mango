/** 管理员会议列表、创建、详情和修改 API。 */

import type { Meeting, MeetingStatus } from '../types'
import { apiClient, authorizationConfig } from './client'

interface MeetingApiResponse {
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
  created_by_id: number
  created_at: string
  updated_at: string
}

export interface MeetingWriteInput {
  title: string
  description: string
  location: string
  navigationName: string
  navigationAddress: string
  navigationLongitude?: number
  navigationLatitude?: number
  startTime: string
  endTime: string
  status: MeetingStatus
}

/**
 * 将后端 snake_case（蛇形命名）会议响应转换为现有页面类型。
 *
 * 入参：meeting 为 FastAPI 返回的会议对象，必填。
 * 返回值：Meeting：字段名和空值已适配现有 Vue 页面。
 * 异常：当前函数不主动抛出异常；响应结构错误由 TypeScript 开发期约束和页面运行错误暴露。
 */
function mapMeeting(meeting: MeetingApiResponse): Meeting {
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
    adminIds: [String(meeting.created_by_id)],
    staffIds: [],
  }
}

/**
 * 将页面会议编辑数据转换为后端请求体。
 *
 * 入参：input 为页面使用的驼峰字段和可为空时间字符串，必填。
 * 返回值：对象：符合 FastAPI MeetingCreate/MeetingUpdate schema 的请求数据。
 * 异常：当前函数不主动抛出异常；时间格式与范围由后端最终校验。
 */
function meetingPayload(input: MeetingWriteInput) {
  return {
    title: input.title,
    description: input.description || null,
    location: input.location || null,
    navigation_name: input.navigationName || null,
    navigation_address: input.navigationAddress || null,
    navigation_longitude: input.navigationLongitude ?? null,
    navigation_latitude: input.navigationLatitude ?? null,
    start_time: input.startTime || null,
    end_time: input.endTime || null,
    status: input.status,
  }
}

export interface MeetingLocationOption {
  poiId: string
  name: string
  address: string
  district: string
  longitude: number
  latitude: number
}

interface MeetingLocationOptionApiResponse {
  poi_id: string
  name: string
  address: string
  district: string
  longitude: number
  latitude: number
}

/**
 * 搜索当前会议可选择的高德导航地点。
 *
 * 入参：meetingId 为会议 ID；query 为至少两个字符的地点关键词；city 为可选城市范围。
 * 返回值：Promise<MeetingLocationOption[]>：最多十条地点名称、地址和坐标。
 * 异常：高德未配置、会议未授权、关键词无效或网络失败时抛出异常。
 */
export async function searchMeetingLocationOptions(
  meetingId: string,
  query: string,
  city = '',
): Promise<MeetingLocationOption[]> {
  const { data } = await apiClient.get<MeetingLocationOptionApiResponse[]>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/location-options`,
    authorizationConfig('admin', { params: { query, city } }),
  )
  return data.map((item) => ({
    poiId: item.poi_id,
    name: item.name,
    address: item.address,
    district: item.district,
    longitude: item.longitude,
    latitude: item.latitude,
  }))
}

/**
 * 查询当前管理员被授权管理的全部会议。
 *
 * 入参：无；管理员 token 从本地 API 会话读取。
 * 返回值：Promise<Meeting[]>：按后端顺序返回并转换后的会议列表。
 * 异常：登录过期、无权限或网络异常时抛出异常，由页面展示。
 */
export async function listAdminMeetings(): Promise<Meeting[]> {
  const { data } = await apiClient.get<MeetingApiResponse[]>('/admin/meetings', authorizationConfig('admin'))
  return data.map(mapMeeting)
}

/**
 * 创建会议并自动获得创建人管理员授权。
 *
 * 入参：input 为已完成页面必填校验的会议数据，必填。
 * 返回值：Promise<Meeting>：后端创建并转换后的会议。
 * 异常：字段、时间、身份或网络无效时抛出异常，由页面展示。
 */
export async function createAdminMeeting(input: MeetingWriteInput): Promise<Meeting> {
  const { data } = await apiClient.post<MeetingApiResponse>(
    '/admin/meetings',
    meetingPayload(input),
    authorizationConfig('admin'),
  )
  return mapMeeting(data)
}

/**
 * 获取当前管理员有权限访问的会议详情。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<Meeting>：转换后的会议详情。
 * 异常：会议不存在、未授权、登录失效或网络失败时抛出异常。
 */
export async function getAdminMeeting(meetingId: string): Promise<Meeting> {
  const { data } = await apiClient.get<MeetingApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}`,
    authorizationConfig('admin'),
  )
  return mapMeeting(data)
}

/**
 * 修改管理员有权限管理的会议基础信息。
 *
 * 入参：meetingId 为会议 ID；input 为保存后的完整页面字段，均必填。
 * 返回值：Promise<Meeting>：后端校验并保存后的会议详情。
 * 异常：时间范围、字段、权限、登录或网络无效时抛出异常。
 */
export async function updateAdminMeeting(meetingId: string, input: MeetingWriteInput): Promise<Meeting> {
  const { data } = await apiClient.patch<MeetingApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}`,
    meetingPayload(input),
    authorizationConfig('admin'),
  )
  return mapMeeting(data)
}
