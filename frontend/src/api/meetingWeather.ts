/** 嘉宾会议天气 API。 */

import { apiClient, authorizationConfig } from './client'

export interface MeetingCurrentWeather {
  observedAt: string
  temperature: number
  condition: string
  iconCode: string
  humidity: number
  windSpeed: number
}

export interface MeetingDailyWeather {
  date: string
  condition: string
  iconCode: string
  precipitation: number
  high: number
  low: number
}

export interface MeetingWeather {
  available: boolean
  locationName: string
  message: string
  sourceName: string
  sourceUrl: string
  current?: MeetingCurrentWeather
  daily: MeetingDailyWeather[]
}

interface MeetingWeatherApiResponse {
  available: boolean
  location_name: string
  message: string
  source_name: string
  source_url: string
  current: null | {
    observed_at: string
    temperature: number
    condition: string
    icon_code: string
    humidity: number
    wind_speed: number
  }
  daily: Array<{
    date: string
    condition: string
    icon_code: string
    precipitation: number
    high: number
    low: number
  }>
}

/**
 * 获取当前嘉宾会议的和风天气实况与七日预报。
 *
 * 入参：meetingId 为数字会议 ID 的字符串形式，必填。
 * 返回值：Promise<MeetingWeather>：转换后的天气、地点、来源和降级提示。
 * 异常：嘉宾未登录、跨会议访问、天气未发布或网络失败时抛出异常。
 */
export async function getGuestMeetingWeather(meetingId: string): Promise<MeetingWeather> {
  const { data } = await apiClient.get<MeetingWeatherApiResponse>(
    `/guest/meetings/${encodeURIComponent(meetingId)}/weather`,
    authorizationConfig('guest'),
  )
  return {
    available: data.available,
    locationName: data.location_name,
    message: data.message,
    sourceName: data.source_name,
    sourceUrl: data.source_url,
    current: data.current
      ? {
          observedAt: data.current.observed_at,
          temperature: data.current.temperature,
          condition: data.current.condition,
          iconCode: data.current.icon_code,
          humidity: data.current.humidity,
          windSpeed: data.current.wind_speed,
        }
      : undefined,
    daily: data.daily.map((item) => ({
      date: item.date,
      condition: item.condition,
      iconCode: item.icon_code,
      precipitation: item.precipitation,
      high: item.high,
      low: item.low,
    })),
  }
}
