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
        <template v-if="!weather?.available || !weather.current">
          <section class="weather-empty" aria-live="polite">
            <el-icon class="weather-empty__icon"><Sunny /></el-icon>
            <p class="weather-empty__title">天气数据暂时不可用</p>
            <p class="weather-empty__desc">{{ weather?.message || '请稍后再试。' }}</p>
            <el-button class="weather-empty__action" type="primary" plain @click="loadFeature">重新加载</el-button>
          </section>
        </template>

        <template v-else>
          <section class="weather-card">
            <header class="weather-card__head">
              <p class="weather-card__location">
                <el-icon><LocationIcon /></el-icon>
                <span>{{ weather.locationName }}</span>
              </p>
            </header>

            <button
              type="button"
              class="weather-card__now"
              :class="{ 'is-expanded': hourlyExpanded }"
              :aria-expanded="hourlyExpanded"
              aria-controls="weather-hourly-section"
              @click="hourlyExpanded = !hourlyExpanded"
            >
              <span class="weather-card__now-icon" aria-hidden="true">{{ weatherIcon(weather.current.iconCode) }}</span>
              <div class="weather-card__now-temp">
                <strong>{{ weather.current.temperature }}<small>°</small></strong>
                <span>{{ weather.current.condition }}</span>
              </div>
              <dl class="weather-card__now-meta">
                <div>
                  <dt>湿度</dt>
                  <dd>{{ weather.current.humidity }}%</dd>
                </div>
                <div>
                  <dt>风速</dt>
                  <dd>{{ weather.current.windSpeed }} km/h</dd>
                </div>
              </dl>
              <span class="weather-card__now-toggle" aria-hidden="true">
                <el-icon><ArrowDown v-if="!hourlyExpanded" /><ArrowUp v-else /></el-icon>
              </span>
            </button>

            <section
              v-if="hourlyExpanded && weather.hourly.length"
              id="weather-hourly-section"
              class="weather-card__hourly"
              aria-label="未来几小时预报"
            >
              <ul>
                <li v-for="item in weather.hourly" :key="item.forecastAt">
                  <span class="weather-hourly-item__time">{{ formatHourlyTime(item.forecastAt) }}</span>
                  <span class="weather-hourly-item__icon" aria-hidden="true">{{ weatherIcon(item.iconCode) }}</span>
                  <span class="weather-hourly-item__condition">{{ item.condition }}</span>
                  <span class="weather-hourly-item__temp"><strong>{{ item.temperature }}°</strong></span>
                  <span v-if="item.precipitationProbability > 0" class="weather-hourly-item__pop">
                    <el-icon><Umbrella /></el-icon>{{ item.precipitationProbability }}%
                  </span>
                </li>
              </ul>
            </section>

            <section v-if="weather.tips.length" class="weather-tips" aria-label="温馨提示">
              <h3>温馨提示</h3>
              <ul>
                <li v-for="(tip, index) in weather.tips" :key="index">{{ tip }}</li>
              </ul>
            </section>

            <section class="weather-card__forecast" aria-label="近期预报">
              <h2>近期预报</h2>
              <ul>
                <li
                  v-for="item in upcomingForecast"
                  :key="item.date"
                  :class="{ 'is-today': item.date === todayKey }"
                >
                  <span class="weather-forecast-item__date">
                    <strong>{{ formatForecastShort(item.date) }}</strong>
                    <small>{{ isToday(item.date) ? '今天' : formatWeekday(item.date) }}</small>
                  </span>
                  <span class="weather-forecast-item__icon" aria-hidden="true">{{ weatherIcon(item.iconCode) }}</span>
                  <span class="weather-forecast-item__condition">{{ item.condition }}</span>
                  <span v-if="item.precipitation > 0" class="weather-forecast-item__rain">
                    <el-icon><Umbrella /></el-icon>{{ item.precipitation }}mm
                  </span>
                  <span class="weather-forecast-item__temperature">
                    <strong>{{ item.high }}°</strong>
                    <em>{{ item.low }}°</em>
                  </span>
                </li>
              </ul>
            </section>
          </section>

          <a class="weather-source" :href="weather.sourceUrl" target="_blank" rel="noopener noreferrer">
            数据由 {{ weather.sourceName }} 提供
          </a>
        </template>
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

      <template v-else-if="feature?.key === 'contact'">
        <div v-if="!contactPersons.length" class="assistant-content-cards">
          <article class="assistant-content-card">联系人信息待补充</article>
        </div>
        <ul v-else class="contact-person-list">
          <li v-for="(person, index) in contactPersons" :key="`${person.name}-${index}`" class="contact-person-card">
            <span class="contact-person-card__avatar" aria-hidden="true">{{ person.name.slice(0, 1) }}</span>
            <div class="contact-person-card__info">
              <strong>{{ person.name }}</strong>
              <small v-if="person.role">{{ person.role }}</small>
            </div>
            <a
              v-if="person.phone"
              class="contact-person-card__call"
              :href="`tel:${person.phone}`"
              :aria-label="`拨打 ${person.name}`"
            >
              <el-icon><Phone /></el-icon>
            </a>
            <span v-else class="contact-person-card__call is-disabled" aria-hidden="true">
              <el-icon><Phone /></el-icon>
            </span>
          </li>
        </ul>
      </template>

      <div v-else-if="feature" class="assistant-content-cards">
        <article v-for="(block, index) in contentBlocks" :key="`${feature.key}-${index}`" class="assistant-content-card">{{ block }}</article>
      </div>
    </main>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowDown, ArrowLeft, ArrowUp, Location as LocationIcon, Phone, Sunny, Umbrella, User } from '@element-plus/icons-vue'
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
const hourlyExpanded = ref(false)
const errorMessage = ref('')
const agendaItems = computed(buildAgendaItems)
const contentBlocks = computed(buildContentBlocks)
const navigationUrl = computed(buildNavigationUrl)
const upcomingForecast = computed(buildUpcomingForecast)
const contactPersons = computed(buildContactPersons)

