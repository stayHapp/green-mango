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
        <section class="weather-current-card">
          <p class="weather-location"><el-icon><LocationIcon /></el-icon>{{ weatherLocation.name }}</p>
          <div class="weather-current-card__main">
            <span class="weather-current-card__icon">{{ currentWeather.icon }}</span>
            <div>
              <div class="weather-current-card__temperature">{{ currentWeather.temperature }}<small>°C</small></div>
              <strong>{{ currentWeather.condition }}</strong>
            </div>
          </div>
          <div class="weather-current-card__meta">
            <span>💧 湿度 {{ currentWeather.humidity }}%</span>
            <span>🌬 风速 {{ currentWeather.windSpeed }} km/h</span>
          </div>
        </section>

        <el-alert
          class="weather-location-alert"
          type="warning"
          :closable="false"
          :title="weatherLocation.message"
        />

        <section class="weather-forecast-card">
          <h2><span />近期预报</h2>
          <article v-for="item in weatherForecast" :key="item.date" class="weather-forecast-item">
            <span class="weather-forecast-item__date">{{ item.date }}</span>
            <span class="weather-forecast-item__icon">{{ item.icon }}</span>
            <span class="weather-forecast-item__condition">{{ item.condition }}</span>
            <span class="weather-forecast-item__rain">💧 {{ item.rainProbability }}%</span>
            <span class="weather-forecast-item__temperature"><strong>{{ item.high }}°</strong><em>{{ item.low }}°</em></span>
          </article>
        </section>

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
import type { Meeting, MeetingAssistantFeature } from '../../types'

interface AgendaDisplayItem {
  id: string
  time: string
  title: string
  detail: string
}

interface WeatherLocationDisplay {
  name: string
  message: string
}

interface WeatherForecastItem {
  date: string
  icon: string
  condition: string
  rainProbability: number
  high: number
  low: number
}

const route = useRoute()
const router = useRouter()
const meeting = ref<Meeting>()
const feature = ref<MeetingAssistantFeature>()
const loading = ref(true)
const errorMessage = ref('')
const meetingDate = computed(formatMeetingDate)
const agendaItems = computed(buildAgendaItems)
const contentBlocks = computed(buildContentBlocks)
const weatherLocation = computed(resolveWeatherLocation)
const currentWeather = computed(buildCurrentWeather)
const weatherForecast = computed(buildWeatherForecast)

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
 * 从会议地点中提取用于天气展示的区、县或城市级地点。
 *
 * 入参：无；函数读取已加载会议的地点文本。
 * 返回值：WeatherLocationDisplay：包含展示地点和天气数据适用说明。
 * 异常：地点为空或无法识别行政区划时使用“会议地点”作为兜底展示，不向页面抛出异常。
 */
function resolveWeatherLocation(): WeatherLocationDisplay {
  const location = meeting.value?.location.trim() ?? ''
  const districtMatches = location.match(/[\u4e00-\u9fa5]{2,}(?:区|县)/g)
  if (districtMatches?.length) {
    const district = districtMatches[districtMatches.length - 1]
    return {
      name: district,
      message: '会议日期天气暂未预报，以下为该区/县近期天气。',
    }
  }

  const cityMatches = location.match(/[\u4e00-\u9fa5]{2,}市/g)
  if (cityMatches?.length) {
    const city = cityMatches[0]
    return {
      name: city,
      message: '会议地点未填写区/县，以下按可识别城市展示近期天气。',
    }
  }

  return {
    name: location || '会议地点',
    message: '会议地点未填写区/县，以下为前端测试天气数据。',
  }
}

/**
 * 构建当前天气卡片的前端测试数据。
 *
 * 入参：无。
 * 返回值：包含天气图标、温度、天气现象、湿度和风速的对象。
 * 异常：当前函数不主动抛出异常；实时天气接口接入后将由接口数据替换。
 */
function buildCurrentWeather(): { icon: string; temperature: number; condition: string; humidity: number; windSpeed: number } {
  return { icon: '☀️', temperature: 27, condition: '晴', humidity: 81, windSpeed: 14 }
}

/**
 * 构建连续七天的前端测试天气预报。
 *
 * 入参：无；函数优先使用会议开始日期作为预报起始日。
 * 返回值：WeatherForecastItem[]：七条包含日期、天气、降水概率和最高最低温的预报数据。
 * 异常：会议开始日期非法时使用当前日期作为起始日，不向页面抛出异常。
 */
function buildWeatherForecast(): WeatherForecastItem[] {
  const startDate = meeting.value?.startTime ? new Date(meeting.value.startTime) : new Date()
  const baseDate = Number.isNaN(startDate.getTime()) ? new Date() : startDate
  const weatherPatterns = [
    { icon: '⛅', condition: '多云', rainProbability: 12, high: 29, low: 23 },
    { icon: '☁️', condition: '阴', rainProbability: 6, high: 29, low: 24 },
    { icon: '☁️', condition: '阴', rainProbability: 9, high: 29, low: 23 },
    { icon: '🌦️', condition: '毛毛雨', rainProbability: 19, high: 29, low: 22 },
    { icon: '☁️', condition: '阴', rainProbability: 41, high: 29, low: 21 },
    { icon: '☀️', condition: '晴', rainProbability: 8, high: 30, low: 23 },
    { icon: '🌦️', condition: '毛毛雨', rainProbability: 17, high: 30, low: 24 },
  ]
  const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weatherPatterns.map((pattern, index) => {
    const date = new Date(baseDate)
    date.setDate(baseDate.getDate() + index)
    return {
      ...pattern,
      date: `${date.getMonth() + 1}月${date.getDate()}日 ${weekdayNames[date.getDay()]}`,
    }
  })
}

onMounted(loadFeature)
</script>
