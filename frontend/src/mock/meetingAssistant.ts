/** 会议助手管理员配置与嘉宾展示的前端 Mock 数据服务。 */

import type { MeetingAssistantFeature, MeetingAssistantFeatureKey } from '../types'

export const meetingAssistantFeatureDefinitions: Array<Pick<MeetingAssistantFeature, 'key' | 'title' | 'description'>> = [
  { key: 'agenda', title: '会议日程', description: '查看当天流程和环节安排' },
  { key: 'manual', title: '会议手册', description: '查看会务资料和注意事项' },
  { key: 'weather', title: '天气情况', description: '了解到场当天城市天气' },
  { key: 'route', title: '路线指引', description: '查看会场位置和交通建议' },
  { key: 'contact', title: '联系我们', description: '联系会务组和现场支持' },
]

const STORAGE_KEY = 'green-mango-meeting-assistant-mock'

/**
 * 从浏览器本地存储读取全部会议助手 Mock 配置。
 *
 * 入参：无。
 * 返回值：Record<string, MeetingAssistantFeature[]>：以会议 ID 为键的配置集合。
 * 异常：存储内容损坏时清除旧值并返回空集合，不向页面抛出异常。
 */
function readFeatureStore(): Record<string, MeetingAssistantFeature[]> {
  const storedValue = window.localStorage.getItem(STORAGE_KEY)
  if (!storedValue) {
    return {}
  }
  try {
    return JSON.parse(storedValue) as Record<string, MeetingAssistantFeature[]>
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
    return {}
  }
}

/**
 * 将全部会议助手 Mock 配置写入浏览器本地存储。
 *
 * 入参：store 为以会议 ID 为键的完整配置集合，必填。
 * 返回值：void：序列化并覆盖当前 Mock 存储。
 * 异常：浏览器禁用本地存储或容量不足时由浏览器抛出异常。
 */
function writeFeatureStore(store: Record<string, MeetingAssistantFeature[]>): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
}

/**
 * 模拟会议助手请求的短暂网络延迟。
 *
 * 入参：value 为待返回值，必填。
 * 返回值：Promise<T>：延迟 120 毫秒后返回原值。
 * 异常：当前函数不主动抛出异常。
 */
function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => window.setTimeout(() => resolve(value), 120))
}

/**
 * 为指定会议创建可重复编辑的五项默认会议助手配置。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：MeetingAssistantFeature[]：五项功能的独立配置副本。
 * 异常：当前函数不主动抛出异常。
 */
function createDefaultFeatures(meetingId: string): MeetingAssistantFeature[] {
  return meetingAssistantFeatureDefinitions.map((definition, index) => ({
    meetingId,
    ...definition,
    content: index === 0 ? '会议日程正在整理中，发布后将在这里展示完整安排。' : '',
    unpublishedMessage: `${definition.title}尚未发布，请稍后查看。`,
    isPublished: false,
  }))
}

/**
 * 获取指定会议的会议助手配置，首次读取时自动初始化默认数据。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：MeetingAssistantFeature[]：当前会议五项功能配置。
 * 异常：当前函数不主动抛出异常。
 */
function getOrCreateFeatures(meetingId: string): MeetingAssistantFeature[] {
  const store = readFeatureStore()
  const existingFeatures = store[meetingId]
  if (existingFeatures) {
    return existingFeatures
  }
  const createdFeatures = createDefaultFeatures(meetingId)
  store[meetingId] = createdFeatures
  writeFeatureStore(store)
  return createdFeatures
}

/**
 * 查询会议助手五项功能配置。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<MeetingAssistantFeature[]>：返回配置副本，避免页面直接修改 Mock 存储。
 * 异常：当前函数不主动抛出异常。
 */
export function listMeetingAssistantFeatures(meetingId: string): Promise<MeetingAssistantFeature[]> {
  return delay(getOrCreateFeatures(meetingId).map((feature) => ({ ...feature })))
}

/**
 * 保存单项会议助手功能的正文、未发布提醒和发布状态。
 *
 * 入参：meetingId 为会议 ID；key 为功能标识；input 为待保存字段，均必填。
 * 返回值：Promise<MeetingAssistantFeature | undefined>：保存后的配置；功能不存在时返回 undefined。
 * 异常：当前 Mock 不主动抛出异常；真实 API 阶段应校验管理员权限和字段长度。
 */
export function updateMeetingAssistantFeature(
  meetingId: string,
  key: MeetingAssistantFeatureKey,
  input: Pick<MeetingAssistantFeature, 'content' | 'unpublishedMessage' | 'isPublished'>,
): Promise<MeetingAssistantFeature | undefined> {
  const store = readFeatureStore()
  const meetingFeatures = store[meetingId] ?? createDefaultFeatures(meetingId)
  const feature = meetingFeatures.find((item) => item.key === key)
  if (!feature) {
    return delay(undefined)
  }
  Object.assign(feature, input)
  store[meetingId] = meetingFeatures
  writeFeatureStore(store)
  return delay({ ...feature })
}