/**
 * 返回 7 日预报中从明天开始的列表，跳过与实时卡片重复的"今天"项。
 *
 * 入参：无；函数读取 weather.daily。
 * 返回值：MeetingDailyWeather[]：去掉了今天条目的预报列表；若 daily 为空则返回空数组。
 * 异常：当前函数不主动抛出异常。
 */
function buildUpcomingForecast(): NonNullable<typeof weather.value>['daily'] {
  return weather.value?.daily.slice(1) ?? []
}

/**
 * 将联系会务配置转换为嘉宾端可拨号的联系人列表。
 *
 * 入参：无；函数读取当前 feature 的 contacts 字段。
 * 返回值：Array<{name, role, phone}>：已清理空白后的联系人列表；缺失时返回空数组。
 * 异常：当前函数不主动抛出异常。
 */
function buildContactPersons(): Array<{ name: string; role: string; phone: string }> {
  return feature.value?.contacts ?? []
}

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

/**
 * 返回当前本地日期对应的和风日期键（yyyy-MM-dd），用于当日预报标记。
 *
 * 入参：无。
 * 返回值：string：当前日期字符串，与和风天气返回的 daily.date 字段格式一致。
 * 异常：当前函数不主动抛出异常。
 */
const todayKey = computed(computeTodayKey)

function computeTodayKey(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

/**
 * 判断给定的和风日期键是否为今天。
 *
 * 入参：value 为日期键，必填。
 * 返回值：boolean：与今日日期一致返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function isToday(value: string): boolean {
  return value === todayKey.value
}

/**
 * 将日期键简化为"7/16"格式。
 *
 * 入参：value 为 yyyy-MM-dd 格式的日期键，必填。
 * 返回值：string：形如"7/16"的短日期；日期无效时返回原文本。
 * 异常：当前函数不主动抛出异常。
 */
function formatForecastShort(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getMonth() + 1}/${date.getDate()}`
}

/**
 * 从日期键返回中文星期文本。
 *
 * 入参：value 为 yyyy-MM-dd 格式的日期键，必填。
 * 返回值：string：周一至周日；日期无效时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatWeekday(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return ''
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()]
}

/**
 * 把和风天气 obsTime 字段（ISO 字符串）转换为当日"HH:mm"。
 *
 * 入参：value 为 ISO 时间字符串（如 2026-07-16T12:00+08:00），必填。
 * 返回值：string：形如"12:30"的简短时间；解析失败时返回原始字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatObservedAt(value: string): string {
  const normalized = value.includes('T') && !value.includes('+') && !value.includes('Z') ? `${value}+08:00` : value
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return value
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

/**
 * 把和风天气 fxTime 字段（ISO 字符串）转换为"周X HH:mm"，便于展示未来几小时。
 *
 * 入参：value 为 ISO 时间字符串，必填。
 * 返回值：string：形如"今天 14:00"或"周二 14:00"；解析失败时返回原始字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatHourlyTime(value: string): string {
  const normalized = value.includes('T') && !value.includes('+') && !value.includes('Z') ? `${value}+08:00` : value
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return value
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const time = `${hours}:${minutes}`
  const now = new Date()
  if (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  ) {
    return `今天 ${time}`
  }
  const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${weekdayNames[date.getDay()]} ${time}`
}

onMounted(loadFeature)
</script>
