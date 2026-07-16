<template>
  <section class="assistant-page">
    <header class="assistant-page__header">
      <el-button :icon="ArrowLeft" circle aria-label="返回" title="返回" @click="goBack" />
      <h1>{{ feature?.title ?? '会议功能' }}</h1>
      <span class="assistant-page__header-space" />
    </header>

    <main class="assistant-page__body">
      <el-skeleton v-if="loading" :rows="6" animated />
      <el-alert v-else-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
      <el-alert v-else-if="feature && !feature.isPublished" type="info" :closable="false" :title="feature.unpublishedMessage" />

      <template v-else-if="feature?.key === 'agenda'">
        <div class="assistant-date-badge">{{ meetingDate }}</div>
        <div class="assistant-timeline">
          <article v-for="item in agendaItems" :key="item.id" class="assistant-timeline-card">
            <div v-if="item.time" class="assistant-timeline-card__time">{{ item.time }}</div>
            <h2>{{ item.title }}</h2>
            <p v-if="item.detail">{{ item.detail }}</p>
          </article>
        </div>
      </template>

      <template v-else-if="feature?.key === 'weather'">
        <el-alert v-if="!weather?.available || !weather.current" type="warning" :closable="false" :title="weather?.message || '天气数据暂时不可用。'" />
        <template v-else>
        <section class="weather-current-card">
          <p class="weather-location"><el-icon><LocationIcon /></el-icon>{{ weather.locationName }}</p>
          <div class="weather-current-card__main">
            <span class="weather-current-card__icon">{{ weatherIcon(weather.current.iconCode) }}</span>
            <div>
              <div class="weather-current-card__temperature">{{ weather.current.temperature }}<small>°C</small></div>
              <strong>{{ weather.current.condition }}</strong>
            </div>
          </div>
          <div class="weather-current-card__meta">
            <span>💧 湿度 {{ weather.current.humidity }}%</span>
            <span>🌬 风速 {{ weather.current.windSpeed }} km/h</span>
          </div>
        </section>

        <el-alert
          class="weather-location-alert"
          type="warning"
          :closable="false"
          :title="weather.message"
        />

        <section class="weather-forecast-card">
          <h2><span />近期预报</h2>
          <article v-for="item in weather.daily" :key="item.date" class="weather-forecast-item">
            <span class="weather-forecast-item__date">{{ formatForecastDate(item.date) }}</span>
            <span class="weather-forecast-item__icon">{{ weatherIcon(item.iconCode) }}</span>
            <span class="weather-forecast-item__condition">{{ item.condition }}</span>
            <span class="weather-forecast-item__rain">💧 {{ item.precipitation }} mm</span>
            <span class="weather-forecast-item__temperature"><strong>{{ item.high }}°</strong><em>{{ item.low }}°</em></span>
          </article>
        </section>

        <a class="weather-source" :href="weather.sourceUrl" target="_blank" rel="noopener noreferrer">天气数据由 {{ weather.sourceName }} 提供</a>
        </template>

        <p v-if="feature.content.trim()" class="weather-supplement">{{ feature.content }}</p>
      </template>

      <div v-else-if="feature" class="assistant-content-cards">
        <article v-for="(block, index) in contentBlocks" :key="`${feature.key}-${index}`" class="assistant-content-card">{{ block }}</article>
      </div>
    </main>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft, Location as LocationIcon } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getPublicMeeting } from '../../api/sessions'
import { getGuestMeetingAssistantFeature, isMeetingAssistantFeatureKey } from '../../api/meetingAssistant'
import { getGuestMeetingWeather, type MeetingWeather } from '../../api/meetingWeather'
import type { Meeting, MeetingAssistantFeature } from '../../types'

interface AgendaDisplayItem {
  id: string
  time: string
  title: string
  detail: string
}

const route = useRoute()
const router = useRouter()
const meeting = ref<Meeting>()
const feature = ref<MeetingAssistantFeature>()
const weather = ref<MeetingWeather>()
const loading = ref(true)
const errorMessage = ref('')
const meetingDate = computed(formatMeetingDate)
const agendaItems = computed(buildAgendaItems)
const contentBlocks = computed(buildContentBlocks)

