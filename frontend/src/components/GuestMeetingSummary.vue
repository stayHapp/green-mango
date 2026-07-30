<template>
  <section
    class="guest-home-summary"
    :class="{ 'is-compact': compact, 'has-description': showDescription && meeting.description }"
    aria-labelledby="guest-meeting-title"
  >
    <div v-if="!compact" class="guest-home-summary__brand" aria-label="知会">
      <span>知</span>
      <small>知 会</small>
    </div>
    <h1 id="guest-meeting-title">{{ meeting.title }}</h1>
    <p v-if="showDescription && meeting.description" class="guest-home-summary__description">
      {{ meeting.description }}
    </p>
    <div class="guest-home-summary__meta">
      <div>
        <el-icon><Calendar /></el-icon>
        <strong>{{ formatMeetingRange(meeting.startTime, meeting.endTime, meeting.timeDisplayMode) }}</strong>
      </div>
      <div>
        <el-icon><Location /></el-icon>
        <strong>{{ meeting.location || '待会务确认' }}</strong>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Calendar, Location } from '@element-plus/icons-vue'

import type { Meeting, MeetingTimeDisplayMode } from '../types'

withDefaults(defineProps<{ meeting: Meeting; compact?: boolean; showDescription?: boolean }>(), {
  compact: false,
  showDescription: false,
})

/**
 * 将会议起止日期格式化为正式中文范围，并按会议配置展示到上午/下午或具体时间。
 *
 * 入参：startTime 为开始时间，endTime 为结束时间，均允许为空；mode 为会议首页时间显示方式，必填。
 * 返回值：string：完整中文日期范围；缺失或非法时返回“待会务确认”。
 * 异常：当前函数不主动抛出异常。
 */
function formatMeetingRange(startTime: string, endTime: string, mode: MeetingTimeDisplayMode): string {
  const startDate = startTime ? new Date(startTime) : undefined
  const endDate = endTime ? new Date(endTime) : undefined
  const start = formatDate(startTime, true, mode)
  const shouldShowEndYear = Boolean(
    endDate &&
      !Number.isNaN(endDate.getTime()) &&
      (!startDate || Number.isNaN(startDate.getTime()) || startDate.getFullYear() !== endDate.getFullYear()),
  )
  const end = formatDate(endTime, shouldShowEndYear, mode)

  if (!start && !end) return '待会务确认'
  if (!start) return end
  if (!end) return start
  return `${start}—${end}`
}

/**
 * 将单个会议时间按配置格式化为中文日期文本。
 *
 * 入参：value 为 ISO 日期时间字符串，允许为空；includeYear 控制是否展示年份；mode 为会议首页时间显示方式，均必填。
 * 返回值：string：有效日期返回中文日期文本，空值或非法日期返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatDate(value: string, includeYear: boolean, mode: MeetingTimeDisplayMode): string {
  if (!value) return ''

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  if (mode === 'time') {
    return date.toLocaleString('zh-CN', {
      ...(includeYear ? { year: 'numeric' as const } : {}),
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  }

  const dateText = date.toLocaleDateString('zh-CN', {
    ...(includeYear ? { year: 'numeric' as const } : {}),
    month: 'long',
    day: 'numeric',
  })
  return `${dateText} ${formatDayPeriod(date)}`
}

/**
 * 根据小时判断会议日期所属的上下午时段。
 *
 * 入参：date 为有效 Date（日期）对象，必填。
 * 返回值：string：0 点到 11 点返回“上午”，12 点到 23 点返回“下午”。
 * 异常：当前函数不主动抛出异常。
 */
function formatDayPeriod(date: Date): string {
  return date.getHours() < 13 ? '上午' : '下午'
}
</script>
