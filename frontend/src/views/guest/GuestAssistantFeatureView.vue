<template>
  <section class="assistant-page">
    <header class="assistant-page__header">
      <button type="button" class="assistant-page__back" aria-label="返回" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </button>
    </header>

    <main class="assistant-page__body">
      <h1 class="assistant-page__title">{{ feature?.title ?? '会议服务' }}</h1>
      <el-skeleton v-if="loading" :rows="6" animated />
      <el-alert v-else-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
      <el-alert v-else-if="feature && !feature.isPublished" type="info" :closable="false" :title="feature.unpublishedMessage" />

      <template v-else-if="feature?.key === 'agenda'">
        <div class="assistant-agenda-list">
          <template v-for="item in agendaItems" :key="item.id">
            <h2 v-if="item.kind === 'date'" class="assistant-agenda-date">{{ item.title }}</h2>
            <article v-else class="assistant-agenda-card">
              <div class="assistant-agenda-card__time">
                <el-icon><Clock /></el-icon>
                <strong>{{ item.time || '时间待定' }}</strong>
              </div>
              <div class="assistant-agenda-card__content">
                <h2>{{ item.title }}</h2>
                <p v-if="item.speaker">
                  <el-icon><User /></el-icon>
                  {{ item.speaker }}
                </p>
                <p v-if="item.location">
                  <el-icon><LocationIcon /></el-icon>
                  {{ item.location }}
                </p>
              </div>
            </article>
          </template>
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
            <span class="weather-forecast-item__rain">💧{{ item.precipitation }}mm</span>
            <span class="weather-forecast-item__temperature"><strong>{{ item.high }}°</strong><em>{{ item.low }}°</em></span>
          </article>
        </section>

        <a class="weather-source" :href="weather.sourceUrl" target="_blank" rel="noopener noreferrer">天气数据由 {{ weather.sourceName }} 提供</a>
        </template>

        <p v-if="feature.content.trim()" class="weather-supplement">{{ feature.content }}</p>
      </template>

      <template v-else-if="feature?.key === 'route'">
        <section class="route-navigation-card">
          <div class="route-navigation-card__icon"><el-icon><LocationIcon /></el-icon></div>
          <div>
            <h2>{{ meeting?.navigationName || meeting?.location || '会议地点' }}</h2>
            <p>{{ meeting?.navigationAddress || meeting?.location || '管理员尚未补充会议地址。' }}</p>
          </div>
          <a
            v-if="navigationUrl"
            class="route-navigation-button"
            :href="navigationUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            打开地图导航
          </a>
          <el-alert v-else type="warning" :closable="false" title="管理员尚未选择准确的导航位置。" />
        </section>

        <section class="route-arrival-guide">
          <h2>到场说明</h2>
          <article v-for="(block, index) in contentBlocks" :key="`route-${index}`" class="assistant-content-card">{{ block }}</article>
        </section>
      </template>

      <div v-else-if="feature" class="assistant-content-cards">
        <article v-for="(block, index) in contentBlocks" :key="`${feature.key}-${index}`" class="assistant-content-card">{{ block }}</article>
      </div>
    </main>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft, Clock, Location as LocationIcon, User } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getPublicMeeting } from '../../api/sessions'
import { getGuestMeetingAssistantFeature, isMeetingAssistantFeatureKey } from '../../api/meetingAssistant'
import { getGuestMeetingWeather, type MeetingWeather } from '../../api/meetingWeather'
import type { Meeting, MeetingAssistantFeature } from '../../types'

interface AgendaDisplayItem {
  id: string
  kind: 'date' | 'entry'
  time: string
  title: string
  speaker: string
  location: string
}

const route = useRoute()
const router = useRouter()
const meeting = ref<Meeting>()
const feature = ref<MeetingAssistantFeature>()
const weather = ref<MeetingWeather>()
const loading = ref(true)
const errorMessage = ref('')
const agendaItems = computed(buildAgendaItems)
const contentBlocks = computed(buildContentBlocks)
const navigationUrl = computed(buildNavigationUrl)

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
      errorMessage.value = '未找到对应的会议服务。'
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
    errorMessage.value = getApiErrorMessage(error, '会议服务加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

/**
 * 返回当前会议的嘉宾首页，并自动展开会议服务列表。
 *
 * 入参：无；函数读取当前路由中的会议 ID。
 * 返回值：Promise<void>：完成嘉宾首页跳转，并通过查询参数触发会议服务抽屉。
 * 异常：路由跳转失败时由 Vue Router 抛出异常。
 */
async function goBack(): Promise<void> {
  await router.push({
    path: `/guest/meetings/${String(route.params.id)}`,
    query: { services: 'open' },
  })
}

/**
 * 将管理员逐行编辑的日程正文转换为简洁日程卡片。
 *
 * 入参：无；函数读取当前已发布正文，支持日期行、时间段，以及用竖线分隔的标题、讲者和地点。
 * 返回值：AgendaDisplayItem[]：包含日期分组或时间、标题、可选讲者与地点的日程展示项。
 * 异常：正文为空时返回一条内容待补充提示。
 * 使用示例：`09:00-09:30 开幕致辞｜主办方代表｜峰会厅`。
 */
function buildAgendaItems(): AgendaDisplayItem[] {
  const lines = feature.value?.content.split('\n').map((line) => line.trim()).filter(Boolean) ?? []
  if (!lines.length) {
    return [{ id: 'empty', kind: 'entry', time: '', title: '日程内容待补充', speaker: '', location: '' }]
  }
  return lines.map((line, index) => {
    const isDateLine = /^(?:\d{4}\s*[年./-]\s*)?\d{1,2}\s*[月./-]\s*\d{1,2}\s*日?$/.test(line)
    if (isDateLine) {
      return { id: `agenda-date-${index}`, kind: 'date', time: '', title: line, speaker: '', location: '' }
    }

    const match = line.match(/^(\d{1,2}:\d{2}(?:\s*[-–—]\s*\d{1,2}:\d{2})?)\s*(.*)$/)
    // 竖线后的两段分别作为讲者和地点；缺失字段不在页面占位。
    const contentParts = (match?.[2] || line).split(/\s*[|｜]\s*/).map((part) => part.trim()).filter(Boolean)
    return {
      id: `agenda-${index}`,
      kind: 'entry',
      time: match?.[1] ?? '',
      title: contentParts[0] || line,
      speaker: contentParts[1] || '',
      location: contentParts[2] || '',
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
 * 根据管理员确认的高德坐标生成手机导航链接。
 *
 * 入参：无；函数读取会议导航名称、经度和纬度。
 * 返回值：string：可调起高德地图或打开高德 H5 的 URI；坐标缺失时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function buildNavigationUrl(): string {
  const longitude = meeting.value?.navigationLongitude
  const latitude = meeting.value?.navigationLatitude
  if (longitude === undefined || latitude === undefined) {
    return ''
  }
  const params = new URLSearchParams({
    from: '',
    to: `${longitude},${latitude},${meeting.value?.navigationName || meeting.value?.location || '会议地点'}`,
    mode: 'car',
    policy: '0',
    src: 'zhihui',
    callnative: '1',
  })
  return `https://uri.amap.com/navigation?${params.toString()}`
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
