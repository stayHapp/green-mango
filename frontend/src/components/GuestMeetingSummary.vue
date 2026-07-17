<template>
  <section class="guest-home-summary" aria-labelledby="guest-meeting-title">
    <h1 id="guest-meeting-title">{{ meeting.title }}</h1>
    <div class="guest-home-summary__meta">
      <div>
        <el-icon><Calendar /></el-icon>
        <strong>{{ formatMeetingRange(meeting.startTime, meeting.endTime) }}</strong>
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

import type { Meeting } from '../types'

defineProps<{ meeting: Meeting }>()

/**
 * 将会议起止时间格式化为正式中文范围。
 *
 * 入参：startTime 为开始时间，endTime 为结束时间；均允许为空。
 * 返回值：string：完整中文时间范围；缺失或非法时返回“待会务确认”。
 * 异常：当前函数不主动抛出异常。
 */
function formatMeetingRange(startTime: string, endTime: string): string {
  const startDate = startTime ? new Date(startTime) : undefined
  const endDate = endTime ? new Date(endTime) : undefined
  const start = formatDate(startTime, true)
  const shouldShowEndYear = Boolean(
    endDate &&
      !Number.isNaN(endDate.getTime()) &&
      (!startDate || Number.isNaN(startDate.getTime()) || startDate.getFullYear() !== endDate.getFullYear()),
  )
  const end = formatDate(endTime, shouldShowEndYear)

  if (!start && !end) return '待会务确认'
  if (!start) return end
  if (!end) return start
  return `${start}—${end}`
}

/**
 * 将单个会议时间格式化为中文月日和时分。
 *
 * 入参：value 为 ISO 日期时间字符串，允许为空；includeYear 控制是否展示年份，必填。
 * 返回值：string：有效日期的中文文本，空值或非法日期返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatDate(value: string, includeYear: boolean): string {
  if (!value) return ''

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  return date.toLocaleString('zh-CN', {
    ...(includeYear ? { year: 'numeric' as const } : {}),
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}
</script>
