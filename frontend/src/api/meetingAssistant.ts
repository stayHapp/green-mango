/** 会议助手管理员配置与嘉宾公开内容 API。 */

import type { MeetingAssistantFeature, MeetingAssistantFeatureKey } from '../types'
import { apiClient, authorizationConfig } from './client'

interface MeetingAssistantFeatureApiResponse {
  meeting_id: number
  feature_key: MeetingAssistantFeatureKey
  content: string | null
  unpublished_message: string
  is_published: boolean
  updated_at?: string
}

export const meetingAssistantFeatureDefinitions: Array<Pick<MeetingAssistantFeature, 'key' | 'title' | 'description'>> = [
  { key: 'agenda', title: '会议日程', description: '查看会议流程和环节安排' },
  { key: 'manual', title: '会议资料', description: '查看参会须知和会务资料' },
  { key: 'weather', title: '天气提醒', description: '了解会场天气和出行提示' },
  { key: 'route', title: '路线导航', description: '查看会场位置和到场说明' },
  { key: 'contact', title: '联系会务', description: '联系会务组和现场支持' },
]

/**
 * 将历史会议手册默认提醒转换为当前“会议资料”产品文案。
 *
 * 入参：key 为固定会议服务标识；message 为后端返回的未发布提醒，均必填。
 * 返回值：string：仅在提醒以历史“会议手册”名称开头时替换产品名称，其他管理员自定义内容保持原样。
 * 异常：当前函数不主动抛出异常。
 */
function normalizeUnpublishedMessage(key: MeetingAssistantFeatureKey, message: string): string {
  const normalizedMessage = message.trim()
  if (key === 'manual' && normalizedMessage.startsWith('会议手册')) {
    return normalizedMessage.replace(/^会议手册(?:尚未发布)?/, '会议资料正在准备中')
  }
  return normalizedMessage
}

/**
 * 判断路由字符串是否为受支持的会议助手功能标识。
 *
 * 入参：value 为待校验字符串，必填。
 * 返回值：value is MeetingAssistantFeatureKey：为五项固定标识之一时返回 true。
 * 异常：当前函数不主动抛出异常。
 */
export function isMeetingAssistantFeatureKey(value: string): value is MeetingAssistantFeatureKey {
  return meetingAssistantFeatureDefinitions.some((definition) => definition.key === value)
}

/**
 * 把后端配置响应转换为包含前端入口文案的页面类型。
 *
 * 入参：response 为后端会议助手配置，必填。
 * 返回值：MeetingAssistantFeature：字段名和固定入口信息已转换的页面对象。
 * 异常：后端返回未知功能标识时抛出 Error，避免页面展示不受支持的入口。
 */
function mapMeetingAssistantFeature(response: MeetingAssistantFeatureApiResponse): MeetingAssistantFeature {
  const definition = meetingAssistantFeatureDefinitions.find((item) => item.key === response.feature_key)
  if (!definition) {
    throw new Error('后端返回了不受支持的会议助手功能。')
  }
  return {
    meetingId: String(response.meeting_id),
    ...definition,
    content: response.content ?? '',
    unpublishedMessage: normalizeUnpublishedMessage(response.feature_key, response.unpublished_message),
    isPublished: response.is_published,
  }
}

/**
 * 获取管理员有权访问会议的五项完整配置。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<MeetingAssistantFeature[]>：包含草稿正文的固定五项配置。
 * 异常：登录过期、会议未授权、网络失败或响应异常时抛出异常。
 */
export async function listAdminMeetingAssistantFeatures(meetingId: string): Promise<MeetingAssistantFeature[]> {
  const { data } = await apiClient.get<MeetingAssistantFeatureApiResponse[]>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/assistant-features`,
    authorizationConfig('admin'),
  )
  return data.map(mapMeetingAssistantFeature)
}

/**
 * 保存管理员编辑的单项会议助手配置。
 *
 * 入参：meetingId 为会议 ID；key 为固定功能标识；input 为正文、提醒和发布状态，均必填。
 * 返回值：Promise<MeetingAssistantFeature>：后端保存并转换后的完整配置。
 * 异常：字段超限、会议未授权、登录过期或网络失败时抛出异常。
 */
export async function updateAdminMeetingAssistantFeature(
  meetingId: string,
  key: MeetingAssistantFeatureKey,
  input: Pick<MeetingAssistantFeature, 'content' | 'unpublishedMessage' | 'isPublished'>,
): Promise<MeetingAssistantFeature> {
  const { data } = await apiClient.patch<MeetingAssistantFeatureApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/assistant-features/${key}`,
    {
      content: input.content,
      unpublished_message: input.unpublishedMessage,
      is_published: input.isPublished,
    },
    authorizationConfig('admin'),
  )
  return mapMeetingAssistantFeature(data)
}

/**
 * 获取当前嘉宾所属会议的单项公开配置。
 *
 * 入参：meetingId 为会议 ID；key 为固定功能标识，均必填。
 * 返回值：Promise<MeetingAssistantFeature>：已发布正文或正文为空的未发布提醒配置。
 * 异常：嘉宾未登录、跨会议访问、功能不存在或网络失败时抛出异常。
 */
export async function getGuestMeetingAssistantFeature(
  meetingId: string,
  key: MeetingAssistantFeatureKey,
): Promise<MeetingAssistantFeature> {
  const { data } = await apiClient.get<MeetingAssistantFeatureApiResponse>(
    `/guest/meetings/${encodeURIComponent(meetingId)}/assistant-features/${key}`,
    authorizationConfig('guest'),
  )
  return mapMeetingAssistantFeature(data)
}