/**
 * 加载会议基础信息和当前会议助手功能配置。
 *
 * 入参：无；函数读取路由中的会议 ID 和功能标识。
 * 返回值：Promise<void>：完成后更新会议、功能配置和页面状态。
 * 异常：会议或功能不存在、网络失败时转换为页面错误提示。
 */
async function loadFeature(): Promise<void> {
  const meetingId = String(route.params.id)
  const featureKey = String(route.params.featureKey)
  loading.value = true
  errorMessage.value = ''
  try {
    if (!isMeetingAssistantFeatureKey(featureKey)) {
      errorMessage.value = '未找到对应的会议功能。'
      return
    }
    const [meetingData, featureData] = await Promise.all([
      getPublicMeeting(meetingId),
      getGuestMeetingAssistantFeature(meetingId, featureKey),
    ])
    meeting.value = meetingData
    feature.value = featureData
    if (featureKey === 'weather' && featureData.isPublished) {
      weather.value = await getGuestMeetingWeather(meetingId)
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '会议功能加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

/**
 * 返回进入当前功能页之前的嘉宾页面。
 *
 * 入参：无。
 * 返回值：void：触发浏览器历史返回。
 * 异常：当前函数不主动抛出异常。
 */
function goBack(): void {
  router.back()
}

/**
 * 将会议开始日期格式化为日程页日期标签。
 *
 * 入参：无；函数读取已加载会议开始时间。
 * 返回值：string：形如 2026-07-18 的日期；会议未加载时返回“会议日程”。
 * 异常：非法日期会返回“会议日程”。
 */
function formatMeetingDate(): string {
  if (!meeting.value?.startTime) {
    return '会议日程'
  }
  const date = new Date(meeting.value.startTime)
  if (Number.isNaN(date.getTime())) {
    return '会议日程'
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * 将管理员逐行编辑的日程正文转换为时间线卡片。
 *
 * 入参：无；函数读取当前已发布正文，每个非空行生成一张卡片。
 * 返回值：AgendaDisplayItem[]：包含时间、标题和可选说明的日程展示项。
 * 异常：正文为空时返回一条内容待补充提示。
 */
function buildAgendaItems(): AgendaDisplayItem[] {
  const lines = feature.value?.content.split('\n').map((line) => line.trim()).filter(Boolean) ?? []
  if (!lines.length) {
    return [{ id: 'empty', time: '', title: '日程内容待补充', detail: '' }]
  }
  return lines.map((line, index) => {
    const match = line.match(/^(\d{1,2}:\d{2}(?:\s*[-–—]\s*\d{1,2}:\d{2})?)\s*(.*)$/)
    return {
      id: `agenda-${index}`,
      time: match?.[1] ?? '',
      title: match?.[2] || line,
      detail: '',
    }
  })
}

/**
 * 将其他会议助手功能的正文按空行分隔为内容卡片。
 *
 * 入参：无；函数读取当前功能正文。
 * 返回值：string[]：清理空白后的内容区块；正文为空时返回占位提示。
 * 异常：当前函数不主动抛出异常。
 */
function buildContentBlocks(): string[] {
  const blocks = feature.value?.content.split(/\n\s*\n/).map((block) => block.trim()).filter(Boolean) ?? []
  return blocks.length ? blocks : ['内容待补充。']
}

/**
 * 将和风天气图标代码转换为当前页面使用的简洁天气符号。
 *
 * 入参：iconCode 为和风天气图标代码，必填。
 * 返回值：string：晴、云、雨、雪、雷或雾对应的 Emoji（表情符号）。
 * 异常：未知代码返回通用多云图标，不向页面抛出异常。
 */
function weatherIcon(iconCode: string): string {
  const code = Number(iconCode)
  if (code === 100 || code === 150) return '☀️'
  if (code >= 101 && code <= 104) return '⛅'
  if (code >= 300 && code <= 399) return code >= 302 && code <= 304 ? '⛈️' : '🌧️'
  if (code >= 400 && code <= 499) return '🌨️'
  if (code >= 500 && code <= 515) return '🌫️'
  return '☁️'
}

/**
 * 将供应商 ISO 日期格式化为中文月日与星期。
 *
 * 入参：value 为 `yyyy-MM-dd` 日期文本，必填。
 * 返回值：string：形如“7月16日 周四”的本地日期文本。
 * 异常：日期无效时返回原始文本。
 */
function formatForecastDate(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdayNames[date.getDay()]}`
}

onMounted(loadFeature)
</script>
